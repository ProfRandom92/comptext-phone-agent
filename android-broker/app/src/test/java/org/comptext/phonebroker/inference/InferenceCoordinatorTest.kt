package org.comptext.phonebroker.inference

import java.util.concurrent.atomic.AtomicInteger
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.runCurrent
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
class InferenceCoordinatorTest {
    @Test fun `allows only one queued inference`() = runTest {
        val active = AtomicInteger(0)
        val peak = AtomicInteger(0)
        val coordinator = InferenceCoordinator(timeoutMillis = 5_000, maxQueued = 1)
        val work: suspend () -> String = {
            peak.updateAndGet { maxOf(it, active.incrementAndGet()) }
            delay(50)
            active.decrementAndGet()
            "ok"
        }
        val first = async { coordinator.run(work) }
        val second = async { coordinator.run(work) }
        runCurrent()
        assertThrows(InferenceBusyException::class.java) { kotlinx.coroutines.runBlocking { coordinator.run(work) } }
        assertEquals("ok", first.await())
        assertEquals("ok", second.await())
        assertEquals(1, peak.get())
    }
}
