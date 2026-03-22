# StockBlog AI — Backend

Python/FastAPI 기반 백엔드 서버입니다. Playwright를 사용하여 ChatGPT newstock GPT에 자동 질의하고, 응답을 블로그 형태로 변환합니다.

## 🚀 실행 방법

### 1. Python 환경 준비

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

### 2. Playwright 브라우저 설치

```bash
playwright install chromium
```

### 3. 환경변수 설정

```bash
copy .env.example .env
# .env 파일을 열어서 필요한 값 수정
```

### 4. 최초 로그인 세션 준비 (중요!)

자동화 전용 프로필에서 ChatGPT에 한 번 수동 로그인해야 합니다:

```bash
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context('./playwright-session', headless=False)
    page = ctx.new_page()
    page.goto('https://chatgpt.com/')
    input('브라우저에서 ChatGPT에 로그인한 후 Enter를 누르세요...')
    ctx.close()
"
```

위 명령을 실행하면 브라우저가 열립니다:
1. `https://chatgpt.com/`에 접속
2. 구글 계정 등으로 로그인
3. 로그인 완료 확인 후 터미널에서 Enter
4. 세션이 `playwright-session/` 폴더에 저장됩니다

> 이후부터는 이 세션이 자동으로 재사용됩니다.

### 5. 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. API 확인

- Health: `http://localhost:8000/api/health`
- Docs (Swagger): `http://localhost:8000/docs`
- 세션 확인: `http://localhost:8000/api/stock/check-session`

## 🧪 테스트 실행

```bash
python -m pytest tests/ -v
```

## 📂 프로젝트 구조

```
backend/
  app/
    main.py                  # FastAPI 앱
    api/routes/stock.py      # API 라우트
    services/
      stocktitan_scraper_service.py   # StockTitan 스크래핑
      chatgpt_browser_service.py      # ChatGPT 자동화
      blog_writer_service.py          # 블로그 변환
    schemas/stock.py         # Pydantic 모델
    core/
      config.py              # 환경설정 + 셀렉터
      logger.py              # SSE 로그 매니저
    utils/
      wait_helpers.py        # 딜레이/대기 유틸
      parser.py              # 파싱 유틸
  tests/                     # 테스트 코드
  requirements.txt
  .env.example
```

## 🔧 세션이 끊겼을 때

1. `playwright-session/` 폴더를 삭제합니다
2. 위의 "최초 로그인 세션 준비" 과정을 다시 수행합니다
3. 서버를 재시작합니다

## ❗ 자주 나는 에러

| 에러 | 원인 | 해결법 |
|------|------|--------|
| `login_required` | ChatGPT 세션 만료 | 로그인 세션 재준비 |
| `newstock_not_found` | newstock GPT 접근 불가 | ChatGPT에서 newstock GPT가 활성화되어 있는지 확인 |
| `connection_failed` | ChatGPT 접속 불가 | 네트워크 확인, VPN 등 점검 |
| `textarea_not_found` | 입력창 로드 안 됨 | 페이지 로드 지연, 재시도 |
| `response_timeout` | 응답 생성 시간 초과 | REQUEST_TIMEOUT 값 증가 |
| `empty_response` | 응답 비어있음 | ChatGPT 상태 확인, 재시도 |
