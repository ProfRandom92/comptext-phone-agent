package org.comptext.phonebroker.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ModelPolicyTest {
    @Test fun `normalizes a safe litertlm display name`() {
        assertEquals("router-270m.litertlm", ModelPolicy.normalizeName(" Router 270M.litertlm "))
    }

    @Test fun `rejects traversal wrong extension and implausible size`() {
        assertThrows(ModelValidationException::class.java) { ModelPolicy.normalizeName("../model.litertlm") }
        assertThrows(ModelValidationException::class.java) { ModelPolicy.normalizeName("model.bin") }
        assertThrows(ModelValidationException::class.java) { ModelPolicy.validateSize(12) }
        assertThrows(ModelValidationException::class.java) { ModelPolicy.validateSize(ModelPolicy.MAX_MODEL_BYTES + 1) }
    }
}
