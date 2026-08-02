package org.comptext.phonebroker

import android.Manifest
import android.app.AlertDialog
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.text.InputType
import android.view.ViewGroup
import android.view.View
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.CheckBox
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.comptext.phonebroker.inference.InferenceBackend
import org.comptext.phonebroker.model.ModelRegistry
import org.comptext.phonebroker.security.TokenVault
import org.comptext.phonebroker.server.ServerPolicy

class MainActivity : ComponentActivity() {
    private lateinit var registry: ModelRegistry
    private lateinit var vault: TokenVault
    private lateinit var preferences: BrokerPreferences
    private lateinit var status: TextView
    private lateinit var token: TextView
    private lateinit var models: Spinner
    private lateinit var backend: Spinner

    private val notificationPermission = registerForActivityResult(ActivityResultContracts.RequestPermission()) { refresh() }
    private val modelPicker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) importModel(uri)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        registry = ModelRegistry(this)
        vault = TokenVault(this)
        preferences = BrokerPreferences(this)
        setContentView(buildUi())
        refresh()
    }

    override fun onResume() {
        super.onResume()
        if (::status.isInitialized) refresh()
    }

    private fun buildUi(): ScrollView {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(32, 28, 32, 48)
        }
        fun heading(text: String) = TextView(this).apply { this.text = text; textSize = 22f; setPadding(0, 20, 0, 8) }
        fun button(text: String, action: () -> Unit) = Button(this).apply { this.text = text; setOnClickListener { action() } }

        root.addView(heading("CompText Phone Broker ${BuildConfig.VERSION_NAME}"))
        status = TextView(this).apply { textSize = 16f; importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES }
        root.addView(status)
        root.addView(button("Start local broker") { requestNotifications(); command(BrokerService.ACTION_START) })
        root.addView(button("Stop broker") { stopService(Intent(this, BrokerService::class.java)); refresh() })

        root.addView(heading("Models"))
        models = Spinner(this)
        root.addView(models, ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT)
        root.addView(button("Import .litertlm model") { modelPicker.launch(arrayOf("application/octet-stream", "application/*")) })
        backend = Spinner(this).apply {
            adapter = ArrayAdapter(this@MainActivity, android.R.layout.simple_spinner_dropdown_item, InferenceBackend.entries.map { it.name })
            setSelection(InferenceBackend.entries.indexOf(preferences.backend()))
        }
        root.addView(backend)
        root.addView(button("Load selected model") {
            val name = models.selectedItem as? String ?: return@button toast("Import a model first")
            preferences.setBackend(InferenceBackend.valueOf(backend.selectedItem.toString()))
            command(BrokerService.ACTION_LOAD, name)
        })
        root.addView(button("Unload model") { command(BrokerService.ACTION_UNLOAD) })

        root.addView(heading("Authentication"))
        token = TextView(this).apply {
            text = "••••••••••••••••"
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            setTextIsSelectable(true)
        }
        root.addView(token)
        root.addView(CheckBox(this).apply {
            text = getString(R.string.reveal_token)
            setOnCheckedChangeListener { _, checked -> token.text = if (checked) vault.getOrCreate() else "••••••••••••••••" }
        })
        root.addView(button("Copy Termux configuration") {
            val configuration = """orchestrator:
  router_mode: broker
  router_base_url: http://${ServerPolicy.HOST}:${ServerPolicy.DEFAULT_PORT}
  router_model: MobileActions-270M
  router_token_env: COMPTEXT_BROKER_TOKEN

export COMPTEXT_BROKER_TOKEN=${vault.getOrCreate()}"""
            getSystemService(ClipboardManager::class.java).setPrimaryClip(ClipData.newPlainText("CompText broker configuration", configuration))
            toast("Configuration copied; clipboard contains the bearer token")
        })
        root.addView(button("Regenerate bearer token") {
            AlertDialog.Builder(this)
                .setTitle("Regenerate token?")
                .setMessage("The previous token will stop working immediately.")
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Regenerate") { _, _ -> vault.regenerate(); token.text = "••••••••••••••••"; toast("Token regenerated") }
                .show()
        })

        root.addView(heading("Diagnostics"))
        root.addView(TextView(this).apply {
            text = getString(R.string.diagnostics, ServerPolicy.HOST, ServerPolicy.DEFAULT_PORT)
            setTextIsSelectable(true)
        })
        return ScrollView(this).apply { addView(root) }
    }

    private fun command(action: String, model: String? = null) {
        val intent = Intent(this, BrokerService::class.java).setAction(action)
        if (model != null) intent.putExtra(BrokerService.EXTRA_MODEL, model)
        ContextCompat.startForegroundService(this, intent)
        status.postDelayed({ refresh() }, 400)
    }

    private fun requestNotifications() {
        if (android.os.Build.VERSION.SDK_INT >= 33 && ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            notificationPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
        }
    }

    private fun importModel(uri: Uri) {
        runCatching { contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION) }
        lifecycleScope.launch {
            status.text = getString(R.string.importing_model)
            val result = withContext(Dispatchers.IO) { runCatching { registry.import(uri) } }
            result.onSuccess { toast("Imported ${it.name}") }.onFailure { toast("Import failed: ${it.message ?: "invalid model"}") }
            refresh()
        }
    }

    private fun refresh() {
        val names = registry.list().map { it.name }
        models.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, names)
        val state = if (BrokerService.running.get()) "Running on ${ServerPolicy.HOST}:${ServerPolicy.DEFAULT_PORT}" else "Stopped"
        status.text = listOfNotNull(state, BrokerService.lastError).joinToString("\n")
    }

    private fun toast(message: String) = Toast.makeText(this, message, Toast.LENGTH_LONG).show()
}
