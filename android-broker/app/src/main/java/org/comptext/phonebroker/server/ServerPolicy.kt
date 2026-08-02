package org.comptext.phonebroker.server

import java.io.ByteArrayOutputStream

object ServerPolicy {
    const val HOST = "127.0.0.1"
    const val DEFAULT_PORT = 8080
    fun validatePort(port: Int): Int = port.also { require(it in 1024..65535) { "port must be unprivileged and valid" } }
}

class RequestTooLargeException : IllegalArgumentException("request body is too large")

class BoundedBodyAccumulator(private val limit: Int) {
    private val output = ByteArrayOutputStream(minOf(limit, 8192))
    val size: Int get() = output.size()

    fun append(chunk: ByteArray, offset: Int = 0, length: Int = chunk.size) {
        require(offset >= 0 && length >= 0 && offset + length <= chunk.size)
        val remaining = limit - output.size()
        if (length > remaining) {
            if (remaining > 0) output.write(chunk, offset, remaining)
            throw RequestTooLargeException()
        }
        output.write(chunk, offset, length)
    }

    fun toByteArray(): ByteArray = output.toByteArray()
}
