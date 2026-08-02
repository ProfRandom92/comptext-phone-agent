package org.comptext.phonebroker.protocol

import com.google.gson.JsonArray
import com.google.gson.JsonElement
import com.google.gson.JsonNull
import com.google.gson.JsonObject
import com.google.gson.JsonParser
import com.google.gson.stream.JsonReader
import com.google.gson.stream.JsonToken
import java.io.StringReader
import java.nio.charset.StandardCharsets

object BrokerLimits {
    const val MAX_REQUEST_BYTES = 256 * 1024
    const val MAX_ROUTE_INPUT_CHARS = 16 * 1024
    const val MAX_CHAT_MESSAGES = 64
    const val MAX_MESSAGE_CHARS = 16 * 1024
    const val MAX_OUTPUT_TOKENS = 2048
    const val DEFAULT_OUTPUT_TOKENS = 512
}

class ProtocolException(val code: String, message: String) : IllegalArgumentException(message)

data class RouteRequest(val model: String, val input: String)
data class ChatMessage(val role: String, val content: String)
data class ChatRequest(val model: String, val messages: List<ChatMessage>, val maxTokens: Int)
data class ModelRequest(val model: String)
data class RouteDecision(
    val kind: String,
    val action: String?,
    val arguments: JsonObject,
    val confidence: Double,
    val reason: String,
    val source: String,
)

object BrokerProtocol {
    private val modelPattern = Regex("[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
    private val actionPattern = Regex("[a-z][a-z0-9_]*")
    private val sourcePattern = Regex("[a-z][a-z0-9_-]*")
    private val routeFields = setOf("model", "input")
    private val decisionFields = setOf("kind", "action", "arguments", "confidence", "reason", "source")

    fun parseRouteRequest(json: String): RouteRequest {
        val value = strictObject(json)
        requireFields(value, routeFields, setOf("model", "input"))
        val model = boundedString(value, "model", 128)
        if (!modelPattern.matches(model)) fail("invalid_schema", "model is not canonical")
        val input = boundedString(value, "input", BrokerLimits.MAX_ROUTE_INPUT_CHARS)
        if (input.toByteArray(StandardCharsets.UTF_8).size > BrokerLimits.MAX_ROUTE_INPUT_CHARS) {
            fail("invalid_schema", "input is too large")
        }
        return RouteRequest(model, input)
    }

    fun parseChatRequest(json: String): ChatRequest {
        val value = strictObject(json)
        requireFields(value, setOf("model", "messages", "max_tokens"), setOf("model", "messages"))
        val model = boundedString(value, "model", 128)
        if (!modelPattern.matches(model)) fail("invalid_schema", "model is not canonical")
        val array = value.get("messages") as? JsonArray ?: fail("invalid_schema", "messages must be an array")
        if (array.isEmpty || array.size() > BrokerLimits.MAX_CHAT_MESSAGES) fail("invalid_schema", "messages are not bounded")
        val messages = array.map { item ->
            val message = item as? JsonObject ?: fail("invalid_schema", "message must be an object")
            requireFields(message, setOf("role", "content"), setOf("role", "content"))
            val role = boundedString(message, "role", 16)
            if (role !in setOf("system", "user", "assistant")) fail("invalid_schema", "unsupported message role")
            ChatMessage(role, boundedString(message, "content", BrokerLimits.MAX_MESSAGE_CHARS))
        }
        val maxTokens = if (value.has("max_tokens")) integer(value, "max_tokens") else BrokerLimits.DEFAULT_OUTPUT_TOKENS
        if (maxTokens !in 1..BrokerLimits.MAX_OUTPUT_TOKENS) fail("invalid_schema", "max_tokens is out of range")
        return ChatRequest(model, messages, maxTokens)
    }

    fun parseModelRequest(json: String): ModelRequest {
        val value = strictObject(json)
        requireFields(value, setOf("model"), setOf("model"))
        val model = boundedString(value, "model", 128)
        if (!modelPattern.matches(model)) fail("invalid_schema", "model is not canonical")
        return ModelRequest(model)
    }

    fun parseImportRequest(json: String) {
        val value = strictObject(json)
        requireFields(value, emptySet(), emptySet())
    }

    fun parseDecision(json: String): RouteDecision {
        val value = strictObject(json)
        requireFields(value, decisionFields, setOf("kind"))
        val kind = boundedString(value, "kind", 32).let { if (it == "planner") "delegate" else it }
        if (kind !in setOf("direct_action", "delegate", "clarify", "reject")) fail("invalid_model_output", "unknown route kind")
        val action = value.get("action")?.takeUnless { it is JsonNull }?.let {
            if (!it.isJsonPrimitive || !it.asJsonPrimitive.isString) fail("invalid_model_output", "action must be text")
            it.asString
        }
        if (kind == "direct_action") {
            if (action == null || !actionPattern.matches(action)) fail("invalid_model_output", "action is not canonical")
        } else if (action != null) fail("invalid_model_output", "non-action route includes action")
        val arguments = value.get("arguments")?.let { it as? JsonObject ?: fail("invalid_model_output", "arguments must be an object") } ?: JsonObject()
        val confidence = value.get("confidence")?.let {
            if (!it.isJsonPrimitive || !it.asJsonPrimitive.isNumber) fail("invalid_model_output", "confidence must be numeric")
            runCatching { it.asDouble }.getOrElse { fail("invalid_model_output", "confidence is invalid") }
        } ?: 0.0
        if (!confidence.isFinite() || confidence !in 0.0..1.0) fail("invalid_model_output", "confidence is out of range")
        val reason = optionalString(value, "reason", 1024, "")
        val source = optionalString(value, "source", 64, "litertlm")
        if (!sourcePattern.matches(source)) fail("invalid_model_output", "source is not canonical")
        return RouteDecision(kind, action, arguments, confidence, reason, source)
    }

    fun decisionJson(decision: RouteDecision): JsonObject = JsonObject().apply {
        addProperty("kind", decision.kind)
        if (decision.action != null) addProperty("action", decision.action)
        add("arguments", decision.arguments)
        addProperty("confidence", decision.confidence)
        addProperty("reason", decision.reason)
        addProperty("source", decision.source)
    }

    private fun strictObject(json: String): JsonObject {
        if (json.toByteArray(StandardCharsets.UTF_8).size > BrokerLimits.MAX_REQUEST_BYTES) fail("request_too_large", "request is too large")
        val reader = JsonReader(StringReader(json))
        val element = readStrict(reader)
        if (reader.peek() != JsonToken.END_DOCUMENT) fail("invalid_json", "trailing JSON is forbidden")
        return element as? JsonObject ?: fail("invalid_schema", "request must be an object")
    }

    private fun readStrict(reader: JsonReader): JsonElement = when (reader.peek()) {
        JsonToken.BEGIN_OBJECT -> JsonObject().also { result ->
            reader.beginObject()
            val seen = mutableSetOf<String>()
            while (reader.hasNext()) {
                val name = reader.nextName()
                if (!seen.add(name)) fail("invalid_json", "duplicate JSON field")
                result.add(name, readStrict(reader))
            }
            reader.endObject()
        }
        JsonToken.BEGIN_ARRAY -> JsonArray().also { result ->
            reader.beginArray()
            while (reader.hasNext()) result.add(readStrict(reader))
            reader.endArray()
        }
        JsonToken.STRING -> JsonParser.parseString("\"${escape(reader.nextString())}\"")
        JsonToken.NUMBER -> JsonParser.parseString(reader.nextString())
        JsonToken.BOOLEAN -> com.google.gson.JsonPrimitive(reader.nextBoolean())
        JsonToken.NULL -> { reader.nextNull(); JsonNull.INSTANCE }
        else -> fail("invalid_json", "invalid JSON token")
    }

    private fun escape(value: String): String = buildString {
        value.forEach { character ->
            when (character) {
                '\\' -> append("\\\\")
                '"' -> append("\\\"")
                '\b' -> append("\\b")
                '\u000C' -> append("\\f")
                '\n' -> append("\\n")
                '\r' -> append("\\r")
                '\t' -> append("\\t")
                else -> if (character < ' ') append("\\u%04x".format(character.code)) else append(character)
            }
        }
    }

    private fun requireFields(value: JsonObject, allowed: Set<String>, required: Set<String>) {
        if (!value.keySet().containsAll(required)) fail("invalid_schema", "required field is missing")
        if (!allowed.containsAll(value.keySet())) fail("invalid_schema", "unknown field is forbidden")
    }

    private fun boundedString(value: JsonObject, field: String, max: Int): String {
        val item = value.get(field) ?: fail("invalid_schema", "$field is required")
        if (!item.isJsonPrimitive || !item.asJsonPrimitive.isString) fail("invalid_schema", "$field must be text")
        return item.asString.also { if (it.isEmpty() || it.length > max) fail("invalid_schema", "$field is not bounded") }
    }

    private fun optionalString(value: JsonObject, field: String, max: Int, fallback: String): String {
        if (!value.has(field)) return fallback
        val item = value.get(field)
        if (!item.isJsonPrimitive || !item.asJsonPrimitive.isString) fail("invalid_model_output", "$field must be text")
        return item.asString.also { if (it.length > max) fail("invalid_model_output", "$field is too large") }
    }

    private fun integer(value: JsonObject, field: String): Int {
        val item = value.get(field)
        if (!item.isJsonPrimitive || !item.asJsonPrimitive.isNumber) fail("invalid_schema", "$field must be an integer")
        val rendered = item.asString
        if (!Regex("-?[0-9]+").matches(rendered)) fail("invalid_schema", "$field must be an integer")
        return rendered.toIntOrNull() ?: fail("invalid_schema", "$field is out of range")
    }

    private fun fail(code: String, message: String): Nothing = throw ProtocolException(code, message)
}
