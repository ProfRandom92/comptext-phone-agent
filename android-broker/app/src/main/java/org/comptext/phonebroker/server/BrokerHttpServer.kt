package org.comptext.phonebroker.server

import com.google.gson.Gson
import com.google.gson.JsonArray
import com.google.gson.JsonObject
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.server.application.Application
import io.ktor.server.application.ApplicationCall
import io.ktor.server.cio.CIO
import io.ktor.server.engine.embeddedServer
import io.ktor.server.request.contentType
import io.ktor.server.request.receiveChannel
import io.ktor.server.response.respondText
import io.ktor.server.routing.get
import io.ktor.server.routing.post
import io.ktor.server.routing.routing
import io.ktor.utils.io.readAvailable
import java.nio.charset.StandardCharsets
import java.util.concurrent.atomic.AtomicBoolean
import org.comptext.phonebroker.BuildConfig
import org.comptext.phonebroker.inference.InferenceBackend
import org.comptext.phonebroker.inference.InferenceBusyException
import org.comptext.phonebroker.inference.LiteRtEngineController
import org.comptext.phonebroker.inference.ModelNotLoadedException
import org.comptext.phonebroker.model.ModelRegistry
import org.comptext.phonebroker.protocol.BrokerLimits
import org.comptext.phonebroker.protocol.BrokerProtocol
import org.comptext.phonebroker.protocol.ProtocolException
import org.comptext.phonebroker.security.BearerAuthenticator

data class BrokerDependencies(
    val authenticator: BearerAuthenticator,
    val models: ModelRegistry,
    val engine: LiteRtEngineController,
    val backend: () -> InferenceBackend,
    val rateLimiter: RateLimiter = RateLimiter(),
)

class BrokerHttpServer(
    private val dependencies: BrokerDependencies,
    private val port: Int = ServerPolicy.DEFAULT_PORT,
) : AutoCloseable {
    private val started = AtomicBoolean(false)
    private var stopServer: (() -> Unit)? = null

    @Synchronized fun start() {
        check(started.compareAndSet(false, true)) { "broker is already running" }
        try {
            val created = embeddedServer(CIO, host = ServerPolicy.HOST, port = ServerPolicy.validatePort(port)) {
                brokerModule(dependencies)
            }
            created.start(wait = false)
            stopServer = { created.stop(1_000, 3_000) }
        } catch (error: Throwable) {
            started.set(false)
            throw error
        }
    }

    @Synchronized override fun close() {
        stopServer?.invoke()
        stopServer = null
        started.set(false)
    }
}

private fun Application.brokerModule(dependencies: BrokerDependencies) {
    routing {
        get("/health") {
            guarded(call, dependencies) {
                respondJson(call, HttpStatusCode.OK, JsonObject().apply {
                    addProperty("status", "ok")
                    addProperty("version", BuildConfig.VERSION_NAME)
                    addProperty("loopback", ServerPolicy.HOST)
                })
            }
        }
        get("/v1/models") {
            guarded(call, dependencies) {
                val models = JsonArray().apply {
                    dependencies.models.list().forEach { record -> add(JsonObject().apply {
                        addProperty("id", record.name)
                        addProperty("size", record.size)
                        addProperty("sha256", record.sha256)
                    }) }
                }
                respondJson(call, HttpStatusCode.OK, JsonObject().apply { add("data", models) })
            }
        }
        get("/v1/status") {
            guarded(call, dependencies) {
                val status = dependencies.engine.status()
                respondJson(call, HttpStatusCode.OK, JsonObject().apply {
                    addProperty("running", true)
                    addProperty("model_loaded", status.loaded)
                    if (status.model != null) addProperty("model", status.model)
                    if (status.backend != null) addProperty("backend", status.backend.name.lowercase())
                    addProperty("active_inference_limit", 1)
                    addProperty("request_limit_bytes", BrokerLimits.MAX_REQUEST_BYTES)
                })
            }
        }
        post("/v1/route") {
            guarded(call, dependencies) {
                val request = BrokerProtocol.parseRouteRequest(readJson(call))
                val prompt = ROUTER_POLICY + "\nUser request:\n" + request.input
                val raw = dependencies.engine.infer(request.model, prompt)
                val decision = BrokerProtocol.parseDecision(raw)
                respondJson(call, HttpStatusCode.OK, JsonObject().apply { add("decision", BrokerProtocol.decisionJson(decision)) })
            }
        }
        post("/v1/chat/completions") {
            guarded(call, dependencies) {
                val request = BrokerProtocol.parseChatRequest(readJson(call))
                val prompt = request.messages.joinToString("\n") { "${it.role}: ${it.content}" }
                val response = dependencies.engine.infer(request.model, prompt)
                respondJson(call, HttpStatusCode.OK, JsonObject().apply {
                    addProperty("model", request.model)
                    add("choices", JsonArray().apply { add(JsonObject().apply {
                        addProperty("index", 0)
                        addProperty("finish_reason", "stop")
                        add("message", JsonObject().apply {
                            addProperty("role", "assistant")
                            addProperty("content", response)
                        })
                    }) })
                })
            }
        }
        post("/v1/models/import") {
            guarded(call, dependencies) {
                BrokerProtocol.parseImportRequest(readJson(call))
                throw BrokerFailure(HttpStatusCode.Conflict, "interactive_required", "model import requires visible Storage Access Framework interaction")
            }
        }
        post("/v1/models/load") {
            guarded(call, dependencies) {
                val request = BrokerProtocol.parseModelRequest(readJson(call))
                val record = dependencies.models.find(request.model)
                    ?: throw BrokerFailure(HttpStatusCode.NotFound, "model_not_found", "model is not imported")
                dependencies.engine.load(record, dependencies.backend())
                respondJson(call, HttpStatusCode.OK, JsonObject().apply {
                    addProperty("status", "loaded")
                    addProperty("model", record.name)
                })
            }
        }
        post("/v1/models/unload") {
            guarded(call, dependencies) {
                val request = BrokerProtocol.parseModelRequest(readJson(call))
                val status = dependencies.engine.status()
                if (status.model != request.model) throw BrokerFailure(HttpStatusCode.Conflict, "model_not_loaded", "requested model is not loaded")
                dependencies.engine.unload()
                respondJson(call, HttpStatusCode.OK, JsonObject().apply { addProperty("status", "unloaded") })
            }
        }
    }
}

private suspend fun guarded(call: ApplicationCall, dependencies: BrokerDependencies, action: suspend () -> Unit) {
    try {
        if (!dependencies.authenticator.isAuthorized(call.request.headers[HttpHeaders.Authorization])) {
            throw BrokerFailure(HttpStatusCode.Unauthorized, "authentication_failed", "valid bearer authentication is required")
        }
        if (!dependencies.rateLimiter.tryAcquire()) {
            throw BrokerFailure(HttpStatusCode.TooManyRequests, "rate_limited", "request rate limit exceeded")
        }
        action()
    } catch (error: BrokerFailure) {
        respondError(call, error.status, error.code, error.message ?: error.code)
    } catch (error: ProtocolException) {
        val status = if (error.code == "request_too_large") HttpStatusCode.PayloadTooLarge else HttpStatusCode.BadRequest
        respondError(call, status, error.code, error.message ?: error.code)
    } catch (_: RequestTooLargeException) {
        respondError(call, HttpStatusCode.PayloadTooLarge, "request_too_large", "request body is too large")
    } catch (_: InferenceBusyException) {
        respondError(call, HttpStatusCode.ServiceUnavailable, "inference_busy", "inference queue is full")
    } catch (_: ModelNotLoadedException) {
        respondError(call, HttpStatusCode.ServiceUnavailable, "model_unavailable", "requested model is unavailable")
    } catch (_: kotlinx.coroutines.TimeoutCancellationException) {
        respondError(call, HttpStatusCode.GatewayTimeout, "inference_timeout", "inference timed out")
    } catch (error: kotlinx.coroutines.CancellationException) {
        throw error
    } catch (_: Exception) {
        respondError(call, HttpStatusCode.InternalServerError, "internal_error", "broker operation failed")
    }
}

private suspend fun readJson(call: ApplicationCall): String {
    val encoding = call.request.headers[HttpHeaders.ContentEncoding]
    if (encoding != null && !encoding.equals("identity", ignoreCase = true)) {
        throw BrokerFailure(HttpStatusCode.UnsupportedMediaType, "content_encoding_forbidden", "encoded request bodies are forbidden")
    }
    if (call.request.contentType().withoutParameters() != ContentType.Application.Json) {
        throw BrokerFailure(HttpStatusCode.UnsupportedMediaType, "content_type_required", "application/json is required")
    }
    val declared = call.request.headers[HttpHeaders.ContentLength]?.toLongOrNull()
    if (declared != null && declared > BrokerLimits.MAX_REQUEST_BYTES) throw RequestTooLargeException()
    val channel = call.receiveChannel()
    val accumulator = BoundedBodyAccumulator(BrokerLimits.MAX_REQUEST_BYTES)
    val buffer = ByteArray(8192)
    while (!channel.isClosedForRead) {
        val remaining = BrokerLimits.MAX_REQUEST_BYTES - accumulator.size
        val read = channel.readAvailable(buffer, 0, minOf(buffer.size, remaining + 1))
        if (read < 0) break
        if (read > 0) accumulator.append(buffer, 0, read)
    }
    return String(accumulator.toByteArray(), StandardCharsets.UTF_8)
}

private suspend fun respondError(call: ApplicationCall, status: HttpStatusCode, code: String, message: String) {
    respondJson(call, status, JsonObject().apply {
        add("error", JsonObject().apply {
            addProperty("code", code)
            addProperty("message", message)
        })
    })
}

private suspend fun respondJson(call: ApplicationCall, status: HttpStatusCode, body: JsonObject) {
    call.respondText(Gson().toJson(body), ContentType.Application.Json, status)
}

private class BrokerFailure(val status: HttpStatusCode, val code: String, message: String) : IllegalArgumentException(message)

private const val ROUTER_POLICY = """Classify only. Never execute actions. Return exactly one JSON object with fields kind, action, arguments, confidence, reason, source. Allowed kinds: direct_action, delegate, clarify, reject. Use canonical lowercase ASCII action names and no extra fields."""
