package org.comptext.phonebroker.inference

import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withTimeout

class InferenceBusyException : IllegalStateException("inference queue is full")

class InferenceCoordinator(
    private val timeoutMillis: Long = 30_000,
    private val maxQueued: Int = 1,
) {
    private val mutex = Mutex()
    private val admitted = AtomicInteger(0)

    init {
        require(timeoutMillis in 1_000..120_000)
        require(maxQueued in 0..8)
    }

    suspend fun <T> run(work: suspend () -> T): T {
        while (true) {
            val current = admitted.get()
            if (current >= maxQueued + 1) throw InferenceBusyException()
            if (admitted.compareAndSet(current, current + 1)) break
        }
        try {
            return withTimeout(timeoutMillis) { mutex.withLock { work() } }
        } finally {
            admitted.decrementAndGet()
        }
    }
}
