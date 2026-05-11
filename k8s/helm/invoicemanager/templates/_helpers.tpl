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
