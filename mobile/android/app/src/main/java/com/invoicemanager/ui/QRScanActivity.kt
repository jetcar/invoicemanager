package com.invoicemanager.ui

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.zxing.integration.android.IntentIntegrator
import com.invoicemanager.databinding.ActivityQrScanBinding
import com.invoicemanager.services.QRLoginService

/**
 * QR scanner activity for passwordless login.
 *
 * Flow:
 * 1. Open ZXing QR scanner
 * 2. Scan the QR code displayed on the desktop browser
 * 3. Send the session token to the auth-service to confirm login
 * 4. The browser polls for confirmation and receives a JWT
 */
class QRScanActivity : AppCompatActivity() {

    private lateinit var binding: ActivityQrScanBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityQrScanBinding.inflate(layoutInflater)
        setContentView(binding.root)

        startQRScanner()
    }

    private fun startQRScanner() {
        IntentIntegrator(this).apply {
            setDesiredBarcodeFormats(IntentIntegrator.QR_CODE)
            setPrompt("Scan the QR code to confirm login")
            setCameraId(0)
            setBeepEnabled(true)
            setBarcodeImageEnabled(false)
            setOrientationLocked(true)
            initiateScan()
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        val result = IntentIntegrator.parseActivityResult(requestCode, resultCode, data)
        if (result != null) {
            if (result.contents != null) {
                // Contents is either a URL with ?token=... or just the token itself
                val token = extractToken(result.contents)
                if (token != null) {
                    confirmLogin(token)
                } else {
                    Toast.makeText(this, "Invalid QR code", Toast.LENGTH_SHORT).show()
                    finish()
                }
            } else {
                // User cancelled scan
                finish()
            }
        } else {
            super.onActivityResult(requestCode, resultCode, data)
        }
    }

    private fun extractToken(content: String): String? {
        return try {
            if (content.startsWith("http")) {
                android.net.Uri.parse(content).getQueryParameter("token")
            } else {
                content.trim().takeIf { it.isNotEmpty() }
            }
        } catch (e: Exception) {
            null
        }
    }

    private fun confirmLogin(sessionToken: String) {
        QRLoginService.confirmLogin(
            sessionToken = sessionToken,
            onSuccess = {
                Toast.makeText(this, "Login confirmed!", Toast.LENGTH_SHORT).show()
                setResult(Activity.RESULT_OK)
                finish()
            },
            onError = { error ->
                Toast.makeText(this, "Login failed: $error", Toast.LENGTH_LONG).show()
                finish()
            }
        )
    }
}
