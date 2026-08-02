package org.comptext.phonebroker.security

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BearerAuthenticatorTest {
    private val auth = BearerAuthenticator { "correct-horse-battery-staple" }

    @Test fun `accepts exact bearer token`() {
        assertTrue(auth.isAuthorized("Bearer correct-horse-battery-staple"))
    }

    @Test fun `rejects missing malformed and mismatched credentials`() {
        assertFalse(auth.isAuthorized(null))
        assertFalse(auth.isAuthorized("Basic abc"))
        assertFalse(auth.isAuthorized("Bearer wrong"))
        assertFalse(auth.isAuthorized("Bearer  correct-horse-battery-staple"))
    }
}
