# KCI 논문 초안 점검 시스템

이미 작성된 학술논문 초안(`.docx`)을 업로드하면 기술경영/KCI 학술지 심사자와
지도교수 관점에서 구조, 이론적 기여, 방법론, 표·그림 설명 등을 점검하고
수정 보고서를 생성하는 Streamlit 앱입니다.

이 프로젝트는 논문을 새로 자동 작성하는 도구가 아닙니다. 기존 초안의 문제를
발견하고 수정 우선순위를 정하는 보조 도구입니다.

## 주요 기능

- DOCX 논문 한 개 업로드 및 본문·표 텍스트 추출
- 초록, 서론, 선행연구/이론적 배경, 연구방법, 분석결과, 논의, 결론, 참고문헌 자동 분리
- 구조 정합성, 이론적 기여, 방법론 방어 가능성 점검
- 본문의 `표 1`, `<그림 1>`, `Table 1`, `Figure 1` 호출과 인접 설명 탐지
- 이론/방법/구성 관점의 Reviewer A/B/C 심사 시뮬레이션
- Major/Moderate/Minor 이슈와 1~3순위 수정 계획 생성
- 화면 결과 확인 및 DOCX/XLSX 다운로드
- 원본 파일명과 실행 시각을 붙여 `outputs/`에 자동 저장

## 프로젝트 구조

```text
paper-review-assistant/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .env.example
├─ src/
│  ├─ __init__.py
│  ├─ docx_loader.py
│  ├─ section_parser.py
│  ├─ llm_client.py
│  ├─ reviewers.py
│  ├─ table_figure_checker.py
│  └─ exporter.py
├─ outputs/
│  ├─ review_reports/
│  └─ tables/
└─ samples/
```

## Windows에서 실행하기

### 1. Python 설치

Python 3.10 이상을 [python.org](https://www.python.org/downloads/)에서 설치합니다.
설치 화면에서 **Add Python to PATH**를 선택하세요.

### 2. GitHub ZIP 다운로드

1. GitHub 저장소 화면에서 **Code → Download ZIP**을 선택합니다.
2. ZIP 압축을 원하는 폴더에 풉니다.
3. 압축을 푼 `paper-review-assistant` 폴더를 엽니다.
4. 탐색기 주소창에 `powershell`을 입력하고 Enter를 누릅니다.

Git을 사용하는 경우 다음과 같이 clone해도 됩니다.

```powershell
git clone https://github.com/aurajacky/paper-review-assistant.git
cd paper-review-assistant
```

### 3. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

명령 프롬프트(cmd)를 사용한다면:

```bat
.venv\Scripts\activate.bat
```

### 4. 패키지 설치

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 앱 실행

```powershell
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 터미널에 표시된 `http://localhost:8501` 주소를
브라우저에 입력합니다.

## OpenAI API Key 입력

가장 간단한 방법은 앱 왼쪽 사이드바의 **OpenAI API Key** 입력창에 키를 넣는 것입니다.
키가 없으면 앱 초기 화면과 문서 미리보기는 작동하지만 점검 실행은 하지 않습니다.

`.env` 파일을 사용하려면 `.env.example`을 `.env`로 복사한 뒤 값을 입력합니다.

```env
OPENAI_API_KEY=sk-여기에_본인의_API_Key
```

`.env`는 `.gitignore`에 포함되어 있으므로 GitHub에 올리지 마세요.

## 사용 방법

1. 왼쪽 사이드바에서 API Key와 모델을 확인합니다.
2. 필요한 분석 항목을 선택합니다.
3. 메인 화면에서 DOCX 논문 한 개를 업로드합니다.
4. 감지된 섹션과 텍스트 미리보기를 확인합니다.
5. **점검 실행**을 누릅니다.
6. 결과 탭을 검토합니다.
7. `review_report.docx`와 `revision_plan.xlsx`를 다운로드합니다.

여러 논문은 동시에 올리지 않고 하나씩 반복 검토합니다. 첫 논문의 결과를 다운로드한
뒤 두 번째 파일을 업로드하면 앱이 이전 세션 결과를 초기화합니다. 저장 파일에는
원본 파일명과 timestamp가 붙으므로 서로 덮어쓰지 않습니다.

## 결과 저장 위치

```text
outputs/review_reports/{원본파일명}_{timestamp}_review_report.docx
outputs/tables/{원본파일명}_{timestamp}_revision_plan.xlsx
```

예:

```text
outputs/review_reports/draft_20260620_153000_review_report.docx
outputs/tables/draft_20260620_153000_revision_plan.xlsx
```

앱 화면의 다운로드 버튼으로도 같은 파일을 받을 수 있습니다.

## 자주 발생하는 오류와 해결 방법

### Python이 설치되어 있지 않음

`python` 명령을 찾을 수 없다는 메시지가 나오면 Python을 설치하고 터미널을 새로
여세요. 설치 시 **Add Python to PATH**를 선택했는지 확인합니다.

### `pip install` 실패

먼저 다음을 실행한 뒤 다시 설치합니다.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

회사·학교 네트워크의 프록시나 보안 정책 때문에 실패할 수 있습니다. 다른 네트워크를
사용하거나 네트워크 관리자에게 PyPI 접근 가능 여부를 문의하세요.

### OpenAI API Key 오류

- 키 앞뒤에 공백이 없는지 확인합니다.
- OpenAI API 결제 및 사용 한도를 확인합니다.
- ChatGPT 구독과 OpenAI API 사용 요금은 별도일 수 있습니다.
- `.env`를 수정했다면 Streamlit을 종료한 뒤 다시 실행합니다.

### DOCX 파일 파싱 실패

- 파일 확장자만 `.docx`로 바꾼 문서가 아닌지 확인합니다.
- 암호화 또는 손상된 문서는 Word에서 새 DOCX로 다시 저장합니다.
- 구형 `.doc` 파일은 Word에서 `.docx`로 변환합니다.

### Streamlit 실행 오류

가상환경이 활성화되어 있는지 확인하고 다음 방식으로 실행해 보세요.

```powershell
python -m streamlit run app.py
```

포트 충돌 시:

```powershell
streamlit run app.py --server.port 8502
```

### Windows PowerShell 실행 정책 문제

`Activate.ps1` 실행이 차단되면 현재 사용자 범위에서 다음을 실행합니다.

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

정책 변경이 허용되지 않는 PC에서는 명령 프롬프트를 열고
`.venv\Scripts\activate.bat`를 사용하거나, 가상환경의 Python을 직접 실행합니다.

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## 분석 한계

- 섹션 제목이 비표준적이면 자동 분리 정확도가 낮아질 수 있습니다.
- 복잡한 텍스트 상자, 각주, 수식, 이미지 속 글자는 완전히 추출되지 않을 수 있습니다.
- 표·그림 점검은 DOCX 개체 수와 본문 호출 패턴을 활용한 규칙 기반 점검입니다.
- AI 결과는 심사 결과를 보장하지 않으며, 인용·통계·사실은 연구자가 다시 검증해야 합니다.
- 긴 논문은 API 입력 한도를 고려해 앞부분부터 일정 길이까지만 분석될 수 있습니다.
