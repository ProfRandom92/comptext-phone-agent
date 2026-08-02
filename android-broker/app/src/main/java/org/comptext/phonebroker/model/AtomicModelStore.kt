package org.comptext.phonebroker.model

import java.io.File
import java.io.FileOutputStream
import java.io.InputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import java.security.MessageDigest
import java.util.UUID

data class ImportedModel(val name: String, val file: File, val size: Long, val sha256: String)

class AtomicModelStore(
    private val root: File,
    private val minBytes: Long = ModelPolicy.MIN_MODEL_BYTES,
    private val maxBytes: Long = ModelPolicy.MAX_MODEL_BYTES,
) {
    init {
        require(minBytes >= 1 && maxBytes >= minBytes)
    }

    fun import(displayName: String, source: InputStream): ImportedModel {
        val name = ModelPolicy.normalizeName(displayName)
        root.mkdirs()
        val partial = File(root, ".$name.partial-${UUID.randomUUID()}")
        val target = File(root, name)
        val digest = MessageDigest.getInstance("SHA-256")
        var total = 0L
        try {
            source.use { input ->
                FileOutputStream(partial).use { output ->
                    val buffer = ByteArray(64 * 1024)
                    while (true) {
                        val read = input.read(buffer)
                        if (read < 0) break
                        if (read == 0) continue
                        val remaining = maxBytes - total
                        if (read > remaining) {
                            if (remaining > 0) {
                                output.write(buffer, 0, remaining.toInt())
                                digest.update(buffer, 0, remaining.toInt())
                                total += remaining
                            }
                            throw ModelValidationException("model exceeds maximum size")
                        }
                        output.write(buffer, 0, read)
                        digest.update(buffer, 0, read)
                        total += read
                    }
                    output.fd.sync()
                }
            }
            if (total !in minBytes..maxBytes) throw ModelValidationException("model size is implausible")
            Files.move(partial.toPath(), target.toPath(), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING)
            return ImportedModel(name, target, total, digest.digest().joinToString("") { "%02x".format(it) })
        } finally {
            partial.delete()
        }
    }
}
