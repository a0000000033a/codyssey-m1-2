# 검증 기록

기준일: 2026-10-01 (Asia/Seoul). 구현 및 개발 검증 완료, Firebase 서버 연결 검증 완료, 실제 웹 로그인 및 시장 데이터 표시 검증 완료, GPT·배포 검증 대기.

| 종류 | 근거 | 결과 |
| --- | --- | --- |
| API·서비스 테스트 | backend/.venv/bin/python -m pytest backend/tests -q | 55개 통과; 저장소·AI·token 검증기는 테스트 대체 객체 |
| 프론트 로직 | node --test frontend/tests/*.test.mjs | 6개 통과 |
| 실제 시장 조회 | verify_market.py --symbol 005930 | 국내 종목 2,590개, 2025-10-01~2026-10-01 주가 242개, 제외 0개 |
| 실제 로컬 HTTP | uvicorn 후 GET /health | 200, 개인 설정 미완료 상태 확인 |
| 실제 브라우저 DOM+HTTP | browser.mjs + preview_server | 로그인, 종목 검색/등록, 기록 CRUD, HTML 메모 안전 표시, 같은 종목 대화 2개 생성·복원, 모바일 가로 넘침 없음, 로그아웃 통과 |
| 정적 빌드 | build-site.mjs | 공개 config 및 html/css/js만 frontend/dist에 생성 |

NAVER EUC-KR XML 파싱 오류를 재현하는 회귀 테스트가 실패한 뒤 인코딩 처리를 수정해 통과했습니다. 브라우저 테스트의 대화 열기·삭제 버튼 선택자 충돌은 대화 열기 버튼으로 한정해 수정했습니다.

Python 3.12.14와 requirements-lock.txt에 기록한 의존성을 사용했습니다. Starlette의 anyio BlockingPortal 관련 upstream deprecation warning 1개가 있습니다.

## 미검증

- 실제 OpenAI 답변과 데이터 요약 반영
- 서버 재시작 후 실제 Firestore 기록 유지
- Render/Vercel 배포와 실제 도메인 CORS/Swagger 인증
- 실제 서비스의 최종 제출용 스크린샷

환경 파일과 실제 서비스 token이 없어서 verify_integration.py는 missing token으로 not_run을 반환했습니다. 이를 성공 검증에 포함하지 않습니다.

screenshots/development는 테스트용 인증·메모리 저장소·대체 AI를 사용해 촬영했고 화면 상단에 그 상태를 표시했습니다. 시장 데이터 242개 수집은 별도의 실제 공개 조회입니다. 개발 화면의 예시 가격·AI 답변은 실제 분석 결과로 사용하지 않습니다.

추가 회귀 검증: 대화 삭제 시 재시도용 답변·요약 사본을 제거하고 식별 tombstone만 유지하며, 동일 요청의 늦은 재시도는 대화를 재생성하지 않습니다. 같은 종목의 대화를 빠르게 바꿀 때 늦은 응답이 마지막 선택을 덮어쓰는 문제를 브라우저에서 재현한 뒤 수정해 통과했습니다.

리뷰 후 추가 검증: 유효한 가격이 하나도 없을 때 `market_invalid_data`와 제외 건수를 보존합니다. 삭제 중인 대화의 늦은 복원 응답은 무시합니다. 답변 저장 후 상세 조회만 실패하면 같은 요청 ID로 재시도하며 중복 메시지를 만들지 않습니다. 세 항목 모두 실패를 재현한 뒤 수정하여 통과했습니다.

## 실제 Firebase 서버 연결 (2026-10-01)

프로젝트 `codyssey-m1-2-401b2`, Firestore Standard `(default)`, 서울 `asia-northeast3`, Spark 요금제, 프로덕션 모드로 생성했습니다. 이메일/비밀번호 제공업체와 개인 사용자, 웹앱 등록을 확인했습니다. 서비스 계정 키는 저장소 밖의 개인 설정 폴더에 권한 600으로 보관하며, backend/.env에는 파일 경로만 설정합니다. 프론트 공개 설정과 허용 사용자 UID는 Git에서 제외된 로컬 환경 파일에 반영했습니다.

Admin SDK의 본인 사용자 조회, Firestore 읽기, 실제 TurnStore 트랜잭션 저장, 동일 요청 재조회, 메시지 2개 복원, 대화 삭제와 재시도 tombstone을 검증했습니다. 이번 검증에서 생성한 임시 데이터만 정리했습니다. 검증 메시지는 직접 작성한 시험용 내용이며 실제 GPT 답변이 아닙니다. 웹 사용자 비밀번호는 에이전트에 전달하지 않았습니다. 실제 웹 로그인도 확인했습니다. OpenAI 호출과 Render/Vercel 배포는 다음 단계입니다.

실제 웹앱에서 개인 Firebase 계정으로 로그인한 뒤 ID token 기반 API 접근, 삼성전자 관심 목록 저장, NAVER 242개 일별 데이터의 실제 Firestore 저장과 요약 표시를 확인했습니다. 가격 화면 캡처는 로컬 임시 파일이며 아직 최종 배포 제출 화면이 아닙니다.

## OpenAI 호환 플랫폼 연결 (2026-10-06)

코디세이 가상 키는 공식 OpenAI 호스트에서 401을 반환했습니다. 발급처를 확인한 뒤 `OPENAI_BASE_URL=https://copa.codyssey.kr/v1`, `OPENAI_API_MODE=chat_completions`, `OPENAI_MODEL=gpt-5.4-mini`로 설정했습니다. 출력 상한 필드는 `OPENAI_CHAT_TOKEN_FIELD`로 선택합니다. 실제 짧은 Chat Completions 호출 1회에서 정상 비어 있지 않은 답변을 확인했습니다. 이 검증은 연결 확인 문구만 보내며 주가 분석·대화 저장까지의 검증은 아닙니다. 실제 SDK와 HTTP 대체 transport를 이용해 호스트/프로토콜/컨텍스트/출력 제한/미완료 응답 및 기존 Responses 계약을 검사했으며 Python 55개와 Node 6개 테스트가 통과했습니다. 로컬 API 서버를 새 설정으로 재시작했습니다.
