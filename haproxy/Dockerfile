FROM haproxy:2.9-alpine

RUN apk add --no-cache gettext

COPY haproxy.railway.template.cfg /usr/local/etc/haproxy/haproxy.template.cfg

ENV AUTH_BACKEND_HOST=auth-service.internal \
    COMPANY_BACKEND_HOST=company-service.internal \
    INVOICE_BACKEND_HOST=invoice-service.internal \
    SUPPLIER_BACKEND_HOST=supplier-service.internal \
    NOTIFICATION_BACKEND_HOST=notification-service.internal \
    AUDIT_BACKEND_HOST=audit-service.internal \
    ARCHIVE_BACKEND_HOST=archive-service.internal

EXPOSE 80

CMD ["/bin/sh", "-c", "set -eu; for v in AUTH_BACKEND_HOST COMPANY_BACKEND_HOST INVOICE_BACKEND_HOST SUPPLIER_BACKEND_HOST NOTIFICATION_BACKEND_HOST AUDIT_BACKEND_HOST ARCHIVE_BACKEND_HOST; do eval \"val=\\${$v}\"; if [ -z \"$val\" ]; then echo \"$v is required and cannot be empty\" >&2; exit 1; fi; done; envsubst < /usr/local/etc/haproxy/haproxy.template.cfg > /usr/local/etc/haproxy/haproxy.cfg && exec haproxy -f /usr/local/etc/haproxy/haproxy.cfg"]
