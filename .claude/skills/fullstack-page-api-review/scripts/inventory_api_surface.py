#!/usr/bin/env python3
"""Print a lightweight FE endpoint and Spring controller inventory."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Optional


SPRING_MAPPING = re.compile(
    r"@(Get|Post|Put|Patch|Delete|Request)Mapping"
    r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)".*?\))?'
)
REQUEST_METHOD = re.compile(r"RequestMethod\.(GET|POST|PUT|PATCH|DELETE)")
FE_GROUP = re.compile(r"^\s{2}([A-Z][A-Z0-9_]*)\s*:\s*\{\s*$")
FE_ENTRY = re.compile(
    r"^\s{4}([A-Z][A-Z0-9_]*)\s*:\s*(?:\([^)]*\)\s*=>\s*)?[`'\"]([^`'\"]+)"
)
SERVICE_CALL = re.compile(
    r"\b(?:apiClient|bookingClient)\.(get|post|put|patch|delete)"
    r"\(\s*(API_ENDPOINTS\.[A-Z0-9_.]+)"
)
LOCAL_IMPORT = re.compile(r"from\s+['\"]@/([^'\"]+)['\"]")
PAGE_EVIDENCE = re.compile(
    r"@/services/|@/stores/|\b(?:trip|bus|route|user|ticket|booking|payment|revenue)"
    r"(?:Service|Store)\.[A-Za-z_][A-Za-z0-9_]*\s*\("
)


def line_ref(path: Path, root: Path, line_number: int) -> str:
    return f"{path.relative_to(root)}:{line_number}"


def normalize_path(base: str, child: str) -> str:
    joined = "/".join(part.strip("/") for part in (base, child) if part.strip("/"))
    return f"/{joined}" if joined else "/"


def resolve_root(candidate: Optional[Path]) -> Path:
    start = (candidate or Path.cwd()).resolve()
    for path in (start, *start.parents):
        if (path / ".codex").is_dir() and (path / "booking_ticket_vue").is_dir():
            return path
    raise SystemExit("Could not resolve System_bus root. Pass --root explicitly.")


def resolve_frontend_import(src_dir: Path, import_path: str) -> Optional[Path]:
    base = src_dir / import_path
    candidates = [base, base.with_suffix(".js"), base.with_suffix(".vue"), base / "index.js"]
    return next((path for path in candidates if path.is_file()), None)


def page_dependency_evidence(
    root: Path, frontend: Path, page_value: Optional[str]
) -> list[tuple[str, str, str]]:
    if not page_value:
        return []

    page = Path(page_value)
    if not page.is_absolute():
        page = root / page
        if not page.exists():
            page = frontend / page_value
    if not page.exists():
        raise SystemExit(f"Page not found: {page_value}")

    src_dir = frontend / "src"
    pending = [page.resolve()]
    visited: set[Path] = set()
    evidence: list[tuple[str, str, str]] = []

    while pending:
        path = pending.pop()
        if path in visited or not path.is_file():
            continue
        visited.add(path)

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines, start=1):
            if PAGE_EVIDENCE.search(line):
                evidence.append(
                    (
                        path.relative_to(frontend).as_posix(),
                        str(index),
                        line.strip(),
                    )
                )

            for import_path in LOCAL_IMPORT.findall(line):
                dependency = resolve_frontend_import(src_dir, import_path)
                if dependency and dependency.resolve() not in visited:
                    pending.append(dependency.resolve())

    return sorted(evidence)


def java_inventory(root: Path, backend: Path) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []

    for path in sorted(backend.rglob("*Controller.java")):
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        class_path = ""

        for index, line in enumerate(lines, start=1):
            match = SPRING_MAPPING.search(line)
            if not match:
                continue

            kind, mapped_path = match.groups()
            mapped_path = mapped_path or ""
            following = "\n".join(lines[index - 1 : min(index + 3, len(lines))])

            if kind == "Request" and "class " in following:
                class_path = mapped_path
                continue

            if kind == "Request":
                method_match = REQUEST_METHOD.search(line)
                method = method_match.group(1) if method_match else "ANY"
            else:
                method = kind.upper()

            results.append(
                (
                    method,
                    normalize_path(class_path, mapped_path),
                    line_ref(path, root, index),
                )
            )

    return results


def frontend_constants(root: Path, endpoint_file: Path) -> list[tuple[str, str, str]]:
    if not endpoint_file.exists():
        return []

    results: list[tuple[str, str, str]] = []
    group = ""

    for index, line in enumerate(endpoint_file.read_text(encoding="utf-8").splitlines(), start=1):
        group_match = FE_GROUP.match(line)
        if group_match:
            group = group_match.group(1)
            continue

        entry_match = FE_ENTRY.match(line)
        if entry_match and group:
            name, value = entry_match.groups()
            results.append((f"{group}.{name}", value, line_ref(endpoint_file, root, index)))

    return results


def frontend_services(root: Path, services_dir: Path) -> list[tuple[str, str, str]]:
    results: list[tuple[str, str, str]] = []

    for path in sorted(services_dir.glob("*.js")):
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            match = SERVICE_CALL.search(line)
            if match:
                method, endpoint = match.groups()
                results.append((method.upper(), endpoint, line_ref(path, root, index)))

    return results


def print_table(title: str, headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> None:
    print(f"\n## {title}\n")
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        print("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--frontend", default="booking_ticket_vue")
    parser.add_argument("--backend", default="ticket-system")
    parser.add_argument("--page", help="Page path relative to root or frontend")
    args = parser.parse_args()

    root = resolve_root(args.root)
    frontend = root / args.frontend
    backend = root / args.backend

    print("# API Surface Inventory")
    print("\nDiscovery output only. Verify contracts in source before marking an API READY.")

    print_table(
        "Target page dependency evidence",
        ("File", "Line", "Evidence"),
        page_dependency_evidence(root, frontend, args.page),
    )
    print_table(
        "Frontend endpoint constants",
        ("Constant", "Path", "Source"),
        frontend_constants(root, frontend / "src/constants/api_endpoint.js"),
    )
    print_table(
        "Frontend service calls",
        ("Method", "Endpoint constant", "Source"),
        frontend_services(root, frontend / "src/services"),
    )
    print_table(
        "Spring controller mappings",
        ("Method", "Path", "Source"),
        java_inventory(root, backend),
    )


if __name__ == "__main__":
    main()
