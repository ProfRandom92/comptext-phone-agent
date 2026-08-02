package org.comptext.phonebroker.server

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class RateLimiterTest {
    @Test fun `bounds requests in a moving window`() {
        var now = 1_000L
        val limiter = RateLimiter(maxRequests = 2, windowMillis = 1_000) { now }
        assertTrue(limiter.tryAcquire())
        assertTrue(limiter.tryAcquire())
        assertFalse(limiter.tryAcquire())
        now = 2_001L
        assertTrue(limiter.tryAcquire())
    }
}
