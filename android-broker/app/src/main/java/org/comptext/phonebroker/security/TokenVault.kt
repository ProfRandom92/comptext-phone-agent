package org.comptext.phonebroker.security

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.security.SecureRandom
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class TokenVault(context: Context) {
    private val preferences = context.getSharedPreferences("broker_credentials", Context.MODE_PRIVATE)
    private val random = SecureRandom()

    @Synchronized fun getOrCreate(): String {
        val encrypted = preferences.getString(KEY_CIPHERTEXT, null)
        val nonce = preferences.getString(KEY_NONCE, null)
        if (encrypted != null && nonce != null) return decrypt(encrypted, nonce)
        return regenerate()
    }

    @Synchronized fun regenerate(): String {
        val bytes = ByteArray(32).also(random::nextBytes)
        val token = Base64.encodeToString(bytes, Base64.URL_SAFE or Base64.NO_WRAP or Base64.NO_PADDING)
        val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.ENCRYPT_MODE, key()) }
        val encrypted = cipher.doFinal(token.toByteArray(Charsets.UTF_8))
        check(preferences.edit()
            .putString(KEY_CIPHERTEXT, Base64.encodeToString(encrypted, Base64.NO_WRAP))
            .putString(KEY_NONCE, Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .commit()) { "could not persist broker credential" }
        return token
    }

    private fun decrypt(encrypted: String, nonce: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply {
            init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(nonce, Base64.NO_WRAP)))
        }
        return String(cipher.doFinal(Base64.decode(encrypted, Base64.NO_WRAP)), Charsets.UTF_8)
    }

    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
            init(KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            ).setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build())
            generateKey()
        }
    }

    private companion object {
        const val KEY_ALIAS = "comptext_phone_broker_token_v1"
        const val KEY_CIPHERTEXT = "ciphertext"
        const val KEY_NONCE = "nonce"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
    }
}
