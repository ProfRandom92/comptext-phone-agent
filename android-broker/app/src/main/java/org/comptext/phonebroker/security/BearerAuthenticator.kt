package org.comptext.phonebroker.security

import java.nio.charset.StandardCharsets
import java.security.MessageDigest

class BearerAuthenticator(private val tokenProvider: () -> String) {
    fun isAuthorized(header: String?): Boolean {
        if (header == null || !header.startsWith("Bearer ") || header.length <= 7) return false
        val candidate = header.substring(7)
        if (candidate.startsWith(' ') || candidate.endsWith(' ')) return false
        val expectedBytes = tokenProvider().toByteArray(StandardCharsets.UTF_8)
        val candidateBytes = candidate.toByteArray(StandardCharsets.UTF_8)
        return MessageDigest.isEqual(expectedBytes, candidateBytes)
    }
}
