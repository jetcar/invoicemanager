#!/usr/bin/env python3
"""Generate invoice-service artifacts from the versioned OpenAPI spec.

Artifacts:
- services/invoice-service/generated/client/python/models.py
- services/invoice-service/generated/client/python/invoice_api_client.py
- services/invoice-service/tests/generated/test_openapi_contract_generated.py
"""

from __future__ import annotations

import argparse
import json
import keyword
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPEC = ROOT / "specs" / "invoice-service" / "v1" / "openapi.json"
DEFAULT_MODELS = ROOT / "services" / "invoice-service" / "generated" / "client" / "python" / "models.py"
DEFAULT_CLIENT = ROOT / "services" / "invoice-service" / "generated" / "client" / "python" / "invoice_api_client.py"
DEFAULT_TESTS = ROOT / "services" / "invoice-service" / "tests" / "generated" / "test_openapi_contract_generated.py"


def to_identifier(value: str) -> str:
    candidate = re.sub(r"[^0-9a-zA-Z_]", "_", value).strip("_").lower()
    if not candidate:
        candidate = "field"
    if candidate and candidate[0].isdigit():
        candidate = f"_{candidate}"
    if keyword.iskeyword(candidate):
        candidate = f"{candidate}_"
    return candidate


def ref_name(ref: str) -> str:
    return ref.split("/")[-1]


def schema_to_type(schema: dict[str, Any]) -> str:
    if "$ref" in schema:
        return ref_name(schema["$ref"])

    schema_type = schema.get("type")
    if schema_type == "array":
        item_type = schema_to_type(schema.get("items", {}))
        return f"list[{item_type}]"
    if schema_type == "object":
        additional_props = schema.get("additionalProperties")
        if isinstance(additional_props, dict):
            return f"dict[str, {schema_to_type(additional_props)}]"
        return "dict[str, Any]"
    if schema_type == "string":
        if schema.get("format") in {"date-time", "date"}:
            return "str"
        return "str"
    if schema_type in {"number"}:
        return "float"
    if schema_type in {"integer"}:
        return "int"
    if schema_type in {"boolean"}:
        return "bool"

    any_of = schema.get("anyOf")
    if any_of:
        types = sorted({schema_to_type(item) for item in any_of})
        return " | ".join(types) if types else "Any"

    one_of = schema.get("oneOf")
    if one_of:
        types = sorted({schema_to_type(item) for item in one_of})
        return " | ".join(types) if types else "Any"

    return "Any"


def generate_models(spec: dict[str, Any]) -> str:
    schemas = spec.get("components", {}).get("schemas", {})
    lines: list[str] = [
        '"""Auto-generated from specs/invoice-service/v1/openapi.json. DO NOT EDIT MANUALLY."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any, TypedDict",
        "",
    ]

    if not schemas:
        lines.append("# No schemas were found in the OpenAPI document.")
        lines.append("")
        return "\n".join(lines)

    for schema_name, schema in sorted(schemas.items()):
        class_name = schema_name
        if schema.get("type") != "object":
            lines.append(f"{class_name} = {schema_to_type(schema)}")
            lines.append("")
            continue

        required = set(schema.get("required", []))
        properties = schema.get("properties", {})
        lines.append(f"class {class_name}(TypedDict, total=False):")
        if required:
            req = ", ".join(sorted(required))
            lines.append(f"    \"\"\"Required fields in OpenAPI: {req}\"\"\"")
        if not properties:
            lines.append("    pass")
        for prop_name, prop_schema in sorted(properties.items()):
            py_name = to_identifier(prop_name)
            annotation = schema_to_type(prop_schema)
            lines.append(f"    {py_name}: {annotation}")
        lines.append("")

    return "\n".join(lines)


def extract_operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    operations: list[dict[str, Any]] = []
    for path, methods in spec.get("paths", {}).items():
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            operation_id = operation.get("operationId") or f"{method}_{path}"
            parameters = operation.get("parameters", [])
            request_body = operation.get("requestBody", {})
            responses = sorted(operation.get("responses", {}).keys())
            operations.append(
                {
                    "path": path,
                    "method": method.lower(),
                    "operation_id": operation_id,
                    "parameters": parameters,
                    "request_body": request_body,
                    "responses": responses,
                }
            )
    return sorted(operations, key=lambda x: (x["path"], x["method"]))


def generate_client(spec: dict[str, Any]) -> str:
    operations = extract_operations(spec)
    lines: list[str] = [
        '"""Auto-generated API client from specs/invoice-service/v1/openapi.json. DO NOT EDIT."""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "from urllib.parse import quote",
        "",
        "import httpx",
        "",
        "",
        "class InvoiceApiClient:",
        "    def __init__(self, base_url: str, token: str | None = None, timeout: float = 30.0) -> None:",
        "        self.base_url = base_url.rstrip('/')",
        "        self.token = token",
        "        self.timeout = timeout",
        "",
        "    def _headers(self, headers: dict[str, str] | None = None) -> dict[str, str]:",
        "        merged = dict(headers or {})",
        "        if self.token and 'Authorization' not in merged:",
        "            merged['Authorization'] = f'Bearer {self.token}'",
        "        return merged",
        "",
        "    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:",
        "        with httpx.Client(base_url=self.base_url, timeout=self.timeout) as client:",
        "            return client.request(method=method, url=path, **kwargs)",
        "",
    ]

    if not operations:
        lines.append("    pass")
        lines.append("")
        return "\n".join(lines)

    for op in operations:
        method_name = to_identifier(op["operation_id"])
        param_defs: list[str] = []
        format_args: list[str] = []
        query_param_map: list[str] = []

        for param in op["parameters"]:
            param_name = param.get("name")
            if not param_name:
                continue
            py_name = to_identifier(param_name)
            location = param.get("in")
            required = bool(param.get("required", False))

            if location == "path":
                param_defs.append(f"{py_name}: str")
                format_args.append(f"{param_name}={py_name}")
            elif location == "query":
                if required:
                    param_defs.append(f"{py_name}: Any")
                else:
                    param_defs.append(f"{py_name}: Any | None = None")
                query_param_map.append(f"'{param_name}': {py_name}")

        request_content = (op["request_body"] or {}).get("content", {}) if isinstance(op["request_body"], dict) else {}
        uses_multipart = "multipart/form-data" in request_content
        has_request_body = bool(op["request_body"])
        if has_request_body:
            if uses_multipart:
                param_defs.append("files: dict[str, Any] | None = None")
            else:
                param_defs.append("json_body: dict[str, Any] | None = None")

        param_defs.extend(["headers: dict[str, str] | None = None", "timeout: float | None = None"])
        signature = ", ".join(["self"] + param_defs)

        lines.append(f"    def {method_name}({signature}) -> httpx.Response:")
        if format_args:
            for param in op["parameters"]:
                if param.get("in") == "path" and param.get("name"):
                    py_name = to_identifier(param["name"])
                    lines.append(f"        {py_name} = quote(str({py_name}), safe='')")
            fmt = ", ".join(format_args)
            lines.append(f"        path = \"{op['path']}\".format({fmt})")
        else:
            lines.append(f"        path = \"{op['path']}\"")

        if query_param_map:
            lines.append(f"        params = {{{', '.join(query_param_map)}}}")
            lines.append("        params = {k: v for k, v in params.items() if v is not None}")
        else:
            lines.append("        params = None")

        lines.append("        req_timeout = self.timeout if timeout is None else timeout")
        lines.append("        kwargs: dict[str, Any] = {'headers': self._headers(headers), 'params': params, 'timeout': req_timeout}")
        if has_request_body:
            if uses_multipart:
                lines.append("        if files is not None:")
                lines.append("            kwargs['files'] = files")
            else:
                lines.append("        if json_body is not None:")
                lines.append("            kwargs['json'] = json_body")
        lines.append(f"        return self._request('{op['method'].upper()}', path, **kwargs)")
        lines.append("")

    return "\n".join(lines)


def generate_contract_tests(spec: dict[str, Any]) -> str:
    operations = extract_operations(spec)
    op_payload = [
        {
            "method": op["method"],
            "path": op["path"],
            "operation_id": op["operation_id"],
            "responses": op["responses"],
        }
        for op in operations
    ]
    payload_json = json.dumps(op_payload, indent=2)

    return "\n".join(
        [
            '"""Auto-generated contract tests from specs/invoice-service/v1/openapi.json. DO NOT EDIT."""',
            "",
            "from __future__ import annotations",
            "",
            "import json",
            "from pathlib import Path",
            "",
            "from app.main import app",
            "",
            f"EXPECTED_OPERATIONS = json.loads('''{payload_json}''')",
            "SPEC_PATH = Path(__file__).resolve().parents[4] / 'specs' / 'invoice-service' / 'v1' / 'openapi.json'",
            "",
            "",
            "def _runtime_operations() -> dict[tuple[str, str], dict]:",
            "    runtime = app.openapi()",
            "    result = {}",
            "    for path, methods in runtime.get('paths', {}).items():",
            "        for method, operation in methods.items():",
            "            if method.lower() not in {'get', 'post', 'put', 'patch', 'delete', 'options', 'head'}:",
            "                continue",
            "            result[(path, method.lower())] = operation",
            "    return result",
            "",
            "",
            "def test_spec_file_exists_and_is_valid_json() -> None:",
            "    assert SPEC_PATH.exists(), f'Missing OpenAPI spec: {SPEC_PATH}'",
            "    data = json.loads(SPEC_PATH.read_text(encoding='utf-8'))",
            "    assert isinstance(data, dict)",
            "    assert 'openapi' in data",
            "",
            "",
            "def test_runtime_paths_and_methods_match_committed_spec() -> None:",
            "    runtime_ops = _runtime_operations()",
            "    expected_set = {(item['path'], item['method']) for item in EXPECTED_OPERATIONS}",
            "    runtime_set = set(runtime_ops.keys())",
            "    assert runtime_set == expected_set",
            "",
            "",
            "def test_runtime_operation_ids_and_responses_match_spec() -> None:",
            "    runtime_ops = _runtime_operations()",
            "    for expected in EXPECTED_OPERATIONS:",
            "        op = runtime_ops[(expected['path'], expected['method'])]",
            "        assert op.get('operationId') == expected['operation_id']",
            "        response_keys = set((op.get('responses') or {}).keys())",
            "        for response_code in expected['responses']:",
            "            assert response_code in response_keys",
            "",
        ]
    )


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate invoice-service artifacts from OpenAPI spec")
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--models-out", type=Path, default=DEFAULT_MODELS)
    parser.add_argument("--client-out", type=Path, default=DEFAULT_CLIENT)
    parser.add_argument("--tests-out", type=Path, default=DEFAULT_TESTS)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text(encoding="utf-8"))

    write_file(args.models_out, generate_models(spec))
    write_file(args.client_out, generate_client(spec))
    write_file(args.tests_out, generate_contract_tests(spec))

    print(f"Generated models: {args.models_out}")
    print(f"Generated client: {args.client_out}")
    print(f"Generated contract tests: {args.tests_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
