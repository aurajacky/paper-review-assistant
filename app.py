from __future__ import annotations

import hashlib
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from src.docx_loader import DocumentLoadError, load_docx
from src.exporter import ExportError, export_results
from src.llm_client import LLMClient, LLMError
from src.reviewers import ANALYSIS_OPTIONS, run_selected_analyses
from src.section_parser import parse_sections
from src.table_figure_checker import inspect_tables_and_figures


load_dotenv()

st.set_page_config(
    page_title="KCI 논문 초안 점검 시스템",
    page_icon="📝",
    layout="wide",
)

st.title("KCI 논문 초안 점검 시스템")
st.caption(
    "이미 작성된 DOCX 논문을 KCI 심사자와 지도교수 관점에서 점검하고 "
    "수정 보고서와 우선순위표를 생성합니다."
)


def reset_result_state(file_hash: str) -> None:
    if st.session_state.get("uploaded_file_hash") != file_hash:
        st.session_state.uploaded_file_hash = file_hash
        st.session_state.analysis_results = None
        st.session_state.exported_files = None


with st.sidebar:
    st.header("분석 설정")
    env_key = os.getenv("OPENAI_API_KEY", "")
    api_key = st.text_input(
        "OpenAI API Key",
        value=env_key,
        type="password",
        help=".env의 OPENAI_API_KEY를 사용하거나 이곳에 직접 입력하세요.",
    )
    model = st.selectbox(
        "모델",
        ["gpt-4.1-mini", "gpt-4o-mini"],
        index=0,
    )
    st.subheader("분석 항목")
    selected_keys = [
        key
        for key, label in ANALYSIS_OPTIONS.items()
        if st.checkbox(label, value=True, key=f"analysis_{key}")
    ]
    st.info("API Key는 분석 요청에만 사용되며 앱이 별도로 저장하지 않습니다.")


uploaded_file = st.file_uploader(
    "점검할 논문 초안 한 개를 업로드하세요.",
    type=["docx"],
    accept_multiple_files=False,
)

if uploaded_file is None:
    st.info("DOCX 파일을 업로드하면 섹션을 감지하고 점검을 시작할 수 있습니다.")
    st.stop()

file_bytes = uploaded_file.getvalue()
file_hash = hashlib.sha256(file_bytes).hexdigest()
reset_result_state(file_hash)
st.success(f"업로드 파일: {uploaded_file.name}")

try:
    document_data = load_docx(file_bytes, uploaded_file.name)
    sections = parse_sections(document_data.paragraphs)
    figure_table_findings = inspect_tables_and_figures(document_data)
except DocumentLoadError as exc:
    st.error(f"DOCX 파일을 읽지 못했습니다: {exc}")
    st.stop()
except Exception as exc:
    st.error(f"문서 처리 중 예상하지 못한 오류가 발생했습니다: {exc}")
    st.stop()

detected = [name for name, text in sections.items() if text.strip()]
st.subheader("감지된 섹션")
if detected:
    st.write(" · ".join(detected))
else:
    st.warning("표준 섹션 제목을 감지하지 못했습니다. 전체 본문 기준으로 분석합니다.")

with st.expander("추출 결과 미리보기"):
    st.write(f"본문 문단: {len(document_data.paragraphs)}개")
    st.write(f"문서 표: {document_data.table_count}개")
    st.write(f"인라인 그림: {document_data.inline_shape_count}개")
    st.text(document_data.full_text[:3000] or "(추출된 본문 없음)")

if not selected_keys:
    st.warning("사이드바에서 분석 항목을 하나 이상 선택하세요.")

run_clicked = st.button(
    "점검 실행",
    type="primary",
    disabled=not selected_keys,
    use_container_width=True,
)

if run_clicked:
    if not api_key.strip():
        st.error("OpenAI API Key가 필요합니다. 사이드바 또는 .env 파일에 입력하세요.")
    elif not document_data.full_text.strip():
        st.error("분석할 텍스트를 추출하지 못했습니다. DOCX 내용을 확인하세요.")
    else:
        try:
            with st.spinner("논문을 점검하고 보고서를 생성하고 있습니다..."):
                client = LLMClient(api_key=api_key.strip(), model=model)
                results = run_selected_analyses(
                    client=client,
                    file_name=uploaded_file.name,
                    sections=sections,
                    full_text=document_data.full_text,
                    selected_keys=selected_keys,
                    table_figure_findings=figure_table_findings,
                )
                exported = export_results(
                    file_name=uploaded_file.name,
                    detected_sections=detected,
                    results=results,
                    output_root=Path("outputs"),
                )
                st.session_state.analysis_results = results
                st.session_state.exported_files = exported
        except LLMError as exc:
            st.error(f"OpenAI API 호출에 실패했습니다: {exc}")
        except ExportError as exc:
            st.error(f"결과 파일 저장에 실패했습니다: {exc}")
        except Exception as exc:
            st.error(f"점검 실행 중 예상하지 못한 오류가 발생했습니다: {exc}")

results = st.session_state.get("analysis_results")
exported = st.session_state.get("exported_files")

if results:
    st.divider()
    st.subheader("점검 결과")
    visible_keys = [key for key in ANALYSIS_OPTIONS if key in results["analyses"]]
    tabs = st.tabs([ANALYSIS_OPTIONS[key] for key in visible_keys])
    for tab, key in zip(tabs, visible_keys):
        with tab:
            analysis = results["analyses"][key]
            st.markdown(analysis.get("markdown") or analysis.get("summary", "결과 없음"))

    st.subheader("종합 평가")
    st.markdown(results.get("overall_assessment", "종합 평가가 생성되지 않았습니다."))

if exported:
    st.subheader("결과 다운로드")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "review_report.docx 다운로드",
            data=exported.report_bytes,
            file_name=exported.report_path.name,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )
        st.caption(f"자동 저장: {exported.report_path}")
    with col2:
        st.download_button(
            "revision_plan.xlsx 다운로드",
            data=exported.plan_bytes,
            file_name=exported.plan_path.name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
        st.caption(f"자동 저장: {exported.plan_path}")
