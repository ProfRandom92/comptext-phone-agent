package org.comptext.phonebroker.protocol

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class BrokerProtocolTest {
    @Test fun `route request accepts only bounded canonical input`() {
        val request = BrokerProtocol.parseRouteRequest("""{"model":"MobileActions-270M","input":"scan storage"}""")
        assertEquals("MobileActions-270M", request.model)
        assertEquals("scan storage", request.input)
    }

    @Test fun `route request rejects unknown fields`() {
        assertThrows(ProtocolException::class.java) {
            BrokerProtocol.parseRouteRequest("""{"model":"router","input":"x","shell":"rm"}""")
        }
    }

    @Test fun `route request rejects oversized prompt`() {
        val input = "x".repeat(BrokerLimits.MAX_ROUTE_INPUT_CHARS + 1)
        assertThrows(ProtocolException::class.java) {
            BrokerProtocol.parseRouteRequest("""{"model":"router","input":"$input"}""")
        }
    }

    @Test fun `decision schema rejects noncanonical actions`() {
        assertThrows(ProtocolException::class.java) {
            BrokerProtocol.parseDecision("""{"kind":"direct_action","action":"open Intent","arguments":{},"confidence":1}""")
        }
    }

    @Test fun `decision schema rejects duplicate json keys`() {
        assertThrows(ProtocolException::class.java) {
            BrokerProtocol.parseDecision("""{"kind":"reject","kind":"delegate","confidence":1}""")
        }
    }
}
