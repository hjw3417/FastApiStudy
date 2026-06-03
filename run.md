# 실행 & API 테스트 가이드

> 자주 까먹는 **실행/테스트 명령 모음**. (개념은 [study.md](study.md), 환경 세팅 시행착오는 [notes.md](notes.md))

## TL;DR — 서버 실행

```bash
cd ~/work/projects/FastApiStudy/fastapi-ca     # ⚠️ 반드시 여기서 (git 루트 아님)
poetry run uvicorn main:app --reload
```

- 뜨면 → `Uvicorn running on http://127.0.0.1:8000`
- **끄기**: `Ctrl + C`
- 이 터미널은 서버가 점유함 → **curl은 다른 터미널**에서.
- `poetry shell`로 venv 활성화한 상태면 `poetry run` 생략 가능: `uvicorn main:app --reload`

## 실행 명령 뜯어보기

| 조각 | 의미 |
|---|---|
| `main:app` | `main.py`의 `app` 객체를 띄워라 |
| `--reload` | 코드 바뀌면 자동 재시작 (개발용. 운영선 빼기) |
| `--port 8001` | 포트 변경 (기본 8000) |
| `--host 0.0.0.0` | 외부 접속 허용 (기본 127.0.0.1 = 내 PC만) |

## 접속 주소

| 주소 | 용도 |
|---|---|
| http://localhost:8000/ | 루트 (`{"Hello":"FastAPI"}`) |
| http://localhost:8000/docs | **Swagger UI** — 테스트 추천 👍 |
| http://localhost:8000/redoc | ReDoc (읽기용 문서) |

## API 테스트 — 2가지

### ① Swagger UI (쉬움, 추천)

브라우저 → `http://localhost:8000/docs` → 엔드포인트 펼치기 → **Try it out** → 값 입력 → **Execute**. curl 안 쳐도 클릭으로 끝.

### ② curl

```bash
# POST /users  — 바디 필수! (없으면 422)
curl -X POST 'http://localhost:8000/users' \
  -H 'Content-Type: application/json' \
  -d '{"name":"kim","email":"kim@test.com","password":"12345678"}'
```

```bash
# GET 루트
curl http://localhost:8000/
```

#### 여러 줄 curl (`\`) — 책 스타일

`\` = **"줄 연속"** 표시("다음 줄에 이어짐"). 책처럼 줄 나눠 쓸 때 사용.

```bash
curl -X 'POST' \
  'http://localhost:8000/users' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "Dexter",
  "email": "dexter.haan@gmail.com",
  "password": "test-password"
}'
```

- 줄 끝 `\` → 계속 / 줄 끝 `\` 없음 → 실행. **마지막 줄(`}'`)엔 `\` 빼야** 실행됨.
- `-d '{` 줄에 `\`가 없어도 이어지는 건 **작은따옴표 `'`가 안 닫혀서** (`}'`에서 닫힘).
- 마지막에 `\`를 남기면 셸이 `>`만 띄우고 멈춤(입력 대기). → `Ctrl+C` 후 다시.
- 헷갈리면 **블록째 복붙**하거나 **한 줄로** 쓰기.

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `ModuleNotFoundError: No module named 'user'` | `fastapi-ca` 아닌 데서 실행 → `cd fastapi-ca` |
| `command not found: uvicorn` | `poetry run` 안 붙임 / venv 비활성 → `poetry run uvicorn ...` |
| `Address already in use` (8000 점유) | `lsof -i :8000`로 PID 찾아 `kill <PID>`, 또는 `--port 8001` |
| `422 Unprocessable Entity` | 요청 바디 누락/형식 오류 → 필수 필드(name·email·password) 확인 |
| 코드 고쳤는데 반영 안 됨 | `--reload` 빠졌거나, import 에러로 reload 실패 → 터미널 로그 확인 |
