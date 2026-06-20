from __future__ import annotations

import json
from collections import OrderedDict
from typing import Any

from src.llm_client import LLMClient


ANALYSIS_OPTIONS = OrderedDict(
    [
        ("structure", "구조 정합성"),
        ("theory", "이론적 기여"),
        ("methodology", "방법론 방어"),
        ("tables_figures", "표/그림 설명"),
        ("reviewers", "리뷰어 시뮬레이션"),
        ("priorities", "수정 우선순위"),
    ]
)

SYSTEM_PROMPT = """
당신은 기술경영 분야 KCI 학술지의 엄격하지만 건설적인 심사자이자 지도교수다.
이미 작성된 논문을 비판적으로 점검하되, 없는 사실·인용·통계 결과를 만들어내지 않는다.
논문에 근거가 없으면 '본문에서 확인되지 않음'이라고 명시한다.
응답은 반드시 유효한 JSON 객체 하나로 작성하고 코드 블록은 사용하지 않는다.
공통 JSON 키:
- summary: 한국어 종합 평가 문자열
- markdown: 화면과 보고서에 넣을 완결된 Markdown 문자열
- issues: 수정 이슈 배열
각 issues 원소는 section, issue_type, severity, problem, recommendation,
suggested_revision, priority 키를 가진다.
severity는 Major/Moderate/Minor 중 하나, priority는 1/2/3 중 하나다.
"""

TASK_PROMPTS = {
    "structure": """
구조 정합성을 점검하라. 제목-초록-서론-연구질문-방법-결과-논의-결론의 일관성,
문제제기와 연구질문의 연결, 결과의 연구질문 응답 여부, 논의의 해석 수준,
결론의 기여와 한계 균형을 평가한다.
markdown에는 종합 평가, Major/Moderate/Minor 문제, 수정 방향, 수정 예시 문장을 포함한다.
""",
    "theory": """
이론적 기여를 점검하라. 단순 방법론 조합 여부, 새로운 구성개념의 명확성,
기존 연구 한계와 차별성, 개념 혼용, 국내 KCI 맥락의 기여를 평가한다.
markdown은 '점검 항목|현재 상태|문제점|수정 방향|보강 문장 예시' 열의 표를 포함한다.
""",
    "methodology": """
방법론 방어 가능성을 점검하라. 데이터 출처, 기간과 대상, 방법 선택 이유,
해석의 과장, 강건성·보완 분석 필요성을 평가한다. 피인용, 특허, 토픽모델링,
네트워크 분석, 머신러닝 결과를 인과적으로 과장하지 않았는지도 본다.
markdown에는 강점, 약점, 예상 심사 지적, 방어 논리, 보강 문장 예시를 포함한다.
""",
    "reviewers": """
세 명의 리뷰어를 시뮬레이션하라.
Reviewer A는 이론적 기여·학술적 중요성·차별성,
Reviewer B는 방법론·데이터·결과 해석·강건성,
Reviewer C는 구성·용어 일관성·표그림·KCI 적합성을 중점 평가한다.
markdown에는 Accept/Minor Revision/Major Revision/Reject 중 게재 가능성,
A/B/C 심사평, Major Revision, Minor Revision, 제출 전 Top 5를 포함한다.
""",
    "priorities": """
논문의 수정 우선순위를 제안하라. 영향이 큰 근본 문제를 먼저 배치하고,
issues 배열을 최소 5개, 최대 15개로 작성한다. 중복 이슈는 합친다.
markdown에는 우선순위 1부터 정렬한 표와 최우선 조치 설명을 포함한다.
""",
}


def _section_context(sections: dict[str, str], limit: int = 55_000) -> str:
    chunks = []
    used = 0
    for name, text in sections.items():
        if not text.strip():
            continue
        chunk = f"\n## {name}\n{text.strip()}\n"
        remaining = limit - used
        if remaining <= 0:
            break
        chunks.append(chunk[:remaining])
        used += len(chunks[-1])
    return "".join(chunks)


def _normalize_issues(
    issues: Any, file_name: str, default_type: str
) -> list[dict[str, Any]]:
    normalized = []
    if not isinstance(issues, list):
        return normalized
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        severity = str(issue.get("severity", "Moderate")).title()
        if severity not in {"Major", "Moderate", "Minor"}:
            severity = "Moderate"
        try:
            priority = int(issue.get("priority", 2))
        except (TypeError, ValueError):
            priority = 2
        normalized.append(
            {
                "file_name": file_name,
                "section": str(issue.get("section", "전체")),
                "issue_type": str(issue.get("issue_type", default_type)),
                "severity": severity,
                "problem": str(issue.get("problem", "")),
                "recommendation": str(issue.get("recommendation", "")),
                "suggested_revision": str(issue.get("suggested_revision", "")),
                "priority": min(3, max(1, priority)),
            }
        )
    return normalized


def _table_figure_result(
    findings: list[dict[str, Any]], file_name: str
) -> dict[str, Any]:
    lines = [
        "| 표/그림 번호 | 현재 문제 | 수정 필요 여부 | 추가 설명 문장 예시 |",
        "|---|---|---|---|",
    ]
    issues = []
    for finding in findings:
        lines.append(
            f"| {finding['item']} | {finding['problem']} | "
            f"{'필요' if finding['needs_revision'] else '아니오'} | "
            f"{finding['suggested_sentence']} |"
        )
        if finding["needs_revision"]:
            issues.append(
                {
                    "file_name": file_name,
                    "section": "표/그림",
                    "issue_type": "표/그림 설명",
                    "severity": "Moderate",
                    "problem": finding["problem"],
                    "recommendation": "본문에서 제시 목적, 핵심 수치, 연구질문과의 연결을 설명한다.",
                    "suggested_revision": finding["suggested_sentence"],
                    "priority": 2,
                }
            )
    return {
        "summary": "DOCX 개체와 본문 호출 패턴을 기준으로 표·그림 설명을 점검했습니다.",
        "markdown": "\n".join(lines),
        "issues": issues,
    }


def run_selected_analyses(
    client: LLMClient,
    file_name: str,
    sections: dict[str, str],
    full_text: str,
    selected_keys: list[str],
    table_figure_findings: list[dict[str, Any]],
) -> dict[str, Any]:
    context = _section_context(sections)
    if not context:
        context = full_text[:55_000]

    analyses: OrderedDict[str, dict[str, Any]] = OrderedDict()
    all_issues: list[dict[str, Any]] = []

    for key in ANALYSIS_OPTIONS:
        if key not in selected_keys:
            continue
        if key == "tables_figures":
            result = _table_figure_result(table_figure_findings, file_name)
        else:
            result = client.request_json(
                SYSTEM_PROMPT,
                f"""
분석 대상 파일: {file_name}
분석 과업:
{TASK_PROMPTS[key]}

논문 본문:
{context}
""",
            )
            result["issues"] = _normalize_issues(
                result.get("issues"), file_name, ANALYSIS_OPTIONS[key]
            )
        result.setdefault("summary", "")
        result.setdefault("markdown", result["summary"])
        result.setdefault("issues", [])
        analyses[key] = result
        all_issues.extend(result["issues"])

    severity_rank = {"Major": 0, "Moderate": 1, "Minor": 2}
    all_issues.sort(
        key=lambda row: (row["priority"], severity_rank.get(row["severity"], 9))
    )

    summaries = "\n".join(
        f"- {ANALYSIS_OPTIONS[key]}: {value.get('summary', '')}"
        for key, value in analyses.items()
    )
    overall_assessment = (
        "선택한 분석 결과를 종합하면 다음과 같습니다.\n\n"
        f"{summaries}\n\n"
        "우선순위표의 Major 이슈부터 수정하고, 수정 후 연구질문-결과-논의의 "
        "연결을 다시 확인하는 것을 권장합니다."
    )

    return {
        "analyses": analyses,
        "issues": all_issues,
        "overall_assessment": overall_assessment,
        "debug": json.dumps({"selected": selected_keys}, ensure_ascii=False),
    }
