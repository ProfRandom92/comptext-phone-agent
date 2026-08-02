package org.comptext.phonebroker.model

import java.text.Normalizer
import java.util.Locale

class ModelValidationException(message: String) : IllegalArgumentException(message)

object ModelPolicy {
    const val MIN_MODEL_BYTES = 1024L * 1024L
    const val MAX_MODEL_BYTES = 8L * 1024L * 1024L * 1024L
    private val safeName = Regex("[a-z0-9][a-z0-9._-]{0,95}\\.litertlm")

    fun normalizeName(displayName: String): String {
        if (displayName.contains('/') || displayName.contains('\\') || displayName.contains("..")) {
            throw ModelValidationException("model name contains a forbidden path component")
        }
        val normalized = Normalizer.normalize(displayName.trim(), Normalizer.Form.NFKC)
            .lowercase(Locale.ROOT)
            .replace(Regex("[^a-z0-9._-]+"), "-")
            .trim('-', '.')
        if (!safeName.matches(normalized)) throw ModelValidationException("model must have a safe .litertlm name")
        return normalized
    }

    fun validateSize(size: Long): Long {
        if (size !in MIN_MODEL_BYTES..MAX_MODEL_BYTES) throw ModelValidationException("model size is implausible")
        return size
    }
}
