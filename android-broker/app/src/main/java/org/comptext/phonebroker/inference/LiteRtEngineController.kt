package org.comptext.phonebroker.inference

import android.content.Context
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Content
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

enum class InferenceBackend { CPU, GPU }
data class EngineStatus(val model: String?, val backend: InferenceBackend?, val loaded: Boolean)

class LiteRtEngineController(context: Context) {
    private val cacheDir = File(context.cacheDir, "litertlm").apply { mkdirs() }.absolutePath
    private val lifecycle = Mutex()
    private val coordinator = InferenceCoordinator(timeoutMillis = 60_000, maxQueued = 1)
    @Volatile private var engine: Engine? = null
    @Volatile private var modelName: String? = null
    @Volatile private var selectedBackend: InferenceBackend? = null

    fun status(): EngineStatus = EngineStatus(modelName, selectedBackend, engine?.isInitialized() == true)

    suspend fun load(record: org.comptext.phonebroker.model.ModelRecord, backend: InferenceBackend) {
        lifecycle.withLock {
            withContext(Dispatchers.IO) {
                engine?.close()
                engine = null
                modelName = null
                selectedBackend = null
                val configuredBackend = when (backend) {
                    InferenceBackend.CPU -> Backend.CPU()
                    InferenceBackend.GPU -> Backend.GPU()
                }
                val replacement = Engine(EngineConfig(
                    modelPath = record.path,
                    backend = configuredBackend,
                    maxNumTokens = org.comptext.phonebroker.protocol.BrokerLimits.MAX_OUTPUT_TOKENS,
                    cacheDir = cacheDir,
                ))
                try {
                    replacement.initialize()
                    engine = replacement
                    modelName = record.name
                    selectedBackend = backend
                } catch (error: Throwable) {
                    replacement.close()
                    throw error
                }
            }
        }
    }

    suspend fun unload() {
        lifecycle.withLock {
            withContext(Dispatchers.IO) { engine?.close() }
            engine = null
            modelName = null
            selectedBackend = null
        }
    }

    suspend fun infer(requiredModel: String, prompt: String): String = coordinator.run {
        lifecycle.withLock {
            val active = engine ?: throw ModelNotLoadedException("no model is loaded")
            if (modelName != requiredModel) throw ModelNotLoadedException("requested model is not loaded")
            withContext(Dispatchers.IO) {
                active.createConversation().use { conversation ->
                    conversation.sendMessage(prompt).contents.contents
                        .filterIsInstance<Content.Text>()
                        .joinToString(separator = "") { it.text }
                }
            }
        }
    }
}

class ModelNotLoadedException(message: String) : IllegalStateException(message)
