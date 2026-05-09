package com.invoicemanager.services

import com.invoicemanager.utils.Constants
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import java.net.HttpURLConnection
import java.net.URL

/**
 * Calls the auth-service magic-link confirm endpoint to confirm a QR login session.
 * The session_token comes from scanning the QR code shown in the desktop browser.
 */
object QRLoginService {

    fun confirmLogin(
        sessionToken: String,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        CoroutineScope(Dispatchers.IO).launch {
            try {
                val url = URL("${Constants.API_BASE_URL}/api/v1/auth/magic-link/confirm/$sessionToken")
                val conn = url.openConnection() as HttpURLConnection
                conn.requestMethod = "POST"
                conn.setRequestProperty("Content-Type", "application/json")
                conn.setRequestProperty("Accept", "application/json")
                conn.connectTimeout = 10_000
                conn.readTimeout = 10_000

                val responseCode = conn.responseCode
                conn.disconnect()

                CoroutineScope(Dispatchers.Main).launch {
                    if (responseCode in 200..299) {
                        onSuccess()
                    } else {
                        onError("Server returned $responseCode")
                    }
                }
            } catch (e: Exception) {
                CoroutineScope(Dispatchers.Main).launch {
                    onError(e.message ?: "Network error")
                }
            }
        }
    }
}
