package org.comptext.phonebroker.model

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.io.File

data class ModelRecord(val name: String, val path: String, val size: Long, val sha256: String)

class ModelRegistry(private val context: Context) {
    private val preferences = context.getSharedPreferences("model_registry", Context.MODE_PRIVATE)
    private val gson = Gson()
    private val store = AtomicModelStore(File(context.filesDir, "models"))

    @Synchronized fun list(): List<ModelRecord> = read().sortedBy { it.name }

    @Synchronized fun find(name: String): ModelRecord? = read().firstOrNull { it.name == name && File(it.path).isFile }

    @Synchronized fun import(uri: Uri): ModelRecord {
        val displayName = context.contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) cursor.getString(0) else null
        } ?: throw ModelValidationException("selected document has no display name")
        val input = context.contentResolver.openInputStream(uri) ?: throw ModelValidationException("selected document cannot be read")
        val imported = store.import(displayName, input)
        val record = ModelRecord(imported.name, imported.file.absolutePath, imported.size, imported.sha256)
        val records = read().filterNot { it.name == record.name } + record
        check(preferences.edit().putString(RECORDS, gson.toJson(records)).commit()) { "could not persist model registry" }
        return record
    }

    private fun read(): List<ModelRecord> {
        val json = preferences.getString(RECORDS, null) ?: return emptyList()
        return runCatching {
            val type = object : TypeToken<List<ModelRecord>>() {}.type
            gson.fromJson<List<ModelRecord>>(json, type).filter { record ->
                record.name == ModelPolicy.normalizeName(record.name) &&
                    record.sha256.matches(Regex("[0-9a-f]{64}")) &&
                    File(record.path).canonicalFile.parentFile == File(context.filesDir, "models").canonicalFile
            }
        }.getOrDefault(emptyList())
    }

    private companion object { const val RECORDS = "records" }
}
