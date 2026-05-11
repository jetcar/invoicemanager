"""Auto-generated API client from specs/invoice-service/v1/openapi.json. DO NOT EDIT."""

from __future__ import annotations

from typing import Any

import httpx


class InvoiceApiClient:
    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout

    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:
        merged = dict(headers or {})
        if self.token and 'Authorization' not in merged:
            merged['Authorization'] = f'Bearer {self.token}'
        return merged

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:
            return client.request(method=method, url=path, **kwargs)

    def api_import_invoice_api_v1_invoices_api_import__api_key__post(self, api_key: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/api-import/{api_key}".format(api_key=api_key)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def list_invoices_api_v1_invoices__company_id__get(self, company_id: str, invoice_type: Any | None = None, status: Any | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}".format(company_id=company_id)
        params = {'invoice_type': invoice_type, 'status': status}
        params = {k: v for k, v in params.items() if v is not None}
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def create_invoice_api_v1_invoices__company_id__post(self, company_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}".format(company_id=company_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def list_automation_rules_api_v1_invoices__company_id__automation_rules_get(self, company_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/automation-rules".format(company_id=company_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def create_automation_rule_api_v1_invoices__company_id__automation_rules_post(self, company_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/automation-rules".format(company_id=company_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def delete_automation_rule_api_v1_invoices__company_id__automation_rules__rule_id__delete(self, company_id: str, rule_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/automation-rules/{rule_id}".format(company_id=company_id, rule_id=rule_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('DELETE', path, **kwargs)

    def upload_einvoice_api_v1_invoices__company_id__upload_einvoice_post(self, company_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/upload-einvoice".format(company_id=company_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def delete_invoice_api_v1_invoices__company_id___invoice_id__delete(self, company_id: str, invoice_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('DELETE', path, **kwargs)

    def get_invoice_api_v1_invoices__company_id___invoice_id__get(self, company_id: str, invoice_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def update_invoice_api_v1_invoices__company_id___invoice_id__patch(self, company_id: str, invoice_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('PATCH', path, **kwargs)

    def list_comments_api_v1_invoices__company_id___invoice_id__comments_get(self, company_id: str, invoice_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/comments".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def add_comment_api_v1_invoices__company_id___invoice_id__comments_post(self, company_id: str, invoice_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/comments".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def list_confirmation_steps_api_v1_invoices__company_id___invoice_id__confirmation_steps_get(self, company_id: str, invoice_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def add_confirmation_step_api_v1_invoices__company_id___invoice_id__confirmation_steps_post(self, company_id: str, invoice_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def decide_confirmation_step_api_v1_invoices__company_id___invoice_id__confirmation_steps__step_id__decide_post(self, company_id: str, invoice_id: str, step_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps/{step_id}/decide".format(company_id=company_id, invoice_id=invoice_id, step_id=step_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def list_transaction_rows_api_v1_invoices__company_id___invoice_id__transaction_rows_get(self, company_id: str, invoice_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)

    def create_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows_post(self, company_id: str, invoice_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def merge_transaction_rows_api_v1_invoices__company_id___invoice_id__transaction_rows_merge_post(self, company_id: str, invoice_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/merge".format(company_id=company_id, invoice_id=invoice_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def delete_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__delete(self, company_id: str, invoice_id: str, row_id: str, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}".format(company_id=company_id, invoice_id=invoice_id, row_id=row_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('DELETE', path, **kwargs)

    def update_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__patch(self, company_id: str, invoice_id: str, row_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}".format(company_id=company_id, invoice_id=invoice_id, row_id=row_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('PATCH', path, **kwargs)

    def split_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__split_post(self, company_id: str, invoice_id: str, row_id: str, json_body: dict[str, Any] | None = None, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = f"/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}/split".format(company_id=company_id, invoice_id=invoice_id, row_id=row_id)
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        if json_body is not None:
            kwargs['json'] = json_body
        return self._request('POST', path, **kwargs)

    def health_health_get(self, headers: dict[str, str] | None = None, timeout: float | None = None) -> httpx.Response:
        path = "/health"
        params = None
        req_timeout = self.timeout if timeout is None else timeout
        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}
        return self._request('GET', path, **kwargs)
