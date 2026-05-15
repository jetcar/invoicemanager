{{/*
Expand the chart name
*/}}
{{- define "invoicemanager.name" -}}
{{- .Chart.Name }}
{{- end }}

{{/*
Create a default fully qualified app name
*/}}
{{- define "invoicemanager.fullname" -}}
{{- .Chart.Name }}
{{- end }}

{{/*
Common labels applied to all resources
*/}}
{{- define "invoicemanager.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: invoicemanager
{{- end }}

{{/*
Selector labels for a specific service
Usage: include "invoicemanager.selectorLabels" (dict "name" "auth-service")
*/}}
{{- define "invoicemanager.selectorLabels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/part-of: invoicemanager
{{- end }}

{{/*
Image reference for an app service
Usage: include "invoicemanager.image" (dict "global" .Values.global "svc" .svc)
*/}}
{{- define "invoicemanager.image" -}}
{{ .global.imageRegistry }}/{{ .svc.image }}:{{ .global.imageTag }}
{{- end }}

{{/*
HAProxy config content rendered into the ConfigMap and hashed for rollout annotations.
*/}}
{{- define "invoicemanager.haproxyConfig" -}}
global
    log stdout format raw local0
    maxconn 50000

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor
    option  http-server-close
    timeout connect 5s
    timeout client  30s
    timeout server  30s

frontend stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s

frontend http_in
    bind *:80
    http-request set-header X-Request-ID %[uuid()]

    acl path_auth        path_beg /api/v1/auth
    acl path_companies   path_beg /api/v1/companies
    acl path_orgs        path_beg /api/v1/organizations
    acl path_invoices    path_beg /api/v1/invoices
    acl path_suppliers   path_beg /api/v1/suppliers
    acl path_notify      path_beg /api/v1/notifications
    acl path_audit       path_beg /api/v1/audit
    acl path_archive     path_beg /api/v1/archive

    use_backend auth_backend         if path_auth
    use_backend company_backend      if path_companies
    use_backend company_backend      if path_orgs
    use_backend invoice_backend      if path_invoices
    use_backend supplier_backend     if path_suppliers
    use_backend notification_backend if path_notify
    use_backend audit_backend        if path_audit
    use_backend archive_backend      if path_archive

    acl path_health path_beg /health
    use_backend health_backend if path_health

    default_backend auth_backend

backend auth_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server auth1 auth-service:8000 check inter 10s rise 2 fall 3

backend company_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server company1 company-service:8000 check inter 10s rise 2 fall 3

backend invoice_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server invoice1 invoice-service:8000 check inter 10s rise 2 fall 3

backend supplier_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server supplier1 supplier-service:8000 check inter 10s rise 2 fall 3

backend notification_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server notification1 notification-service:8000 check inter 10s rise 2 fall 3

backend audit_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server audit1 audit-service:8000 check inter 10s rise 2 fall 3

backend archive_backend
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    server archive1 archive-service:8000 check inter 10s rise 2 fall 3

backend health_backend
    balance roundrobin
    server auth1 auth-service:8000 check
{{- end }}
