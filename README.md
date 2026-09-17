# 내 데이터를 아는 AI 비서 (Data-Aware AI Assistant)

## 서비스 소개

일반적인 챗봇은 "이번 달 실적이 어때?" 같은 질문에 개인화된 답을 하지 못합니다.
이 서비스는 사용자가 등록한 시계열 데이터(매출/실적 등)를 분석해 요약 정보를 만들고,
그 요약을 GPT의 시스템 프롬프트에 주입(context injection)하여 **내 데이터를 아는 AI 비서**와 대화할 수 있게 합니다.

- 사용자가 (날짜, 값, 메모) 형태로 데이터를 등록/수정/삭제
- 백엔드가 데이터를 분석해 기간/통계/트렌드 요약 생성
- AI 채팅 시 요약을 시스템 프롬프트에 삽입해 맞춤형 답변 제공
- 모든 대화는 자동 저장되며, 목록에서 다시 불러올 수 있음

## 기술 스택

- **백엔드**: FastAPI, Pydantic, firebase-admin(Firestore), openai
- **프론트엔드**: HTML / CSS / Vanilla JavaScript (프레임워크 미사용)
- **DB**: Firebase Firestore
- **AI**: OpenAI Chat Completions API
- **배포**: 백엔드 - Render / 프론트엔드 - Vercel

## 배포 URL

| 항목 | URL |
| --- | --- |
| 프론트엔드 | _배포 후 작성_ |
| 백엔드 API | _배포 후 작성_ |
| Swagger UI | `<백엔드 URL>/docs` |

> ⚠️ Render 무료 티어는 일정 시간 요청이 없으면 슬립 상태가 되어, 첫 요청 시 최대 수십 초의 지연(콜드 스타트)이 발생할 수 있습니다. 프론트엔드 채팅 로딩 표시가 이 지연 동안 노출됩니다.

## 로컬 실행 방법

### 백엔드

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # 값 채우기
uvicorn app.main:app --reload
```

- Swagger UI: http://localhost:8000/docs
- (선택) 샘플 데이터 100개 이상 생성 후 Firestore에 저장:
  ```bash
  python seed_data.py            # Firestore에 저장 (환경변수 필요)
  python seed_data.py --dry-run  # 키 없이 JSON 파일로만 확인
  ```

### 프론트엔드

`frontend/js/config.js`에서 로컬 실행 시 자동으로 `http://localhost:8000`을 바라보도록 되어 있습니다.
정적 파일이므로 아무 로컬 서버로 열면 됩니다. 예:

```bash
cd frontend
python3 -m http.server 5500
# http://localhost:5500 접속
```

## 환경 변수 (최소 세트)

### 백엔드 (Render)

| 변수 | 설명 |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `OPENAI_MODEL` | 사용할 모델 (기본 `gpt-4o-mini`) |
| `CHAT_MAX_TOKENS` | 응답 최대 토큰 수 (기본 500, 비용 제어용) |
| `FIREBASE_SERVICE_ACCOUNT_JSON` | Firebase 서비스 계정 키 JSON 전체를 한 줄 문자열로 |
| `ALLOWED_ORIGINS` | CORS 허용 도메인 (콤마 구분, 예: `https://your-app.vercel.app`) |

### 프론트엔드 (Vercel)

| 변수 | 설명 |
| --- | --- |
| `API_BASE_URL` | 백엔드(Render) 배포 URL. 빌드 시 `scripts/generate-config.js`가 이 값을 읽어 `js/config.js`를 생성합니다. |

## 배포 방법 요약

### 백엔드 → Render

1. GitHub에 푸시
2. Render에서 New Web Service 생성, 이 저장소 연결
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   (또는 저장소 루트의 `render.yaml`을 Blueprint로 사용)
5. 환경 변수 등록 후 배포, `<URL>/docs`에서 Swagger 확인

### 프론트엔드 → Vercel

1. Vercel에서 이 저장소 Import, Root Directory를 `frontend`로 지정
2. Build Command: `node scripts/generate-config.js` (이미 `vercel.json`에 설정됨)
3. 환경 변수 `API_BASE_URL`에 Render 백엔드 URL 등록
4. 배포

## API 엔드포인트 요약

### 데이터 (`/api/data`)

- `POST /api/data` — 데이터 추가
- `GET /api/data` — 목록 조회
- `PUT /api/data/{id}` — 수정
- `DELETE /api/data/{id}` — 삭제
- `GET /api/data/summary` — 요약(기간/개수/통계/트렌드) — 챗봇 프롬프트 주입에 사용

### 대화 기록 (`/api/conversations`)

- `POST /api/conversations` — 대화 저장
- `GET /api/conversations` — 목록 조회 (메시지 본문 제외, 요약 정보만: id/title/message_count/created_at/updated_at)
- `GET /api/conversations/{id}` — 특정 대화의 전체 메시지 조회 ("불러오기"에 사용)
- `DELETE /api/conversations/{id}` — 삭제

### 채팅 (`/api/chat`)

- `POST /api/chat` — 데이터 요약 조회 → 시스템 프롬프트 주입 → GPT 호출 → 대화 자동 저장 → 응답 반환

## 컨텍스트 주입 흐름

```
사용자 메시지
   │
   ▼
GET /api/data/summary  ──► 기간/개수/통계/트렌드 요약
   │
   ▼
시스템 프롬프트 생성 (요약 삽입)
   │
   ▼
OpenAI Chat Completions 호출 (system + 이전 대화 히스토리 + 사용자 메시지)
   │
   ▼
응답을 conversations 컬렉션에 자동 저장 (user/assistant 메시지 append)
```

## Firestore 컬렉션 구조

- `data`: `{ date: string(YYYY-MM-DD), value: number, memo: string | null }`
- `conversations`: `{ title: string, messages: [{role, content}], created_at, updated_at }`

## 제출 스크린샷

_아래 위치에 스크린샷을 추가하세요._

- 데이터 요약이 보이는 채팅 화면 (질문+답변 포함): `docs/screenshot-chat.png`
- 데이터 관리 화면 (CRUD 동작): `docs/screenshot-data.png`
- 대화 기록 화면 (불러오기 동작): `docs/screenshot-history.png`

## 보너스로 구현한 항목

- 프론트엔드 시각화: 데이터 관리 탭의 추세 라인 차트 (Canvas, 라이브러리 미사용)
- 데이터 내보내기: CSV / JSON 다운로드 버튼
- 다크 모드 토글 (localStorage에 사용자 선택 저장)
