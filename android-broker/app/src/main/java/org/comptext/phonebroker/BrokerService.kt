package org.comptext.phonebroker

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.IBinder
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import org.comptext.phonebroker.inference.LiteRtEngineController
import org.comptext.phonebroker.model.ModelRegistry
import org.comptext.phonebroker.security.BearerAuthenticator
import org.comptext.phonebroker.security.TokenVault
import org.comptext.phonebroker.server.BrokerDependencies
import org.comptext.phonebroker.server.BrokerHttpServer
import org.comptext.phonebroker.server.ServerPolicy

class BrokerService : Service() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private lateinit var models: ModelRegistry
    private lateinit var engine: LiteRtEngineController
    private lateinit var tokenVault: TokenVault
    private lateinit var preferences: BrokerPreferences
    private var server: BrokerHttpServer? = null

    override fun onCreate() {
        super.onCreate()
        models = ModelRegistry(this)
        engine = LiteRtEngineController(this)
        tokenVault = TokenVault(this)
        preferences = BrokerPreferences(this)
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val action = intent?.action
        if (action == null || action == ACTION_STOP) {
            stopSelf()
            return START_NOT_STICKY
        }
        if (running.compareAndSet(false, true)) {
            ServiceCompat.startForeground(
                this,
                NOTIFICATION_ID,
                notification("Starting local broker"),
                if (Build.VERSION.SDK_INT >= 34) ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE else 0,
            )
            try {
                tokenVault.getOrCreate()
                server = BrokerHttpServer(BrokerDependencies(
                    authenticator = BearerAuthenticator(tokenVault::getOrCreate),
                    models = models,
                    engine = engine,
                    backend = preferences::backend,
                )).also { it.start() }
                lastError = null
                notifyState("Listening on ${ServerPolicy.HOST}:${ServerPolicy.DEFAULT_PORT}")
            } catch (_: Exception) {
                lastError = "Broker failed to start"
                stopSelf()
                return START_NOT_STICKY
            }
        }
        when (action) {
            ACTION_LOAD -> intent.getStringExtra(EXTRA_MODEL)?.let { name ->
                scope.launch {
                    val record = models.find(name)
                    if (record == null) lastError = "Model is not imported"
                    else runCatching { engine.load(record, preferences.backend()) }
                        .onSuccess { lastError = null; notifyState("Loaded ${record.name}") }
                        .onFailure { lastError = "Model load failed" }
                }
            }
            ACTION_UNLOAD -> scope.launch {
                runCatching { engine.unload() }
                    .onSuccess { lastError = null; notifyState("Listening; no model loaded") }
                    .onFailure { lastError = "Model unload failed" }
            }
        }
        return START_NOT_STICKY
    }

    override fun onDestroy() {
        server?.close()
        server = null
        runBlocking(Dispatchers.IO) { runCatching { engine.unload() } }
        scope.cancel()
        running.set(false)
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    private fun createNotificationChannel() {
        getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL_ID, "Local broker", NotificationManager.IMPORTANCE_LOW).apply {
                description = "Visible status for the user-controlled loopback inference broker"
                setShowBadge(false)
            },
        )
    }

    private fun notification(text: String): Notification {
        val stop = PendingIntent.getService(
            this,
            1,
            Intent(this, BrokerService::class.java).setAction(ACTION_STOP),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val open = PendingIntent.getActivity(
            this,
            2,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.stat_sys_download_done)
            .setContentTitle("CompText Phone Broker")
            .setContentText(text)
            .setContentIntent(open)
            .setOngoing(true)
            .setSilent(true)
            .addAction(0, "Stop", stop)
            .build()
    }

    private fun notifyState(text: String) {
        getSystemService(NotificationManager::class.java).notify(NOTIFICATION_ID, notification(text))
    }

    companion object {
        const val ACTION_START = "org.comptext.phonebroker.action.START"
        const val ACTION_STOP = "org.comptext.phonebroker.action.STOP"
        const val ACTION_LOAD = "org.comptext.phonebroker.action.LOAD"
        const val ACTION_UNLOAD = "org.comptext.phonebroker.action.UNLOAD"
        const val EXTRA_MODEL = "model"
        private const val CHANNEL_ID = "comptext_broker"
        private const val NOTIFICATION_ID = 601
        val running = AtomicBoolean(false)
        @Volatile var lastError: String? = null
    }
}
