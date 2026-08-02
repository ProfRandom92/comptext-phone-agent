# CompText Phone Broker

This native Android companion exposes on-device LiteRT-LM inference to Termux over an
authenticated IPv4 loopback service. It never executes CompText actions and contains no
cloud or remote-server fallback.

## Build

The project pins Gradle 8.14.5, Android Gradle Plugin 8.13.2, Kotlin 2.3.21, and
`com.google.ai.edge.litertlm:litertlm-android:0.15.0`.

```powershell
.\gradlew.bat testDebugUnitTest lintDebug assembleDebug
```

The debug APK is written to `app/build/outputs/apk/debug/app-debug.apk`. Models,
keystores, local SDK paths, build outputs, and credentials are ignored and must never be
committed.

## Use

1. Open the application and explicitly start the foreground broker.
2. Import a compatible `.litertlm` document through the Android system picker.
3. Select CPU or GPU and load the imported model.
4. Reveal or copy the bearer token only when configuring Termux.
5. Merge the copied orchestrator fragment into the CompText YAML configuration and set
   `COMPTEXT_BROKER_TOKEN` in the Termux process.

The server binds only to `127.0.0.1:8080`. Every endpoint requires bearer
authentication. The maximum request body is 256 KiB, inference is serialized, and only
one request may wait behind the active inference. The model import endpoint deliberately
returns `interactive_required`; imports must originate from visible Storage Access
Framework interaction.

The notification can stop the service at any time. The service is not sticky and there
is no boot receiver.
