package com.invoicemanager.services

import com.invoicemanager.utils.Constants
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.IOException
import java.util.concurrent.TimeUnit

/**
 * Calls the auth-service magic-link confirm endpoint to confirm a QR login session.
 * The session_token comes from scanning the QR code shown in the desktop browser.
 */
object QRLoginService {

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .writeTimeout(10, TimeUnit.SECONDS)
        .build()

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    fun confirmLogin(
        sessionToken: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = "${Constants.API_BASE_URL}/api/v1/auth/magic-link/confirm/$sessionToken"
                val request = Request.Builder()
                    .url(url)
                    .post("{}".toRequestBody(jsonMediaType))
                    .build()

                httpClient.newCall(request).execute().use { response ->
                    if (response.isSuccessful) {
                        CoroutineScope(Dispatchers.Main).launch { onSuccess() }
                    } else {
                        val msg = "Server returned ${response.code}"
                        CoroutineScope(Dispatchers.Main).launch { onError(msg) }
                    }
                }
            } catch (e: IOException) {
                val msg = e.message ?: "Network error"
                CoroutineScope(Dispatchers.Main).launch { onError(msg) }
            }
        }
    }
}
