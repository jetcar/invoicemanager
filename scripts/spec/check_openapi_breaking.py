#!/usr/bin/env python3
"""Basic breaking-change checks between two OpenAPI specs.

Breaking changes detected:
- removed paths
- removed operations from existing paths
- removed response status codes for existing operations
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def load_spec(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_breaking_changes(base: dict[str, Any], head: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    base_paths = base.get("paths", {})
    head_paths = head.get("paths", {})

    for path, base_methods in sorted(base_paths.items()):
        if path not in head_paths:
            issues.append(f"Removed path: {path}")
            continue

        head_methods = head_paths[path]
        for method, base_op in sorted(base_methods.items()):
            method_l = method.lower()
            if method_l not in HTTP_METHODS:
                continue

            if method not in head_methods:
                issues.append(f"Removed operation: {method.upper()} {path}")
                continue

            base_responses = set((base_op.get("responses") or {}).keys())
            head_responses = set((head_methods[method].get("responses") or {}).keys())
            removed_responses = sorted(base_responses - head_responses)
            if removed_responses:
                issues.append(
                    f"Removed response codes for {method.upper()} {path}: {', '.join(removed_responses)}"
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenAPI backward compatibility")
    parser.add_argument("--base", type=Path, required=True, help="Base branch spec path")
    parser.add_argument("--head", type=Path, required=True, help="Current branch spec path")
    args = parser.parse_args()

    if not args.base.exists():
        print(f"Base spec not found ({args.base}); skipping breaking-change check.")
        return 0

    if not args.head.exists():
        print(f"Head spec missing ({args.head}); cannot evaluate compatibility.")
        return 1

    base = load_spec(args.base)
    head = load_spec(args.head)
    issues = find_breaking_changes(base, head)

    if issues:
        print("Breaking OpenAPI changes detected:")
        for item in issues:
            print(f"- {item}")
        return 1

    print("No breaking OpenAPI changes detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
