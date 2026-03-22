# Economy Blog Platform

주간 이슈 수집 → 키워드 랭킹 → 블로그 초안 생성 플랫폼

## 기술 스택

- **Backend**: FastAPI + SQLAlchemy (async) + MySQL
- **Frontend**: React + Vite
- **AI**: OpenAI Responses API (Structured Output)

## 실행 방법

### 1. MySQL DB 초기화

HeidiSQL 또는 터미널에서 `init_db.sql` 실행:

```sql
source init_db.sql;
```

### 2. 환경변수 설정

루트에 `.env` 파일을 생성합니다 (`.env.example` 참고):

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=yourpassword
DB_NAME=economy_blog
OPENAI_API_KEY=sk-...
```

### 3. 백엔드 실행

```bash
cd backend
.\.venv\Scripts\Activate.ps1    # Windows
uvicorn app.main:app --reload --port 8000
```

### 4. 프론트엔드 실행

```bash
cd frontend
npm run dev
```

### 5. 접속

- 프론트엔드: http://localhost:3000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/api/health

## 사용 흐름

1. **대시보드** → "이번 주 이슈 수집" 버튼 클릭
2. 시스템이 자동으로 뉴스 수집 → 키워드 추출 → 점수화 → 랭킹
3. 상위 10개 **키워드 카드** 확인
4. 카드 클릭 → **네이버형 / 티스토리형** 블로그 초안 생성
5. 복사 버튼으로 내용 가져가기
6. **저장된 초안** 페이지에서 과거 주차/키워드 조회

## 폴더 구조

```
economy_blog/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 진입점
│   │   ├── config.py         # 환경변수
│   │   ├── database.py       # DB 연결
│   │   ├── models/           # SQLAlchemy 모델 (6개)
│   │   ├── schemas/          # Pydantic 스키마
│   │   ├── routers/          # API 라우터 (4개)
│   │   ├── services/         # 비즈니스 로직 (5개)
│   │   ├── prompts/          # OpenAI 프롬프트
│   │   └── utils/            # 유틸리티
│   ├── requirements.txt
│   └── .venv/
├── frontend/
│   ├── src/
│   │   ├── pages/            # 4개 페이지
│   │   ├── components/       # 공용 컴포넌트
│   │   └── api/              # axios 클라이언트
│   └── package.json
├── init_db.sql               # MySQL DDL
├── .env.example
└── README.md
```
