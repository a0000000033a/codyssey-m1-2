# 실제 연결 및 배포 설정

Render API(`https://codyssey-m1-2-api.onrender.com`)와 Vercel 프론트(`https://project-6ablk.vercel.app`)를 배포했습니다. 개인 계정·Firestore·코디세이 AI 설정을 연결했으며, 배포 환경 전체 기능 검증은 아직 완료하지 않았습니다. 비밀 키나 서비스 계정 JSON은 채팅 또는 GitHub에 붙여넣지 않습니다.

## 1. Firebase

1. [Firebase Console](https://console.firebase.google.com/)에서 프로젝트를 만듭니다.
2. Firestore Database를 생성하고 위치를 선택합니다. 위치는 변경이 어려우므로 사용할 지역을 먼저 확인합니다.
3. Authentication의 이메일/비밀번호 로그인을 활성화하고 Users에서 본인 계정 하나를 추가합니다. 그 계정의 UID를 `ALLOWED_USER_UID`로 설정합니다.
4. 프로젝트 설정의 서비스 계정에서 Admin SDK용 키를 준비합니다. 로컬에서는 키 파일을 Git 저장소 밖에 두고 `GOOGLE_APPLICATION_CREDENTIALS`에 절대 경로를 지정합니다. Render에서는 JSON 전체를 `FIREBASE_SERVICE_ACCOUNT_JSON` 비밀 환경 변수에 넣습니다. 두 방식 중 하나를 사용합니다.
5. 웹 앱을 등록하고 공개 설정 3개(apiKey/authDomain/projectId)를 `frontend/.env`에 넣습니다.
6. Authentication 설정에서 로컬 `localhost`와 `127.0.0.1`, 실제 Vercel 도메인을 허용 도메인으로 등록합니다.
7. Firestore Rules에는 저장소의 `firestore.rules`를 적용합니다. 웹에서 직접 Firestore로 접근하지 않으며 모든 데이터는 인증된 FastAPI에서 처리합니다. Firebase Admin SDK는 Rules를 우회하므로 FastAPI의 UID 검증이 접근 제어를 담당합니다.
8. Firebase CLI를 사용한다면 `firebase deploy --only firestore --project 본인프로젝트ID`로 저장소의 rules와 index를 적용합니다. CLI가 없으면 콘솔에서 Rules를 적용하고 필요한 index를 확인합니다.

## 2. OpenAI와 로컬 설정

사용할 플랫폼에서 발급한 키를 `backend/.env`의 `OPENAI_API_KEY`에 넣습니다. 키, API 주소, 호출 방식, 모델을 함께 바꿔야 합니다. OpenAI 공식 키와 다른 플랫폼의 가상 키는 서로 바꿔 사용할 수 없습니다.

공식 OpenAI 설정:
```dotenv
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_MODE=responses
OPENAI_MODEL=gpt-5.4-mini
```

코디세이 플랫폼 설정:
```dotenv
OPENAI_BASE_URL=https://copa.codyssey.kr/v1
OPENAI_API_MODE=chat_completions
OPENAI_MODEL=gpt-5.4-mini
OPENAI_CHAT_TOKEN_FIELD=max_completion_tokens
```

`OPENAI_BASE_URL`에는 `/chat/completions`나 `/responses`를 붙이지 않습니다. 다른 플랫폼도 OpenAI 호환 프로토콜을 지원해야 하며, 지원 모델과 출력 제한 필드를 확인합니다. Chat Completions가 `max_tokens`만 받는 경우 `OPENAI_CHAT_TOKEN_FIELD=max_tokens`로 바꿉니다. `/models` 지원 여부와 채팅 지원 여부는 다를 수 있으므로 모델 조회 실패만으로 키가 잘못됐다고 판단하지 않습니다.

출력 상한은 기본 800토큰, 호출 시간은 45초, 자동 재시도는 0회입니다. Responses는 `store=false`를 사용합니다. 호환 Chat 플랫폼의 데이터 보관 정책은 해당 플랫폼에서 확인해야 합니다. 환경 파일을 바꾼 뒤 API 서버를 재시작합니다.

로컬 환경 파일은 각 `.env.example`을 복사해 생성합니다. `ALLOWED_ORIGINS`는 JSON 배열입니다. 예: `["http://127.0.0.1:5500","http://localhost:5500"]`.

```sh
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

프론트 공개 설정의 `FIREBASE_API_KEY`는 웹 설정이며 OpenAI 키나 Firebase 서비스 계정 키를 넣는 칸이 아닙니다. 생성되는 config.js에는 공개 설정 4개만 들어갑니다.

## 3. Render 백엔드

- 저장소: `a0000000033a/codyssey-m1-2`
- 운영 배포 브랜치: `main` (Render 및 Vercel Production Branch Tracking)
- Root Directory: `backend`
- Python: `3.12.14`
- Build: `pip install -r requirements-lock.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- 플랜: free 설정을 제공하며 유료 플랜 전환은 별도로 결정합니다.

환경 변수는 OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_API_MODE, OPENAI_MODEL, OPENAI_CHAT_TOKEN_FIELD, FIREBASE_SERVICE_ACCOUNT_JSON, ALLOWED_USER_UID, ALLOWED_ORIGINS입니다. 추가 제한 설정은 `backend/.env.example`을 확인합니다. 키를 등록하지 않아도 health/docs는 열리지만 개인 API는 설정 미완료를 표시합니다.

배포 후 실제 주소의 `/health`와 `/docs`를 확인합니다. Swagger Authorize에는 로그인한 Firebase ID token을 넣습니다. 화면에서 첫 연결 지연 안내와 재시도를 제공합니다. 콜드스타트 중 채팅 POST를 자동 반복하지 않습니다.

## 4. Vercel 프론트

저장소를 가져오고 Framework Preset은 Other, Root Directory는 저장소 루트로 둡니다. `vercel.json`이 `node frontend/scripts/build-site.mjs`를 실행하여 `frontend/dist`를 정적 배포합니다. 환경 파일·테스트·빌드 스크립트는 출력에 포함하지 않습니다.

환경 변수 4개:

- API_BASE_URL: 실제 Render API 주소 (마지막 `/`는 선택)
- FIREBASE_API_KEY: Firebase 웹 공개 설정
- FIREBASE_AUTH_DOMAIN: Firebase 웹 인증 도메인
- FIREBASE_PROJECT_ID: Firebase 프로젝트 ID

Vercel 도메인이 정해지면 Render의 ALLOWED_ORIGINS와 Firebase 허용 도메인에 추가합니다. 환경 변수를 바꾸면 프론트를 재배포합니다. Vercel production 배포 브랜치는 검증 대상 개발 브랜치로 명시하고, main 통합 후 main으로 맞춥니다.

## 5. 실제 검증

짧게 유효한 Firebase ID token을 로컬 환경에 `VERIFY_FIREBASE_ID_TOKEN`으로 설정합니다. 화면이나 채팅에 토큰을 표시하지 않습니다. `VERIFY_API_BASE_URL`을 실제 API 주소로 설정하고, GPT 호출을 포함하려면 `VERIFY_CALL_AI=1`을 설정합니다.

```sh
backend/.venv/bin/python backend/scripts/verify_integration.py
```

이 스크립트는 개인 기록과 대화 2개를 생성·수정·조회하고 종료 시 직접 생성한 문서만 삭제합니다. GPT 확인은 질문 1개와 동일 요청 재시도를 사용합니다. 스크립트 성공에 더해 서버 재시작 후 기록 유지와 브라우저 실제 로그인을 별도로 확인합니다. 종료 시 `cleanup` 결과도 확인합니다.

최종 제출은 실제 Firebase/GPT를 사용한 배포 화면에서 요약+질문/답변, 기록 저장·수정 결과, 복수 대화 목록·복원을 촬영합니다. `docs/screenshots/development`는 테스트 대체 연결을 사용한 개발 화면이며 최종 제출 증빙을 대신하지 않습니다.

## 공식 문서

- [Firebase token 검증](https://firebase.google.com/docs/auth/admin/verify-id-tokens)
- [Firestore 트랜잭션](https://firebase.google.com/docs/firestore/manage-data/transactions)
- [OpenAI Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
- [Render FastAPI](https://render.com/docs/deploy-fastapi)
- [Vercel 설정](https://vercel.com/docs/project-configuration/vercel-json)
