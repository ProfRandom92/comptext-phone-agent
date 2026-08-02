package org.comptext.phonebroker.server

import java.util.ArrayDeque

class RateLimiter(
    private val maxRequests: Int = 60,
    private val windowMillis: Long = 60_000,
    private val clock: () -> Long = System::currentTimeMillis,
) {
    private val requests = ArrayDeque<Long>()

    init {
        require(maxRequests in 1..10_000)
        require(windowMillis > 0)
    }

    @Synchronized fun tryAcquire(): Boolean {
        val now = clock()
        while (requests.isNotEmpty() && now - requests.first() >= windowMillis) requests.removeFirst()
        if (requests.size >= maxRequests) return false
        requests.addLast(now)
        return true
    }
}
