package org.comptext.phonebroker.model

import java.io.ByteArrayInputStream
import java.io.IOException
import java.io.InputStream
import java.nio.file.Files
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertThrows
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder

class AtomicModelStoreTest {
    @get:Rule val temporary = TemporaryFolder()

    @Test fun `imports atomically with a sha256 record`() {
        val root = temporary.newFolder("models")
        val store = AtomicModelStore(root, minBytes = 1, maxBytes = 1024)
        val record = store.import("Router.litertlm", ByteArrayInputStream("model".toByteArray()))
        assertEquals("router.litertlm", record.name)
        assertEquals(5, record.size)
        assertEquals(64, record.sha256.length)
        assertEquals("model", record.file.readText())
        assertFalse(root.listFiles()!!.any { it.name.contains("partial") })
    }

    @Test fun `removes partial import after stream failure`() {
        val root = temporary.newFolder("failed")
        val store = AtomicModelStore(root, minBytes = 1, maxBytes = 1024)
        val failing = object : InputStream() {
            override fun read(): Int = throw IOException("read failed")
        }
        assertThrows(IOException::class.java) { store.import("broken.litertlm", failing) }
        assertEquals(emptyList<String>(), Files.list(root.toPath()).use { paths -> paths.map { it.fileName.toString() }.toList() })
    }

    @Test fun `does not write bytes beyond configured maximum`() {
        val root = temporary.newFolder("bounded")
        val store = AtomicModelStore(root, minBytes = 1, maxBytes = 4)
        assertThrows(ModelValidationException::class.java) {
            store.import("large.litertlm", ByteArrayInputStream(byteArrayOf(1, 2, 3, 4, 5)))
        }
        assertEquals(emptyArray<String>().toList(), root.list()!!.toList())
    }
}
