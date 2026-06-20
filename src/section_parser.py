from __future__ import annotations

import re
from collections import OrderedDict

from src.docx_loader import ParagraphData


SECTION_ALIASES = OrderedDict(
    [
        ("초록", ["초록", "국문초록", "abstract"]),
        ("서론", ["서론", "연구의 배경", "introduction"]),
        (
            "선행연구 또는 이론적 배경",
            [
                "선행연구",
                "이론적 배경",
                "문헌연구",
                "문헌 고찰",
                "literature review",
                "theoretical background",
            ],
        ),
        (
            "연구방법",
            [
                "연구방법",
                "연구 방법",
                "연구설계",
                "자료 및 방법",
                "methodology",
                "methods",
            ],
        ),
        (
            "분석결과",
            ["분석결과", "연구결과", "실증분석", "결과", "results", "findings"],
        ),
        ("논의", ["논의", "토론", "discussion"]),
        (
            "결론",
            ["결론", "결론 및 시사점", "요약 및 결론", "conclusion", "conclusions"],
        ),
        ("참고문헌", ["참고문헌", "references", "bibliography"]),
    ]
)


def _normalize_heading(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"^[<\[]?\s*(?:제\s*)?[ivxlcdm\d]+(?:장|절)?[.\-\s:>]*", "", text)
    text = re.sub(r"[<>\[\]().:：\-_\s]", "", text)
    return text


def _match_section(paragraph: ParagraphData) -> str | None:
    text = paragraph.text.strip()
    if len(text) > 80:
        return None

    normalized = _normalize_heading(text)
    heading_style = "heading" in paragraph.style_name.lower() or "제목" in paragraph.style_name

    for section, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            alias_normalized = _normalize_heading(alias)
            if normalized == alias_normalized:
                return section
            if heading_style and normalized.startswith(alias_normalized):
                return section
    return None


def parse_sections(paragraphs: list[ParagraphData]) -> OrderedDict[str, str]:
    collected: OrderedDict[str, list[str]] = OrderedDict(
        (section, []) for section in SECTION_ALIASES
    )
    preamble: list[str] = []
    current: str | None = None

    for paragraph in paragraphs:
        matched = _match_section(paragraph)
        if matched:
            current = matched
            continue
        if current is None:
            preamble.append(paragraph.text)
        else:
            collected[current].append(paragraph.text)

    result: OrderedDict[str, str] = OrderedDict()
    if preamble:
        result["제목 및 기타 앞부분"] = "\n".join(preamble)
    for section, lines in collected.items():
        result[section] = "\n".join(lines)
    return result
