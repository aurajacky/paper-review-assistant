from __future__ import annotations

import re
from typing import Any

from src.docx_loader import DocumentData


REFERENCE_PATTERN = re.compile(
    r"(?:<\s*)?(표|그림)\s*(\d+)(?:\s*>)?|"
    r"\b(Table|Figure)\s*(\d+)\b",
    re.IGNORECASE,
)


def inspect_tables_and_figures(document: DocumentData) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    paragraphs = document.paragraphs

    for index, paragraph in enumerate(paragraphs):
        matches = list(REFERENCE_PATTERN.finditer(paragraph.text))
        for match in matches:
            kind = match.group(1) or match.group(3) or "표/그림"
            number = match.group(2) or match.group(4) or "?"
            previous = paragraphs[index - 1].text if index > 0 else ""
            following = paragraphs[index + 1].text if index + 1 < len(paragraphs) else ""

            problems = []
            if len(previous) < 20:
                problems.append("바로 앞의 제시 목적 설명이 짧거나 없습니다.")
            if len(following) < 30:
                problems.append("바로 뒤의 핵심 수치·해석 설명이 짧거나 없습니다.")

            findings.append(
                {
                    "item": f"{kind} {number}",
                    "problem": " ".join(problems) if problems else "인접 설명이 확인됩니다.",
                    "needs_revision": bool(problems),
                    "suggested_sentence": (
                        f"{kind} {number}는 연구질문과 관련된 핵심 결과를 제시하며, "
                        "주요 수치가 의미하는 바를 본문에서 구체적으로 해석할 필요가 있다."
                    ),
                }
            )

    if document.table_count and not any("표" in row["item"] or "Table" in row["item"] for row in findings):
        findings.append(
            {
                "item": "문서 내 표",
                "problem": f"실제 표 {document.table_count}개가 있으나 본문 표 번호 호출을 찾지 못했습니다.",
                "needs_revision": True,
                "suggested_sentence": "다음 <표 1>은 분석대상과 핵심 변수를 요약하여 제시한다.",
            }
        )

    if document.inline_shape_count and not any(
        "그림" in row["item"] or "Figure" in row["item"] for row in findings
    ):
        findings.append(
            {
                "item": "문서 내 그림",
                "problem": (
                    f"인라인 그림 {document.inline_shape_count}개가 있으나 "
                    "본문 그림 번호 호출을 찾지 못했습니다."
                ),
                "needs_revision": True,
                "suggested_sentence": "다음 <그림 1>은 분석 절차와 변수 간 관계를 시각화한다.",
            }
        )

    if not findings:
        findings.append(
            {
                "item": "표/그림 전체",
                "problem": "본문 호출 패턴과 DOCX 표·그림 개체를 찾지 못했습니다.",
                "needs_revision": False,
                "suggested_sentence": "표나 그림을 추가한다면 제시 목적과 결과 해석을 본문에 함께 작성하세요.",
            }
        )
    return findings
