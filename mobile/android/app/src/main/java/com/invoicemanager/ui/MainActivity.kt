package com.invoicemanager.ui

import android.annotation.SuppressLint
import android.content.Intent
import android.os.Bundle
import android.webkit.*
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.invoicemanager.databinding.ActivityMainBinding
import com.invoicemanager.services.AuthTokenManager
import com.invoicemanager.utils.Constants

/**
 * Main activity: hosts a full-screen WebView that loads the InvoiceManager web UI.
 *
 * Key features:
 * - Full-screen WebView with JavaScript enabled
 * - JavaScript bridge for native features (QR login, push token, biometrics)
 * - Deep link handling for magic login links
 * - Intercepts /qr-scan to open native QR scanner
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var tokenManager: AuthTokenManager

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        tokenManager = AuthTokenManager(this)
        setupWebView()
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        handleIntent(intent)
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        val webView = binding.webView
        webView.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            databaseEnabled = true
            allowFileAccess = false
            allowContentAccess = false
            setSupportZoom(false)
            builtInZoomControls = false
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
            mediaPlaybackRequiresUserGesture = false
        }

        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url.toString()
                // Intercept QR scan request from web UI
                if (url.contains("/qr-scan")) {
                    startQRScanner()
                    return true
                }
                return false
            }

            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame) {
                    Toast.makeText(
                        this@MainActivity,
                        "Connection error: ${error.description}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
        }

        // JavaScript bridge for native features
        webView.addJavascriptInterface(NativeBridge(), "InvoiceManagerNative")

        webView.loadUrl(Constants.BASE_URL)
    }

    private fun handleIntent(intent: Intent?) {
        val uri = intent?.data ?: return
        // Handle invoicemanager://login?token=... deep link (magic login)
        if (uri.scheme == "invoicemanager" && uri.host == "login") {
            val token = uri.getQueryParameter("token") ?: return
            binding.webView.loadUrl("${Constants.BASE_URL}/magic-login?token=$token&source=app")
        }
    }

    private fun startQRScanner() {
        startActivity(Intent(this, QRScanActivity::class.java))
    }

    override fun onBackPressed() {
        if (binding.webView.canGoBack()) {
            binding.webView.goBack()
        } else {
            super.onBackPressed()
        }
    }

    /**
     * JavaScript interface exposed to the web UI as `window.InvoiceManagerNative`.
     */
    inner class NativeBridge {
        /** Return the stored auth token to the web UI. */
        @JavascriptInterface
        fun getAuthToken(): String = tokenManager.getAccessToken() ?: ""

        /** Store an auth token received from the web UI. */
        @JavascriptInterface
        fun setAuthToken(token: String, refreshToken: String) {
            tokenManager.saveTokens(token, refreshToken)
        }

        /** Clear tokens (logout). */
        @JavascriptInterface
        fun clearTokens() {
            tokenManager.clearTokens()
        }

        /** Get the stored FCM push token. */
        @JavascriptInterface
        fun getPushToken(): String = tokenManager.getPushToken() ?: ""

        /** Open native QR scanner for login confirmation. */
        @JavascriptInterface
        fun openQRScanner() = startQRScanner()

        /** Return app version. */
        @JavascriptInterface
        fun getAppVersion(): String = "1.0.0"
    }
}
