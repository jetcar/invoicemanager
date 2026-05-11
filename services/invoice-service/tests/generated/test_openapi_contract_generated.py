"""Auto-generated contract tests from specs/invoice-service/v1/openapi.json. DO NOT EDIT."""

from __future__ import annotations

import json
from pathlib import Path

from app.main import app

EXPECTED_OPERATIONS = json.loads('''[
  {
    "method": "post",
    "path": "/api/v1/invoices/api-import/{api_key}",
    "operation_id": "api_import_invoice_api_v1_invoices_api_import__api_key__post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}",
    "operation_id": "list_invoices_api_v1_invoices__company_id__get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}",
    "operation_id": "create_invoice_api_v1_invoices__company_id__post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}/automation-rules",
    "operation_id": "list_automation_rules_api_v1_invoices__company_id__automation_rules_get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/automation-rules",
    "operation_id": "create_automation_rule_api_v1_invoices__company_id__automation_rules_post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "delete",
    "path": "/api/v1/invoices/{company_id}/automation-rules/{rule_id}",
    "operation_id": "delete_automation_rule_api_v1_invoices__company_id__automation_rules__rule_id__delete",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/upload-einvoice",
    "operation_id": "upload_einvoice_api_v1_invoices__company_id__upload_einvoice_post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "delete",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}",
    "operation_id": "delete_invoice_api_v1_invoices__company_id___invoice_id__delete",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}",
    "operation_id": "get_invoice_api_v1_invoices__company_id___invoice_id__get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "patch",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}",
    "operation_id": "update_invoice_api_v1_invoices__company_id___invoice_id__patch",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/comments",
    "operation_id": "list_comments_api_v1_invoices__company_id___invoice_id__comments_get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/comments",
    "operation_id": "add_comment_api_v1_invoices__company_id___invoice_id__comments_post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps",
    "operation_id": "list_confirmation_steps_api_v1_invoices__company_id___invoice_id__confirmation_steps_get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps",
    "operation_id": "add_confirmation_step_api_v1_invoices__company_id___invoice_id__confirmation_steps_post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/confirmation-steps/{step_id}/decide",
    "operation_id": "decide_confirmation_step_api_v1_invoices__company_id___invoice_id__confirmation_steps__step_id__decide_post",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows",
    "operation_id": "list_transaction_rows_api_v1_invoices__company_id___invoice_id__transaction_rows_get",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows",
    "operation_id": "create_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows_post",
    "responses": [
      "201",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/merge",
    "operation_id": "merge_transaction_rows_api_v1_invoices__company_id___invoice_id__transaction_rows_merge_post",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "delete",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}",
    "operation_id": "delete_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__delete",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "patch",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}",
    "operation_id": "update_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__patch",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "post",
    "path": "/api/v1/invoices/{company_id}/{invoice_id}/transaction-rows/{row_id}/split",
    "operation_id": "split_transaction_row_api_v1_invoices__company_id___invoice_id__transaction_rows__row_id__split_post",
    "responses": [
      "200",
      "422"
    ]
  },
  {
    "method": "get",
    "path": "/health",
    "operation_id": "health_health_get",
    "responses": [
      "200"
    ]
  }
]''')
SPEC_PATH = Path(__file__).resolve().parents[4] / 'specs' / 'invoice-service' / 'v1' / 'openapi.json'


def _runtime_operations() -> dict[tuple[str, str], dict]:
    runtime = app.openapi()
    result = {}
    for path, methods in runtime.get('paths', {}).items():
        for method, operation in methods.items():
            if method.lower() not in {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}:
                continue
            result[(path, method.lower())] = operation
    return result


def test_spec_file_exists_and_is_valid_json() -> None:
    assert SPEC_PATH.exists(), f'Missing OpenAPI spec: {SPEC_PATH}'
    data = json.loads(SPEC_PATH.read_text(encoding='utf-8'))
    assert isinstance(data, dict)
    assert 'openapi' in data


def test_runtime_paths_and_methods_match_committed_spec() -> None:
    runtime_ops = _runtime_operations()
    expected_set = {(item['path'], item['method']) for item in EXPECTED_OPERATIONS}
    runtime_set = set(runtime_ops.keys())
    assert runtime_set == expected_set


def test_runtime_operation_ids_and_responses_match_spec() -> None:
    runtime_ops = _runtime_operations()
    for expected in EXPECTED_OPERATIONS:
        op = runtime_ops[(expected['path'], expected['method'])]
        assert op.get('operationId') == expected['operation_id']
        response_keys = set((op.get('responses') or {}).keys())
        for response_code in expected['responses']:
            assert response_code in response_keys
