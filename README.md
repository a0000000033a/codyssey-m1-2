# 국내 주식 AI 분석 비서

국내 관심 종목의 과거 주가·거래량과 개인 기록을 바탕으로 질문에 답하는 개인용 AI 비서를 개발합니다.

현재는 설계 단계입니다. 실행 가능한 애플리케이션과 배포 URL은 아직 없습니다.

## 예정 기능

- 국내 관심 종목 검색·등록 및 한 종목씩 분석
- 최근 1년의 일별 시장 데이터 수집·저장과 요약
- 날짜·관심 가격·메모 추가·조회·수정·삭제
- 저장된 데이터 요약을 반영하는 AI 채팅
- 종목당 여러 대화 생성, 자동 저장, 불러오기 및 삭제
- 본인 계정 로그인

## 기술 구성

| 구성 | 기술 |
| --- | --- |
| 백엔드 | Python 3.10 이상, FastAPI, Pydantic |
| 프론트엔드 | HTML, CSS, JavaScript |
| 저장·인증 | Firebase Firestore, Firebase Authentication |
| AI | OpenAI GPT API |
| 배포 | Render(백엔드), Vercel(프론트엔드) |

시장 가격과 사용자가 입력한 관심 가격은 구분합니다. 대화 하나는 한 종목에 연결하며, 같은 종목에 여러 대화를 만들 수 있습니다.

## 설계

[설계 문서](docs/superpowers/specs/2026-10-01-stock-assistant-design.md)에 화면 흐름, API, 저장 구조, 컨텍스트 주입, 검증 및 배포 기준을 정리했습니다.

## 환경 변수 계획

서버에는 `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_MAX_OUTPUT_TOKENS`, `FIREBASE_SERVICE_ACCOUNT_JSON` 또는 `GOOGLE_APPLICATION_CREDENTIALS`, `ALLOWED_USER_UID`, `ALLOWED_ORIGINS`를 설정합니다.

프론트엔드에는 `API_BASE_URL`과 로그인용 공개 Firebase 설정인 `FIREBASE_API_KEY`, `FIREBASE_AUTH_DOMAIN`, `FIREBASE_PROJECT_ID`를 설정합니다.

OpenAI 키와 Firebase 서비스 계정 키는 서버 환경에서만 관리합니다. 실제 키, 환경 파일, 개인 데이터와 대화 기록은 저장소에 커밋하지 않습니다.

## 실행·배포·제출 증빙

로컬 실행 명령, 배포 URL(프론트엔드·API·Swagger), 실행 검증 결과와 제출 스크린샷은 구현 및 실제 배포 확인 후 추가합니다. 개발 중인 기능을 완료된 것으로 표시하지 않습니다.
