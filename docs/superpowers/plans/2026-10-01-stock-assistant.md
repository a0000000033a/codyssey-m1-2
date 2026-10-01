# 국내 주식 AI 분석 비서 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 국내 관심 종목의 저장된 시장 데이터와 개인 기록으로 답하고, 한 종목의 여러 대화를 관리하는 개인용 서비스를 완성합니다.

**Architecture:** FastAPI 라우터는 검증·인증 후 서비스를 호출하고, 서비스는 저장소와 외부 데이터/AI 어댑터를 사용합니다. 요약은 외부 연결 없이 계산하며, 바닐라 프론트는 인증된 API로만 개인 데이터를 다룹니다. 배포는 Render와 Vercel을 사용합니다.

**Tech Stack:** Python 3.10+, FastAPI, uvicorn, Pydantic, firebase-admin, openai, python-dotenv, FinanceDataReader(실데이터 검증 후보), pytest, HTML/CSS/JavaScript, Firebase Authentication/Firestore.

**Spec:** `docs/superpowers/specs/2026-10-01-stock-assistant-design.md`

## Global Constraints

- 국내 범위는 코스피·코스닥 상장 주식입니다. ETF·ETN·코넥스는 첫 버전 검색 대상에서 제외합니다.
- 최근 1년의 일별 데이터를 기본 분석 범위로 사용합니다.
- 한 대화는 한 종목에 연결합니다. 종목별 대화 개수에 제한을 두지 않습니다.
- 시장 가격과 사용자 관심 가격은 별개 데이터입니다.
- 본인 허용 UID 한 개만 접근하며, 클라이언트의 owner UID를 신뢰하지 않습니다.
- 메모 최대 1,000자, 질문 최대 2,000자, 수동 저장 최대 100개 메시지와 메시지별 8,000자입니다.
- AI에는 최근 대화 최대 12개 메시지와 최근 개인 기록 20개를 전달합니다.
- 백엔드는 Render, 프론트엔드는 Vercel에 배포합니다.
- 표시 문구는 한국어 `~합니다/~습니다/~입니다`로 통일합니다.
- 비밀 값은 채팅·Git·프론트 설정·로그에 노출하지 않습니다.
- 선택 보너스는 이번 계획에 포함하지 않습니다. 외부 테스트를 대체 객체 테스트와 구분합니다.

## Review Focus

1. 서로 다른 종목으로 빠르게 전환해도 늦게 도착한 응답이 새 종목의 화면에 표시되지 않아야 합니다(Task 6).
2. 거래량이 0인 날은 유지하고 NaN/무한대/중복 날짜와 조회 실패는 정확히 구분해야 합니다(Task 2).
3. 표본 0개·39개·100개 미만과 추세 ±1% 경계에서 잘못된 통계·확신을 제공하지 않아야 합니다(Task 3).
4. 전송 timeout·동시 질문·삭제와 전송 경합에서 중복 메시지나 삭제된 대화 부활이 없어야 합니다(Task 4/5).
5. 만료 토큰·권한 없는 ID·잘못된 cursor·메모의 HTML/지시문은 인증 우회나 실행으로 이어지지 않아야 합니다(Task 1/3/5/6).

## 파일 경계와 실행 원칙

`backend/app/core/`는 설정·인증·예외·의존성 조립, `schemas/`는 검증 모델, `providers/`는 외부 연결, `repositories/`는 Firestore, `services/`는 업무 흐름, `routers/`는 HTTP 계약을 맡습니다. `frontend/js/`는 인증·통신·상태·화면을 나눕니다. Python 디렉터리는 패키지로 생성합니다.

실행 시 using-git-worktrees를 적용해 `codex/stock-assistant` 개발 브랜치를 분리합니다. 각 기능은 실패 테스트 → 실패 확인 → 최소 구현 → 성공 확인 → 변경 검토 → 커밋 순서로 진행합니다. 아래 명령은 레포 루트에서 `backend/.venv/bin/python`을 사용합니다. Git stage는 해당 Task 파일만 명시합니다. 완료한 체크박스는 실제 확인 뒤 갱신합니다.

## Task 1: 인증된 API와 실행 환경

**Files:** Create `backend/requirements.txt`, `backend/requirements-dev.txt`, `backend/pyproject.toml`, `backend/.env.example`, `backend/app/main.py`, `backend/app/core/{config,auth,errors,dependencies}.py`, `backend/app/schemas/common.py`, `backend/tests/{conftest,test_auth}.py`.

**Interfaces:** `Settings`는 spec의 서버 환경 변수와 `OPENAI_TIMEOUT_SECONDS=45`, `CHAT_LOCK_SECONDS=90`, `CHAT_INPUT_MAX_CHARS=24000`을 읽습니다. `require_owner(credentials) -> str`는 허용 UID를 반환합니다. `create_app(settings, dependencies) -> FastAPI`는 테스트에서 외부 연결을 대체할 수 있게 합니다. `Page[T]`는 `items`, `next_cursor`를, `ApiError`는 `code`, `message`를 정의합니다. 목록 기본 limit=30, 최대=100으로 고정합니다.

- [x] 인증·CORS 실패 테스트를 작성합니다: 토큰 없음/만료는 401, 다른 UID는 403, 허용 UID는 성공, `/docs`·`/health` 공개, 허용 origin preflight만 성공합니다. 필수 비밀 설정 누락은 안전하게 실패하며 응답·로그에 값이 없습니다.
- [x] Python 3.10 이상을 확인하고 `python3 -m venv backend/.venv`로 환경을 만든 뒤 개발 의존성을 설치합니다. `backend/.venv/bin/python -m pytest backend/tests/test_auth.py -q`를 실행해 미구현으로 실패하는지 확인합니다.
- [x] 설정, Firebase ID token 검증, 예외 응답, CORS, 공개 health, Swagger Bearer security를 구현합니다. 모듈 import 시 외부 네트워크 호출을 하지 않고 테스트에서는 검증기를 주입합니다. 최신 SDK 공식 문서에 맞춰 호환 버전을 선택·기록합니다.
- [x] 같은 명령이 성공하는지 확인하고 `backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --port 8000`으로 `/health`, `/docs`를 확인합니다. 실제 키 없이 health를 위한 테스트 구성과 배포 구성은 구분합니다.
- [x] 변경을 검토하고 `feat: add authenticated FastAPI foundation`으로 커밋합니다.

## Task 2: 국내 종목 수집·저장·관심 목록

**Files:** Create `backend/app/schemas/stocks.py`, `backend/app/providers/market.py`, `backend/app/repositories/{base,firestore}.py`, `backend/app/services/stocks.py`, `backend/app/routers/stocks.py`, `backend/tests/{fakes,test_stocks}.py`, `backend/scripts/verify_market.py`; Modify `backend/app/core/dependencies.py`, `backend/app/main.py`.

**Interfaces:** `Stock(market, symbol, name, exchange)`, `MarketPoint(date, close, volume, source, fetched_at)`. `MarketProvider.list_stocks() -> list[Stock]`, `history(symbol, start, end) -> list[MarketPoint]`. `StockService.search(q, cursor, limit) -> Page[Stock]`, `register(uid, symbol) -> WatchItem`, `refresh(symbol, force=False) -> SyncResult`. `FirestoreRepository`는 stocks/watchlist/market_data/sync_state를 담당하며 개인 작업에 uid를 필수로 받습니다.

- [x] 테스트를 작성합니다: 코스피·코스닥 일반 주식만 검색, 코드 앞자리 0 유지, 중복 등록 시 기존 항목 반환, 24시간 캐시 재사용, 오래된 데이터 재수집, 거래량 0 유지, NaN/무한대/음수 제외, 날짜 중복 제거, 수집 실패 시 기존 데이터 유지.
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_stocks.py -q`를 실행해 미구현으로 실패하는지 확인합니다.
- [x] FinanceDataReader의 현재 공식 API와 실제 데이터를 확인하고 명시적 출처와 가격 조정 정보를 기록합니다. 일반 주식 분류는 종목 메타데이터로 검증합니다. 데이터 수집이 불가능하면 실패 근거와 대안을 정리해 데이터 공급원 변경을 논의합니다.
- [x] 수집·Firestore 저장·검색·등록·삭제·갱신을 구현합니다. 날짜 순으로 upsert하며 batch당 최대 400건으로 나눕니다. cursor는 검색 조건과 연결하고 잘못된 cursor는 400을 반환합니다. 관심 종목 삭제 시 개인 기록·대화는 유지합니다. 종목 목록도 24시간 캐시하며 빈 결과와 조회 실패를 구분합니다.
- [x] 테스트 성공을 확인하고 `backend/.venv/bin/python backend/scripts/verify_market.py --symbol 005930`으로 최근 1년의 실제 데이터 100건 이상을 확인합니다. 기간·건수·제외 건수만 출력하며 원본 데이터는 커밋하지 않습니다.
- [x] 변경과 검증 결과를 검토하고 `feat: add domestic stock ingestion and watchlist`로 커밋합니다.

## Task 3: 개인 기록 CRUD와 데이터 요약

**Files:** Create `backend/app/schemas/data.py`, `backend/app/services/{data,summary}.py`, `backend/app/routers/data.py`, `backend/tests/{test_data,test_summary}.py`; Modify repository, dependencies, main.

**Interfaces:** `RecordInput(symbol, date, value, memo)`, `Record`는 id·owner_uid·timestamp를 추가합니다. `DataService.create(uid, payload) -> Record`, `list(uid, symbol, cursor, limit) -> Page[Record]`, `update(uid, id, payload) -> Record`, `delete(uid, id) -> None`. `calculate_summary(points: list[MarketPoint], records: list[Record], sync: SyncResult) -> Summary`는 순수 계산입니다. `SummaryService.get(uid, symbol) -> Summary`는 저장된 데이터를 읽습니다. 응답 키는 `market_data`, `personal_records`, `quality`입니다.

- [x] CRUD 테스트를 작성합니다: 미래 날짜(Asia/Seoul), 잘못된 코드, 비유한/0/음수 가격, 1,001자 메모는 422, 타인 ID는 404, 같은 날의 복수 기록과 페이지 조회는 성공합니다.
- [x] 요약 테스트를 작성합니다: 개인 가격을 시장 평균에 섞지 않습니다. 0건은 통계 null·판단 불가, 39건은 추세 판단 불가, 40건은 최근 20건과 직전 20건 평균을 비교합니다. 변화율 ±1%는 유지, 경계를 초과하면 상승/하락입니다. 100건 미만 경고, 최근 개인 기록 20개, 제외 건수를 확인합니다.

  대표 테스트 이름과 핵심 assertion: `test_personal_price_is_not_market_price`는 시장 종가 100·200과 개인 가격 999 입력에 대해 `assert result.market_data.average_close == 150`을 요구합니다. `test_trend_boundary_is_stable`은 이전 20개 100, 최근 20개 101인 입력에 대해 `assert result.market_data.trend.direction == "stable"`을 요구합니다. direction 값은 `up/down/stable/insufficient`로 고정하고 화면에서 한국어로 변환합니다.
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_data.py backend/tests/test_summary.py -q`로 실패를 확인합니다.
- [x] 필수 data 5개 API와 저장·계산을 구현합니다. `/summary`는 `/{id}`보다 먼저 등록합니다. 요약 조회는 stock service의 캐시 규칙으로 데이터를 확보하며, 동시 갱신은 중복을 방지합니다. 잘못된 cursor는 400을 반환합니다.
- [x] 테스트 성공과 Swagger의 5개 API 및 응답 모델을 확인합니다.
- [x] `feat: add personal records and stock summaries`로 커밋합니다.

## Task 4: 종목별 복수 대화와 복원·삭제

**Files:** Create `backend/app/schemas/conversations.py`, `backend/app/services/conversations.py`, `backend/app/routers/conversations.py`, `backend/tests/test_conversations.py`; Modify repository, dependencies, main.

**Interfaces:** `Message(role, content, turn_id, sequence, created_at, context_snapshot)`. `ConversationService.create(uid, symbol, messages) -> ConversationDetail`, `list(uid, symbol, cursor, limit) -> Page[ConversationMeta]`, `get(uid, id) -> ConversationDetail`, `delete(uid, id) -> None`. detail의 messages는 sequence 순서로 모두 반환하며 meta에는 본문을 포함하지 않습니다.

- [x] 같은 종목의 대화 2개가 다른 ID로 생성되고 각각의 메시지가 독립적으로 복원되는 테스트를 작성합니다. 타인 ID는 404, role=system과 101개 메시지/8,001자 본문은 422입니다.

  `test_two_conversations_for_same_symbol`의 핵심 assertion은 `assert first.id != second.id`와 `assert service.get(uid, first.id).messages[0].content == "첫 대화 질문"`입니다. 두 번째 대화에는 다른 본문을 저장해 서로의 내용을 복원하지 않는지 확인합니다.
- [x] 삭제 테스트에 하위 메시지 삭제, 중간 실패 후 재시도, 삭제 중 채팅 거부, 관심 목록 제거 후 대화 보존을 추가합니다.
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_conversations.py -q`로 실패를 확인합니다.
- [x] 필수 4개 API를 구현합니다. 빈 대화 저장을 허용하며 수동 저장은 부모와 최대 100개 메시지를 같은 batch로 만듭니다. 제목은 첫 질문 최대 40자이며 빈 대화는 `새 대화`입니다. 삭제 시 status=deleting을 기록하고 하위 메시지를 나눠 삭제한 뒤 부모를 삭제합니다.
- [x] 테스트 성공과 목록에 본문이 포함되지 않는 것을 확인합니다.
- [x] `feat: support multiple conversations per stock`로 커밋합니다.

## Task 5: 컨텍스트 기반 AI와 자동 저장

**Files:** Create `backend/app/schemas/chat.py`, `backend/app/providers/ai.py`, `backend/app/services/{context,chat}.py`, `backend/app/routers/chat.py`, `backend/tests/{test_context,test_chat}.py`; Modify repository, dependencies, main.

**Interfaces:** `ChatInput(symbol, message, conversation_id: str | None, request_id: UUID)`, `ChatResult(conversation_id, user_message, assistant_message, context)`. `build_context(summary: Summary, messages: list[Message], input_max_chars: int) -> ModelInput`, `AIProvider.answer(context: ModelInput) -> str`, `ChatService.send(uid, payload) -> ChatResult`. repository는 `acquire_turn(uid, payload, lease_seconds) -> TurnClaim`, `commit_turn(claim, user_message, assistant_message, context) -> ChatResult`를 제공합니다. 요청 ID의 고유 키는 uid를 포함하고, 대화 ID 없는 재시도도 최초 생성 대화에 연결합니다.

- [x] 컨텍스트 테스트를 작성합니다: 선택 종목·기간·기준일·표본 부족 안내, 최근 메시지 12개와 개인 기록 20개를 전달합니다. 메모 속 지시를 system 지침에 합치지 않고 데이터로 처리합니다. 입력 24,000자를 넘지 않도록 오래된 메시지와 긴 메모부터 줄이고 생략 여부를 기록합니다.
- [x] 채팅 테스트를 작성합니다: 종목 불일치 400, 타인 ID 404, 동시 질문 409, 성공 요청 재시도 시 AI 호출 총 1회, 다른 본문으로 같은 ID 사용 시 409, 만료 잠금 복구, 모델 timeout, 저장 실패, 삭제 중 거부. 대화 ID 없는 최초 질문도 같은 request ID 재시도에서 중복 대화·메시지를 만들지 않습니다.

  `test_successful_retry_does_not_call_model_twice`는 같은 payload를 2회 보내 `assert first.conversation_id == retry.conversation_id`, `assert ai.calls == 1`, `assert len(conversations.get(uid, first.conversation_id).messages) == 2`를 요구합니다.
- [x] `backend/.venv/bin/python -m pytest backend/tests/test_context.py backend/tests/test_chat.py -q`로 실패를 확인합니다.
- [x] 최신 OpenAI 공식 SDK 문서에 맞춰 어댑터를 구현합니다. 출력 기본 상한 800토큰, 호출 timeout 45초, SDK 자동 재시도 0회, 잠금 90초입니다. 모델 호출은 트랜잭션 밖에서 수행하고 저장 시 잠금 소유자와 대화 status를 재확인해 사용자/AI 메시지와 요약을 원자적으로 저장합니다. 호출 실패는 잠금을 풀고, 저장 결과 불명확 시 요청 ID의 기존 결과를 조회합니다.
- [x] 테스트 성공과 Swagger의 POST `/api/chat`을 확인합니다. 실제 GPT 호출은 Task 7에서 제한적으로 수행합니다.
- [x] `feat: add contextual AI chat with durable turn storage`로 커밋합니다.

## Task 6: 바닐라 프론트 사용자 흐름

**Files:** Create `frontend/index.html`, `frontend/styles.css`, `frontend/js/{auth,api,state,app,stocks,records,conversations,chat}.js`, `frontend/scripts/build-config.mjs`, `frontend/package.json`, `frontend/.env.example`, `frontend/tests/{api,state,config}.test.mjs`.

**Interfaces:** `auth.getIdToken()`, `api.request(path, {method, body, signal})`, `state.selectStock(stock)`. 상태는 selectedSymbol/conversationId/generation/busy/nextCursor를 관리하며 응답 표시 전에 generation을 확인합니다. 빌드 스크립트는 공개 설정 4개만 JSON으로 안전하게 직렬화하여 config.js에 기록합니다. Firebase 브라우저 SDK는 공식 ES module의 고정 버전을 사용하며 UI 프레임워크는 추가하지 않습니다.

- [x] api/state/config 테스트를 먼저 작성합니다: 종목 전환 후 늦은 응답 폐기, 만료 토큰 1회 갱신, POST timeout 자동 재전송 없음, config에 서버 비밀 없음. `node --test frontend/tests/*.test.mjs`로 실패를 확인합니다.
- [x] 로그인, 종목 검색·등록·선택, 요약, 개인 기록 CRUD, 복수 대화 목록·생성·복원·삭제, 채팅과 로딩을 구현합니다. 모든 목록에 `더 보기`를 연결하고 사용자 문자열은 textContent로 표시합니다. 대화 복원 시 종목도 복원합니다. 입력 라벨·키보드 사용·작은 화면 배치를 제공합니다.
- [x] health 연결 timeout 60초, 일반 GET 30초, chat 90초를 적용하고 콜드스타트 안내와 재시도를 표시합니다. 채팅 재시도는 같은 request ID를 사용합니다. 로그아웃 시 화면의 개인 데이터와 요청 상태를 초기화합니다.
- [x] node 테스트 성공 후 브라우저에서 HTML 메모의 텍스트 표시, 종목 전환 중 늦은 응답, 같은 종목의 두 대화 독립, 기록 추가→수정→삭제, 재로그인 복원을 검증합니다. 일반 화면과 작은 화면 스크린샷을 확인합니다.
- [x] `feat: add vanilla stock assistant interface`로 커밋합니다.

## Task 7: 실제 서비스 연결과 배포 설정

**Files:** Create `render.yaml`, `vercel.json`, `firestore.rules`, `firestore.indexes.json`, `backend/scripts/verify_integration.py`, `docs/deployment.md`; Modify `README.md`, `backend/.env.example`, `frontend/.env.example`.

**Interfaces:** integration script는 테스트 토큰을 환경에서 받으며 값과 UID·키 내용을 출력하지 않습니다. 직접 생성한 테스트 문서 ID만 정리합니다. 결과는 데이터 건수, 검사별 pass/fail, GPT 호출 횟수입니다.

- [ ] Firestore·Render·Vercel 최신 공식 문서를 확인하고 uid+date, uid+symbol+updated_at, market+symbol+date 조회에 필요한 index와 브라우저 직접 접근 차단 rules를 작성합니다. Render는 backend를 기준 폴더로 PORT에 uvicorn을 실행하며 Vercel은 공개 설정 생성 후 정적 frontend를 제공합니다.
- [ ] 개발용 Firestore/Auth 계정, 서비스 키, OpenAI 키와 허용 UID를 환경에 설정합니다. 준비되지 않은 외부 인증·비밀 입력은 사용자에게 해당 설정만 요청합니다. 대체 객체 테스트를 실제 연결 검증으로 표시하지 않습니다.
- [ ] 실제 시장 데이터 100개 이상 저장·재조회, 기록 CRUD, 같은 종목의 대화 2개와 전체 복원, GPT 질문 1회 및 동일 요청 재시도(추가 호출 0회), 서버 재시작 후 기록 보존을 확인합니다. 생성한 테스트 개인 기록은 정리합니다.
- [ ] `backend/.venv/bin/python -m pytest backend/tests -q`, `node --test frontend/tests/*.test.mjs`, 공개 설정의 비밀 노출 검사, `git diff --check`를 실행합니다.
- [ ] 검증 결과를 검토하고 `chore: prepare Render and Vercel deployment`로 커밋합니다.

## Task 8: 배포 확인과 제출 증빙

**Files:** Modify `README.md`, `docs/deployment.md`; Create `docs/screenshots/{chat,records,conversations}.png`, `docs/verification.md`.

- [ ] 전체 브랜치를 리뷰하고 누락 기능·비밀 노출·데이터 혼합·중복 전송 문제를 수정해 관련 검증을 재실행합니다. 독립 리뷰는 사용자가 선택한 실행 방법과 승인한 모델 기준에 따릅니다.
- [ ] 개발 브랜치를 GitHub에 push하고 Render/Vercel에 실제 서비스를 연결합니다. Firebase 허용 도메인과 ALLOWED_ORIGINS를 실제 주소로 설정합니다. 기존 개발·배포 허가 범위에서 진행하며 외부 로그인 또는 유료 선택이 필요하면 해당 단계만 요청합니다.
- [ ] 배포 URL의 프론트·health·Swagger·인증 API·CORS·콜드스타트 안내를 확인합니다. 로그인 후 CRUD, 질문·답변, 같은 종목 두 대화의 복원·계속하기, 새로고침 후 저장 유지, 삭제를 확인합니다.
- [ ] 실제 실행에서 요약+질문+답변, 기록 저장 결과, 여러 대화 목록+복원 화면을 캡처합니다. 개인 이메일 등은 촬영 전에 표시에서 제외합니다. 검증 기록에는 mock/실제 연결/로컬/배포 구분, 출처·시각·검증 결과를 적습니다.
- [ ] README를 실제 venv/실행 명령, 환경 변수, 배포 3개 URL, 저장 구조, 컨텍스트 주입 흐름, 비용·상한, 데이터 한계와 스크린샷으로 업데이트합니다. 미완료 연결·검증은 명확히 표시합니다.
- [ ] `docs: add deployment verification and submission evidence`로 커밋하고 승인된 통합 방식으로 main에 반영하여 원격 커밋 일치를 확인합니다.

## 사용자 입력이 필요할 수 있는 지점

Firebase/Render/Vercel 계정 로그인, OpenAI 키, 허용 UID, 데이터 공급원 변경, 유료 서비스 선택입니다. 기존 인증을 먼저 확인하고 비밀 값을 채팅에 붙여넣도록 요청하지 않습니다. 외부 설정을 기다리는 동안 독립 구현과 대체 객체 검증을 진행하며, 실제 연결 완료와 구분합니다.

## 계획 자체 검토

설계의 각 기능을 Task 1~8에 연결했습니다. 시장/개인 데이터, 대화 메타데이터/메시지, UI/저장 책임을 분리하고 대체 객체 테스트와 실제 연결·배포 검증을 구분했습니다.

권장 실행 방식은 주담당이 이 작업에서 순서대로 구현하는 방식입니다. 인증·저장·요약·채팅·UI가 같은 API 계약에 의존하므로 한 담당자가 인터페이스를 유지하며 단계별 검증하기 좋습니다. 구현 시작 전 사용자가 계획을 검토하고 실행 방식을 선택합니다.
