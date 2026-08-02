package org.comptext.phonebroker

import android.content.Context
import org.comptext.phonebroker.inference.InferenceBackend

class BrokerPreferences(context: Context) {
    private val preferences = context.getSharedPreferences("broker_settings", Context.MODE_PRIVATE)
    fun backend(): InferenceBackend = runCatching {
        InferenceBackend.valueOf(preferences.getString(BACKEND, InferenceBackend.CPU.name)!!)
    }.getOrDefault(InferenceBackend.CPU)
    fun setBackend(value: InferenceBackend) {
        check(preferences.edit().putString(BACKEND, value.name).commit()) { "could not persist backend setting" }
    }
    private companion object { const val BACKEND = "backend" }
}
