package com.invoicemanager.utils

object Constants {
    // Base URL for the web UI (served by HAProxy)
    const val BASE_URL = "https://invoicemanager.yourdomain.com"

    // API base URL (same host – HAProxy routes /api/v1/* to appropriate services)
    const val API_BASE_URL = BASE_URL
}
