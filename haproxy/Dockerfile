FROM haproxy:2.9-alpine

RUN apk add --no-cache gettext

COPY haproxy.railway.template.cfg /usr/local/etc/haproxy/haproxy.template.cfg
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Defaults use service names on private networking; override per platform if DNS names differ.
ENV AUTH_BACKEND_HOST=auth-service \
    COMPANY_BACKEND_HOST=company-service \
    INVOICE_BACKEND_HOST=invoice-service \
    SUPPLIER_BACKEND_HOST=supplier-service \
    NOTIFICATION_BACKEND_HOST=notification-service \
    AUDIT_BACKEND_HOST=audit-service \
    ARCHIVE_BACKEND_HOST=archive-service

EXPOSE 80

CMD ["/entrypoint.sh"]
