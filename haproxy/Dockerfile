FROM haproxy:2.9-alpine

RUN apk add --no-cache gettext

COPY haproxy.railway.template.cfg /usr/local/etc/haproxy/haproxy.template.cfg
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Defaults for internal DNS hostnames; override these env vars per platform if names differ.
ENV AUTH_BACKEND_HOST=auth-service.internal \
    COMPANY_BACKEND_HOST=company-service.internal \
    INVOICE_BACKEND_HOST=invoice-service.internal \
    SUPPLIER_BACKEND_HOST=supplier-service.internal \
    NOTIFICATION_BACKEND_HOST=notification-service.internal \
    AUDIT_BACKEND_HOST=audit-service.internal \
    ARCHIVE_BACKEND_HOST=archive-service.internal

EXPOSE 80

CMD ["/entrypoint.sh"]
