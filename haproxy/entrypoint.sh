#!/bin/sh
set -eu

required_vars="
AUTH_BACKEND_HOST
COMPANY_BACKEND_HOST
INVOICE_BACKEND_HOST
SUPPLIER_BACKEND_HOST
NOTIFICATION_BACKEND_HOST
AUDIT_BACKEND_HOST
ARCHIVE_BACKEND_HOST
"

for v in $required_vars; do
  val="$(printenv "$v" || true)"
  if [ -z "$val" ]; then
    echo "ERROR: $v is required but not set or empty. Configure it in your Railway service environment variables." >&2
    exit 1
  fi
done

envsubst < /usr/local/etc/haproxy/haproxy.railway.template.cfg > /usr/local/etc/haproxy/haproxy.cfg
exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg
