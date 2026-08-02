package org.comptext.phonebroker.server

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ServerPolicyTest {
    @Test fun `server is fixed to IPv4 loopback`() {
        assertEquals("127.0.0.1", ServerPolicy.HOST)
        assertEquals(8080, ServerPolicy.validatePort(8080))
    }

    @Test fun `invalid ports are rejected`() {
        assertThrows(IllegalArgumentException::class.java) { ServerPolicy.validatePort(0) }
        assertThrows(IllegalArgumentException::class.java) { ServerPolicy.validatePort(65536) }
    }

    @Test fun `body accumulator never retains beyond limit`() {
        val accumulator = BoundedBodyAccumulator(4)
        accumulator.append(byteArrayOf(1, 2, 3))
        assertThrows(RequestTooLargeException::class.java) { accumulator.append(byteArrayOf(4, 5)) }
        assertEquals(4, accumulator.size)
    }
}
