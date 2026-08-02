import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "org.comptext.phonebroker"
    compileSdk = 36

    defaultConfig {
        applicationId = "org.comptext.phonebroker"
        minSdk = 31
        targetSdk = 36
        versionCode = 601
        versionName = "0.6.1"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    testOptions { unitTests.isReturnDefaultValues = true }
    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
}

kotlin { compilerOptions { jvmTarget.set(JvmTarget.JVM_17) } }

dependencyLocking { lockAllConfigurations() }

dependencies {
    implementation("androidx.activity:activity-ktx:1.13.0")
    // 1.19.0 requires API 37 and AGP 9.1; 1.18.0 is the newest API-36-compatible line.
    implementation("androidx.core:core-ktx:1.18.0")
    implementation("com.google.ai.edge.litertlm:litertlm-android:0.15.0")
    implementation("com.google.code.gson:gson:2.14.0")
    implementation("io.ktor:ktor-server-cio:3.5.2")
    implementation("io.ktor:ktor-server-core:3.5.2")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.11.0")

    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.11.0")
}
