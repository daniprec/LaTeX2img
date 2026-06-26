from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).lower()


def clean(value: object) -> str:
    return str(value or "").strip()


def read_csv_text(raw: str) -> List[List[str]]:
    sample = raw[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.get_dialect("excel")
    return list(csv.reader(raw.splitlines(), dialect))


def read_csv_bytes(data: bytes) -> List[List[str]]:
    return read_csv_text(data.decode("utf-8-sig", errors="replace"))


def read_csv(path: Path) -> List[List[str]]:
    return read_csv_text(path.read_text(encoding="utf-8-sig", errors="replace"))


def rows_to_csv_text(rows: Sequence[Sequence[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerows(rows)
    return output.getvalue()


def rows_to_csv_bytes(rows: Sequence[Sequence[str]]) -> bytes:
    return rows_to_csv_text(rows).encode("utf-8")


def write_csv(path: Path, rows: Sequence[Sequence[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writerows(rows)


def first_header_row(rows: Sequence[Sequence[str]], required: Iterable[str]) -> int:
    req = [norm(x) for x in required]
    for idx, row in enumerate(rows):
        normalized = [norm(c) for c in row]
        if all(any(r == cell or r in cell for cell in normalized) for r in req):
            return idx
    raise ValueError(f"Could not find a header row containing: {', '.join(required)}")


def first_available_header_row(
    rows: Sequence[Sequence[str]], required_groups: Sequence[Sequence[str]]
) -> int:
    for required in required_groups:
        try:
            return first_header_row(rows, required)
        except ValueError:
            continue
    required = sorted({item for group in required_groups for item in group})
    raise ValueError(f"Could not find a header row containing one of: {', '.join(required)}")


def local_part(value: str) -> str:
    value = clean(value)
    if "@" in value:
        value = value.split("@", 1)[0]
    return value


def key_variants(value: object) -> List[str]:
    text = clean(value)
    if not text:
        return []
    local = local_part(text)
    variants = [norm(text), norm(local)]
    if "." in local:
        variants.append(norm(local.split(".", 1)[0]))
    if "_" in local:
        variants.append(norm(local.split("_", 1)[0]))
    return list(dict.fromkeys(v for v in variants if v))


@dataclass
class WebWorkExport:
    header: List[str]
    key_idx: int
    project_indices: List[int]
    project_names: List[str]
    rows: List[List[str]]


@dataclass
class BlackboardExport:
    header: List[str]
    key_idx: int
    rows: List[List[str]]


@dataclass
class ConversionResult:
    rows: List[List[str]]
    matched: int
    unmatched: int
    appended_columns: int
    appended_headers: List[str]
    overwritten_headers: List[str]
    unmatched_blackboard_keys: List[str]
    unmatched_webwork_keys: List[str]
    blackboard_key: str
    webwork_key: str


@dataclass
class ColumnAction:
    value_idx: int
    output_idx: int
    header: str
    overwrites_existing: bool


BLACKBOARD_KEY_COLUMNS = ["email", "e-mail", "username", "user id", "login id", "login"]
WEBWORK_KEY_COLUMNS = ["email", "e-mail", "login id", "login", "username", "user id"]


def find_column(header: Sequence[str], key_column: str) -> int:
    wanted = norm(key_column)
    for i, cell in enumerate(header):
        normalized = norm(cell)
        if normalized == wanted or wanted in normalized:
            return i
    raise ValueError(f"Column not found: {key_column}")


def find_preferred_column(header: Sequence[str], preferred: Sequence[str]) -> Optional[int]:
    header_norm = [norm(cell) for cell in header]
    for candidate in preferred:
        for i, cell in enumerate(header_norm):
            if candidate == cell or candidate in cell:
                return i
    return None


def detect_webwork(
    rows: List[List[str]], key_column: Optional[str] = None
) -> WebWorkExport:
    header_idx = first_available_header_row(
        rows, [["email"], ["e-mail"], ["login id"], ["username"], ["user id"]]
    )
    header = [clean(c) for c in rows[header_idx]]
    header_norm = [norm(c) for c in header]

    if key_column is not None:
        try:
            key_idx = find_column(header, key_column)
        except ValueError as exc:
            raise ValueError(f"WebWork key column not found: {key_column}") from exc
    else:
        key_idx = find_preferred_column(header, WEBWORK_KEY_COLUMNS)
        if key_idx is None:
            raise ValueError("Could not detect the WebWork key column.")

    project_indices: List[int] = []
    project_names: List[str] = []
    started = False
    for i, cell in enumerate(header):
        c = norm(cell)
        if c.startswith("problem_set") or c.startswith("problem set"):
            started = True
            project_indices.append(i)
            project_names.append(cell or f"Project_{len(project_indices)}")
        elif started:
            project_indices.append(i)
            project_names.append(cell or f"Project_{len(project_indices)}")

    if not project_indices:
        try:
            score_idx = next(
                i
                for i, cell in enumerate(header_norm)
                if cell in {"%score", "% score", "score"}
            )
        except StopIteration as exc:
            raise ValueError("Could not detect WebWork project columns.") from exc
        project_indices = list(range(score_idx + 1, len(header)))
        project_names = [
            header[i] or f"Project_{j + 1}" for j, i in enumerate(project_indices)
        ]

    data_rows: List[List[str]] = []
    for row in rows[header_idx + 1 :]:
        if not any(clean(c) for c in row):
            continue
        data_rows.append([clean(c) for c in row])

    return WebWorkExport(
        header=header,
        key_idx=key_idx,
        project_indices=project_indices,
        project_names=project_names,
        rows=data_rows,
    )


def detect_blackboard(
    rows: List[List[str]], key_column: Optional[str] = None
) -> BlackboardExport:
    if not rows:
        raise ValueError("Blackboard file is empty.")
    header = [clean(c) for c in rows[0]]

    if key_column is not None:
        try:
            key_idx = find_column(header, key_column)
        except ValueError as exc:
            raise ValueError(f"Blackboard key column not found: {key_column}") from exc
    else:
        key_idx = find_preferred_column(header, BLACKBOARD_KEY_COLUMNS)
        if key_idx is None:
            raise ValueError("Could not detect the Blackboard key column.")

    out_rows = [[clean(c) for c in row] for row in rows]
    for row in out_rows[1:]:
        while len(row) < len(header):
            row.append("")
    return BlackboardExport(header=header, key_idx=key_idx, rows=out_rows)


def build_indexed_lookup(
    webwork: WebWorkExport,
) -> Tuple[Dict[str, Tuple[List[str], int]], Dict[str, List[int]]]:
    lookup: Dict[str, Tuple[List[str], int]] = {}
    variant_records: Dict[str, List[int]] = {}
    for row_idx, row in enumerate(webwork.rows):
        if len(row) <= webwork.key_idx:
            continue
        key = row[webwork.key_idx]
        if not key:
            continue
        values = [row[i] if i < len(row) else "" for i in webwork.project_indices]
        for variant in key_variants(key):
            lookup[variant] = (values, row_idx)
            variant_records.setdefault(variant, []).append(row_idx)
    return lookup, variant_records


def unique_values(values: Iterable[str]) -> List[str]:
    seen = set()
    unique = []
    for value in values:
        cleaned = clean(value)
        if not cleaned:
            continue
        normalized = norm(cleaned)
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(cleaned)
    return unique


def convert_rows(
    blackboard_rows: List[List[str]],
    webwork_rows: List[List[str]],
    blackboard_key: Optional[str] = None,
    webwork_key: Optional[str] = None,
) -> ConversionResult:
    bb = detect_blackboard(blackboard_rows, blackboard_key)
    ww = detect_webwork(webwork_rows, webwork_key)
    lookup, variant_records = build_indexed_lookup(ww)

    out_header = list(bb.header)
    appended_headers: List[str] = []
    overwritten_headers: List[str] = []
    column_actions: List[ColumnAction] = []
    used_names = {norm(h) for h in out_header}
    existing_names = {
        norm(header): idx for idx, header in enumerate(bb.header) if idx != bb.key_idx
    }

    for value_idx, name in enumerate(ww.project_names):
        candidate = clean(name) or "Project"
        existing_idx = existing_names.get(norm(candidate))
        if existing_idx is not None:
            header = out_header[existing_idx]
            overwritten_headers.append(header)
            column_actions.append(
                ColumnAction(
                    value_idx=value_idx,
                    output_idx=existing_idx,
                    header=header,
                    overwrites_existing=True,
                )
            )
            continue

        base = candidate
        suffix = 2
        while norm(candidate) in used_names:
            candidate = f"{base} ({suffix})"
            suffix += 1
        used_names.add(norm(candidate))
        output_idx = len(out_header)
        out_header.append(candidate)
        appended_headers.append(candidate)
        column_actions.append(
            ColumnAction(
                value_idx=value_idx,
                output_idx=output_idx,
                header=candidate,
                overwrites_existing=False,
            )
        )

    out_rows: List[List[str]] = [out_header]
    matched = 0
    unmatched = 0
    matched_webwork_rows = set()
    unmatched_blackboard_keys: List[str] = []

    for row in bb.rows[1:]:
        out = list(row)
        while len(out) < len(out_header):
            out.append("")
        key_value = out[bb.key_idx] if bb.key_idx < len(out) else ""
        values = None
        for variant in key_variants(key_value):
            if variant in lookup:
                values, row_idx = lookup[variant]
                matched_webwork_rows.add(row_idx)
                matched_webwork_rows.update(variant_records.get(variant, []))
                break
        if values is None:
            unmatched += 1
            unmatched_blackboard_keys.append(clean(key_value))
        else:
            matched += 1
            for action in column_actions:
                out[action.output_idx] = values[action.value_idx]
        out_rows.append(out)

    unmatched_webwork_keys = []
    for row_idx, row in enumerate(ww.rows):
        if row_idx in matched_webwork_rows or len(row) <= ww.key_idx:
            continue
        unmatched_webwork_keys.append(row[ww.key_idx])

    return ConversionResult(
        rows=out_rows,
        matched=matched,
        unmatched=unmatched,
        appended_columns=len(appended_headers),
        appended_headers=appended_headers,
        overwritten_headers=unique_values(overwritten_headers),
        unmatched_blackboard_keys=unique_values(unmatched_blackboard_keys),
        unmatched_webwork_keys=unique_values(unmatched_webwork_keys),
        blackboard_key=bb.header[bb.key_idx],
        webwork_key=ww.header[ww.key_idx],
    )


def convert(
    blackboard_path: Path,
    webwork_path: Path,
    output_path: Path,
    blackboard_key: Optional[str] = None,
    webwork_key: Optional[str] = None,
) -> Tuple[int, int, int]:
    result = convert_rows(
        blackboard_rows=read_csv(blackboard_path),
        webwork_rows=read_csv(webwork_path),
        blackboard_key=blackboard_key,
        webwork_key=webwork_key,
    )
    write_csv(output_path, result.rows)
    return result.matched, result.unmatched, result.appended_columns
