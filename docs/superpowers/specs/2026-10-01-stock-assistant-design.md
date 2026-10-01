# 개인용 국내 주식 AI 분석 비서 설계

작성일: 2026-10-01
상태: 2026-10-01 사용자 승인 완료. 구현 계획 검토 단계이며 구현은 아직 시작하지 않았습니다.

## 1. 목적과 확정된 범위

본인만 사용하는 웹 서비스입니다. 국내 관심 종목을 여러 개 등록하고, 선택한 한 종목의 과거 주가·거래량과 개인 메모를 근거로 AI와 대화합니다. 삼성전자·SK하이닉스에 제한하지 않습니다. 다른 시장은 추후 확장합니다.

사용자와 합의한 내용:

- 주가·거래량은 자동으로 가져옵니다.
- 사용자는 날짜·관심 가격·메모를 추가·수정·삭제합니다.
- 시장 가격과 사용자 관심 가격은 별개 데이터입니다.
- 한 대화는 한 종목에 연결합니다. 종목별 대화 개수에 제한을 두지 않습니다.
- 대화는 자동 저장하고, 목록에서 불러와 이어가거나 삭제합니다.
- FastAPI, HTML/CSS/JavaScript, Firestore, GPT API를 사용합니다.
- 백엔드는 Render, 프론트엔드는 Vercel에 배포합니다.

이번 문서의 구현 제안:

- 국내 범위는 코스피·코스닥 상장 주식입니다. ETF·ETN·코넥스는 첫 버전 검색 대상에서 제외합니다.
- 최근 1년의 일별 데이터를 기본 분석 범위로 사용합니다.
- Firebase Authentication 이메일/비밀번호 로그인과 서버의 허용 UID 한 개로 개인 접근을 제한합니다. 회원가입 화면은 제공하지 않습니다.
- 선택 보너스인 Function Calling, MCP/Actions, 그래프, 내보내기, 다크 모드는 필수 기능 완료 범위에 포함하지 않습니다. 별도 선택 시 추가합니다.

## 2. 사용자 흐름과 화면

로그인 후 종목 검색과 관심 목록을 표시합니다. 종목명 또는 6자리 코드로 검색해 등록합니다. 선택한 종목의 명칭·코드·데이터 기준일을 항상 표시합니다.

주요 화면은 세 구역입니다.

1. 분석·채팅: 데이터 기간, 개수, 종가 통계, 최근 추세, 거래량 요약을 보여줍니다. 새 대화를 만들고 질문하면 로딩 상태 후 답변을 표시합니다.
2. 내 기록: 날짜, 관심 가격(원), 메모를 입력하고 기존 기록을 수정·삭제합니다. 저장 결과를 표시하고 목록 및 AI용 요약을 갱신합니다.
3. 대화 기록: 선택한 종목의 여러 대화를 제목·수정일과 함께 표시합니다. 선택 시 해당 종목과 메시지를 복원합니다. 새 대화 생성, 이어서 질문, 삭제를 제공합니다.

현재 대화의 종목을 바꾸는 기능은 없습니다. 다른 종목 선택 시 그 종목의 대화 목록으로 이동하며, 기존 대화는 보존합니다. 요청이 진행 중일 때 중복 전송을 막습니다.

표시 문구는 한국어 `~합니다/~습니다/~입니다`로 통일합니다. 첫 연결 시 서버 준비에 시간이 걸릴 수 있다는 안내와 재시도 버튼을 제공합니다.

## 3. 애플리케이션 구조

```text
frontend/                 HTML, CSS, JavaScript, 환경 설정 생성 스크립트
backend/app/main.py       앱 초기화, CORS, 예외 처리
backend/app/routers/      종목, 데이터, 대화, 채팅 HTTP 계약
backend/app/schemas/      Pydantic 요청·응답 검증
backend/app/services/     시장 데이터 수집, 요약 계산, 대화 흐름, AI 호출
backend/app/repositories/ Firestore 조회·저장
backend/app/providers/    시장 데이터와 OpenAI 어댑터
backend/app/core/         환경 설정, 인증, 공통 오류
backend/tests/            핵심 계산·인증·API·저장 오류 검증
docs/                     설계와 제출 증빙
```

라우터는 요청 검증 및 서비스 호출을 담당합니다. 요약 계산은 외부 서비스와 분리한 순수 계산 함수로 구성합니다. Firestore 접근과 외부 API는 어댑터로 분리하여 테스트에서 대체할 수 있습니다.

시장 식별자는 `KR`과 6자리 종목 코드입니다. 외부 데이터 수집을 provider 경계로 분리해 추후 시장 추가 시 주된 채팅·저장 구조를 재사용합니다.

## 4. 시장 데이터 수집과 요약

FinanceDataReader를 우선 검증 후보로 사용합니다. 공식 프로젝트가 국내 종목 목록과 가격 조회를 제공하지만, 실제 국내 데이터 접근 가능성·출력 컬럼·가격 조정 방식은 구현 초기에 실데이터로 검증해야 합니다. 검증되지 않은 가격을 보정 가격이라고 표시하지 않습니다.

종목 목록은 캐시하여 검색하고, 등록 시 유효한 상장 종목인지 확인합니다. 선택 시 Firestore에 저장된 데이터를 먼저 읽습니다. 최근 동기화가 24시간 이내이면 재사용하고, 신규 종목·오래된 데이터 또는 명시적 새로고침 요청 시 최근 1년을 수집하여 날짜별로 upsert합니다. 수집 실패 시 기존 데이터와 갱신 실패 상태를 함께 표시하며 임의 데이터를 생성하지 않습니다.

휴장일 데이터를 채우지 않고 중복 날짜를 제거합니다. 날짜, 유한한 양수 가격, 0 이상의 거래량을 검증합니다. 결측·비정상 행 제외 개수를 표시합니다. 저장을 분할해 Firestore 배치 한도를 준수합니다.

요약은 시장 데이터와 개인 기록을 별도 필드로 반환합니다.

- 시장 데이터: 시작·종료 날짜, 개수, 평균·최고·최저 종가, 마지막 종가와 날짜, 평균·최근 거래량.
- 추세: 최근 20개 종가의 평균과 그 직전 20개 평균 비교. 변화율 +1% 초과는 상승, -1% 미만은 하락, 그 사이는 유지로 정의합니다. 비교 데이터 40개 미만이면 판단 불가입니다.
- 개인 기록: 개수와 최근 20개 기록의 날짜·관심 가격·메모. 개인 관심 가격을 시장 종가 통계에 섞지 않습니다.
- 품질: 출처, 조회 시각, 가격 조정 방식의 확인 상태, 표본 부족·갱신 실패 안내.

최근 1년 내 유효한 시장 데이터가 100개 미만인 종목도 화면에서 조회할 수 있지만 표본 부족을 표시합니다. 과제 완료 검증에는 실제 시장 데이터 100개 이상인 종목을 사용합니다. 기간은 거래일 기준으로 계산하고 사용자 요청에 없는 실시간 시세·뉴스·재무 정보는 답변 근거로 제공하지 않습니다.

## 5. Firestore 저장 구조

모든 개인 문서에는 `owner_uid`를 저장하고 서버에서 인증된 UID로 조회합니다. 브라우저는 Firestore를 직접 읽거나 쓰지 않습니다. 클라이언트용 Firestore 규칙은 직접 접근을 차단하며, Admin SDK 권한의 접근 제어는 FastAPI가 수행합니다.

| 컬렉션 | 주요 필드 | 용도 |
| --- | --- | --- |
| stocks | market, symbol, name, exchange, refreshed_at | 종목 검색용 목록 |
| watchlist | owner_uid, market, symbol, name, created_at | 관심 종목 |
| market_data | market, symbol, date, close, volume, source, fetched_at | 날짜별 시장 데이터 |
| data | owner_uid, market, symbol, date, value, memo, created_at, updated_at | 사용자의 관심 가격·메모 CRUD |
| conversations | owner_uid, market, symbol, title, created_at, updated_at, status | 대화 목록과 메타데이터 |
| conversations/{id}/messages | role, content, turn_id, sequence, created_at, context_snapshot | 대화 메시지 |
| sync_state | market, symbol, last_success_at, last_error | 데이터 갱신 상태 |

시장 데이터 문서 ID는 시장·종목·날짜 조합으로 정해 중복을 방지합니다. 개인 기록은 같은 날짜에도 여러 개 작성할 수 있습니다. 관심 목록 중복 등록은 기존 항목을 반환합니다. 관심 목록 제거 시 대화와 기록은 삭제하지 않습니다. 대화 삭제 시 메시지 하위 컬렉션도 서버에서 삭제하며, 삭제 진행 상태와 재시도를 관리합니다.

## 6. API 계약

`/api`의 개인 데이터·AI 엔드포인트는 Bearer Firebase ID token을 요구합니다. 서버는 토큰을 검증하고 `ALLOWED_USER_UID`와 일치하는 사용자만 허용합니다. 클라이언트가 전달한 owner UID는 신뢰하지 않습니다. `/health`와 `/docs`는 공개하며 Swagger에서도 Bearer 인증을 사용합니다.

| 메서드·경로 | 동작 |
| --- | --- |
| GET /api/stocks?q= | 국내 종목 검색 |
| GET /api/watchlist | 관심 종목 목록 |
| POST /api/watchlist | 종목 등록 |
| DELETE /api/watchlist/{id} | 관심 목록에서 제거 |
| POST /api/stocks/{symbol}/refresh | 시장 데이터 수집·갱신 |
| POST /api/data | `{symbol, date, value, memo}` 개인 기록 추가 |
| GET /api/data?symbol= | 해당 종목의 개인 기록 목록 |
| PUT /api/data/{id} | 날짜·관심 가격·메모 수정 |
| DELETE /api/data/{id} | 개인 기록 삭제 |
| GET /api/data/summary?symbol= | 시장 요약과 개인 기록 요약 |
| POST /api/conversations | 종목과 messages를 검증해 새 대화 저장; 빈 messages도 허용 |
| GET /api/conversations?symbol= | 대화 메타데이터 목록; messages는 포함하지 않음 |
| GET /api/conversations/{id} | 메타데이터와 전체 messages 조회 |
| DELETE /api/conversations/{id} | 대화와 메시지 삭제 |
| POST /api/chat | 질문 답변 및 대화 자동 저장 |

목록은 cursor 기반으로 페이지 처리하며 프론트의 더 보기 동작과 연결합니다. `POST /api/chat` 입력은 `symbol`, `message`, 선택적 `conversation_id`, 재시도 식별용 `request_id`입니다. 기존 대화 ID가 있으면 종목 일치 여부를 검사합니다. 응답은 `conversation_id`, 저장된 사용자·AI 메시지, 답변 당시 context 요약입니다.

Pydantic으로 6자리 코드, ISO 날짜(미래 날짜 불허), 유한한 양수 관심 가격, 메모 최대 1,000자, 질문 최대 2,000자를 검증합니다. 수동 대화 저장은 최대 100개 메시지와 메시지별 8,000자 제한을 적용하며 role은 user/assistant만 허용합니다. 존재하지 않거나 소유권이 없는 문서는 404, 인증 실패는 401, 허용 계정 불일치는 403으로 처리합니다.

## 7. AI 컨텍스트와 자동 저장

채팅 서비스는 summary API와 같은 요약 서비스를 직접 호출합니다. 서버 내부에서 자신의 HTTP API를 다시 호출하지 않습니다.

```text
질문 및 대화 소유권 검증
→ 선택 종목의 최신 저장 데이터 요약
→ 시스템 지침 + 구조화된 요약 + 개인 기록 + 최근 대화
→ GPT 호출
→ 사용자·AI 메시지와 당시 요약을 원자적으로 저장
→ 저장된 답변을 화면에 반환
```

시스템 지침은 선택 종목·분석 기간·데이터 기준일을 명시하고, 주어진 근거에 없는 사실은 확인할 수 없다고 답하도록 합니다. 메모와 대화는 사용자 데이터로 처리하며 그 안의 지시가 시스템 지침을 바꾸지 못하도록 구성합니다. 가격과 추세 해석은 과거 데이터의 관찰과 한계를 설명합니다.

최근 대화 최대 12개 메시지를 모델에 전달합니다. 메모·대화·요약 전체 입력 길이를 제한하고, 출력 토큰 상한과 호출 timeout을 환경 설정으로 관리합니다. 모델 ID는 `OPENAI_MODEL`로 설정합니다.

대화 문서에 진행 중 요청과 request ID를 기록하여 같은 대화의 동시 질문을 방지합니다. 동일 request ID의 성공 재시도는 기존 결과를 반환합니다. 잠금 만료 시간을 두어 중단된 요청을 복구합니다. OpenAI 호출 중 Firestore 트랜잭션을 유지하지 않습니다. 호출 성공 후 메시지 저장이 실패하면 저장 실패를 명확히 반환하고, 화면은 답변을 저장 완료로 표시하지 않습니다. 외부 모델 호출과 DB 저장 간 완전한 exactly-once는 보장하지 않으며 자동 재호출을 제한합니다.

## 8. 배포와 환경 변수

백엔드 기본 환경 변수:

- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_MAX_OUTPUT_TOKENS`
- `FIREBASE_SERVICE_ACCOUNT_JSON` 또는 `GOOGLE_APPLICATION_CREDENTIALS`
- `ALLOWED_USER_UID`
- `ALLOWED_ORIGINS` — 로컬 및 실제 Vercel 도메인 목록
- `PORT` — Render 제공 포트

프론트 빌드 환경 변수:

- `API_BASE_URL`
- Firebase 로그인용 공개 설정: `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`

바닐라 프론트는 빌드 스크립트가 공개 설정만 담은 config.js를 생성합니다. 서버 비밀 키는 출력하지 않습니다. Firebase 웹 설정은 인증·접근 제어를 대신하지 않습니다. 서비스 계정 JSON과 OpenAI 키는 서버 환경에만 둡니다.

Render 실행 명령은 PORT를 사용한 uvicorn입니다. Vercel은 정적 파일과 설정 생성 빌드를 배포합니다. CORS는 실제 허용 origin과 필요한 메서드·Authorization 헤더를 명시합니다. 콜드스타트 안내, 연결 timeout, 사용자 재시도를 구현합니다. 채팅 POST를 연결 오류만으로 자동 반복하지 않습니다.

배포에는 사용자 계정 로그인, Firebase 프로젝트·Firestore·허용 사용자, OpenAI API 키, GitHub 저장소, Render/Vercel 프로젝트 접근이 필요합니다. 비밀 값은 채팅에 붙여넣지 않고 로컬 환경 파일 또는 배포 서비스 설정에 입력합니다. 배포 URL은 실제 배포·확인 후 README에 기록합니다.

## 9. 검증과 완료 기준

- 실제 국내 종목의 유효 데이터 100개 이상을 저장하고 Firestore 기반 요약을 확인합니다.
- 시장 가격과 관심 가격이 섞이지 않는지, 추세 경계·데이터 부족을 계산 테스트로 검증합니다.
- 기록 CRUD, 종목별 복수 대화, 전체 대화 불러오기·삭제, 소유권 검증을 테스트합니다.
- 모델을 대체한 API 테스트로 정확한 종목 컨텍스트·자동 저장·중복 요청·호출 및 저장 실패를 검증합니다.
- 실제 Firestore/GPT 연결은 제한된 횟수로 별도 확인합니다. 대체 객체 테스트를 실서비스 검증으로 표시하지 않습니다.
- 브라우저에서 로그인, 종목 등록·선택, 기록 추가·수정·삭제, 질문 로딩·답변, 같은 종목의 두 대화 생성과 복원을 확인합니다.
- 배포된 프론트와 API, Swagger 인증 호출, CORS, 서버 재시작 후 기록 유지를 확인합니다.
- README에는 소개, 스택, URL, 로컬 실행·venv, 환경 변수, 컬렉션, 컨텍스트 주입 흐름, 비용 제한, 데이터 출처와 제한을 기록합니다.
- 제출 스크린샷은 요약과 질문·답변, 데이터 관리 동작, 여러 대화 목록 및 복원 화면을 실제 실행에서 캡처합니다.

## 10. 확인한 공식 자료

- FinanceDataReader: https://github.com/FinanceData/FinanceDataReader
- Firebase ID token 검증: https://firebase.google.com/docs/auth/admin/verify-id-tokens

실데이터 수집, OpenAI 모델 선택과 배포 설정은 구현 단계에서 최신 공식 자료와 실제 연결 결과를 확인합니다.
