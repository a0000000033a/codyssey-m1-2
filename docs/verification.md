# 검증 기록

기준일: 2026-10-01 (Asia/Seoul). 구현 및 개발 검증 완료, 실제 외부 계정 연결·배포 검증 대기.

| 종류 | 근거 | 결과 |
| --- | --- | --- |
| API·서비스 테스트 | backend/.venv/bin/python -m pytest backend/tests -q | 49개 통과; 저장소·AI·token 검증기는 테스트 대체 객체 |
| 프론트 로직 | node --test frontend/tests/*.test.mjs | 6개 통과 |
| 실제 시장 조회 | verify_market.py --symbol 005930 | 국내 종목 2,590개, 2025-10-01~2026-10-01 주가 242개, 제외 0개 |
| 실제 로컬 HTTP | uvicorn 후 GET /health | 200, 개인 설정 미완료 상태 확인 |
| 실제 브라우저 DOM+HTTP | browser.mjs + preview_server | 로그인, 종목 검색/등록, 기록 CRUD, HTML 메모 안전 표시, 같은 종목 대화 2개 생성·복원, 모바일 가로 넘침 없음, 로그아웃 통과 |
| 정적 빌드 | build-site.mjs | 공개 config 및 html/css/js만 frontend/dist에 생성 |

NAVER EUC-KR XML 파싱 오류를 재현하는 회귀 테스트가 실패한 뒤 인코딩 처리를 수정해 통과했습니다. 브라우저 테스트의 대화 열기·삭제 버튼 선택자 충돌은 대화 열기 버튼으로 한정해 수정했습니다.

Python 3.12.14와 requirements-lock.txt에 기록한 의존성을 사용했습니다. Starlette의 anyio BlockingPortal 관련 upstream deprecation warning 1개가 있습니다.

## 미검증

- 실제 Firebase 로그인 및 Admin SDK/Firestore 읽기·쓰기·트랜잭션
- 실제 OpenAI 답변과 데이터 요약 반영
- 서버 재시작 후 실제 Firestore 기록 유지
- Render/Vercel 배포와 실제 도메인 CORS/Swagger 인증
- 실제 서비스의 최종 제출용 스크린샷

환경 파일과 실제 서비스 token이 없어서 verify_integration.py는 missing token으로 not_run을 반환했습니다. 이를 성공 검증에 포함하지 않습니다.

screenshots/development는 테스트용 인증·메모리 저장소·대체 AI를 사용해 촬영했고 화면 상단에 그 상태를 표시했습니다. 시장 데이터 242개 수집은 별도의 실제 공개 조회입니다. 개발 화면의 예시 가격·AI 답변은 실제 분석 결과로 사용하지 않습니다.

추가 회귀 검증: 대화 삭제 시 재시도용 답변·요약 사본을 제거하고 식별 tombstone만 유지하며, 동일 요청의 늦은 재시도는 대화를 재생성하지 않습니다. 같은 종목의 대화를 빠르게 바꿀 때 늦은 응답이 마지막 선택을 덮어쓰는 문제를 브라우저에서 재현한 뒤 수정해 통과했습니다.

리뷰 후 추가 검증: 유효한 가격이 하나도 없을 때 `market_invalid_data`와 제외 건수를 보존합니다. 삭제 중인 대화의 늦은 복원 응답은 무시합니다. 답변 저장 후 상세 조회만 실패하면 같은 요청 ID로 재시도하며 중복 메시지를 만들지 않습니다. 세 항목 모두 실패를 재현한 뒤 수정하여 통과했습니다.
