# FastAPI 학습 노트

책 따라가면서 막혔던 부분, Spring과 비교한 개념, 환경 세팅 과정을 정리.

---

## 1. 환경 세팅 (실제로 한 것)

### 최종 환경

| 항목 | 버전 / 위치 |
|---|---|
| Python | 3.12.13 (Homebrew) |
| Poetry | 2.4.1 (pipx 설치, `~/.local/bin/poetry`) |
| Poetry plugin | `poetry-plugin-shell` (책의 `poetry shell` 명령 부활용) |
| 프로젝트 venv | `~/Library/Caches/pypoetry/virtualenvs/fastapi-ca-uyA_g9J_-py3.12` |

### 맥에 깔린 Python 3개 (정리 안 함, 둬도 됨)

| Python | 위치 | 용도 |
|---|---|---|
| Xcode 3.9 | `/usr/bin/python3` | 시스템 도구용. **건드리지 말 것** |
| Homebrew 3.12 | `/opt/homebrew/.../3.12` | 프로젝트용 |
| Homebrew 3.14 | `/opt/homebrew/.../3.14` | 안 쓰지만 brew 의존성 있을 수 있어서 둠 |

### 시행착오 요약

1. **시스템 pip로 poetry 설치** → `~/Library/Python/3.9/bin/poetry`로 가서 PATH 없음 → `command not found`
2. **brew install poetry** → 잘 되는데 `poetry self add poetry-plugin-shell` 하면 brew 관리 패키지의 RECORD 파일 없어서 에러
3. **pipx로 poetry 재설치** → plugin 추가도 정상 동작 (✅ 정답)

### Poetry 설치 명령 (정답 순서)

```bash
brew uninstall poetry           # 기존 brew poetry 제거
brew install pipx
pipx ensurepath                 # ~/.local/bin을 PATH에 추가
# (새 터미널 열기)
pipx install poetry
poetry self add poetry-plugin-shell  # poetry shell 명령 부활
```

### 프로젝트 Python 버전 갈아타기 (3.14 → 3.12)

```bash
cd fastapi-ca
# pyproject.toml에서: requires-python = ">=3.12,<3.13"
poetry env remove --all
poetry env use python3.12
poetry lock                     # lock 파일 재생성 (pyproject 바뀐 경우 필수)
poetry install
poetry env info                 # 확인
```

---

## 2. Poetry 1.x vs 2.x 포맷 차이 (책과 다른 이유)

책은 1.x 기준. 우리가 깐 건 2.x → `pyproject.toml` 구조가 다름.

### 책 (Poetry 1.x — Poetry 전용)

```toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.111.0"
uvicorn = {extras = ["standard"], version = "^0.30.1"}
```

### 우리 (Poetry 2.x — PEP 621 표준)

```toml
[project]
requires-python = ">=3.12,<3.13"
dependencies = [
    "fastapi (>=0.136.3,<0.137.0)",
    "uvicorn[standard] (>=0.30.0,<0.31.0)",
]

[tool.poetry]
package-mode = false   # 라이브러리 배포 안 함 (학습 프로젝트는 필수)
```

### 짚을 점

- **기능 동일, 적는 방식만 다름**. PEP 621은 파이썬 공식 표준 (pip, uv, hatch 등 다 같이 씀)
- `poetry add fastapi` 같은 명령은 그대로 먹음 → 손으로 toml 편집할 일 거의 없음
- `^0.111.0` (캐럿 표기) = `(>=0.111.0,<0.112.0)` (의미 동일)
- **`package-mode = false` 안 적으면** 2.x에서 `poetry install`이 에러로 죽음 (1.x에선 경고만)

### `poetry shell` 동작 차이

Poetry 2.0부터 `poetry shell`이 기본 제거됨. 두 가지 대안:

```bash
# 옵션 ①: 새 방식
eval $(poetry env activate)

# 옵션 ②: 플러그인 깔아서 책처럼 사용 (우리가 한 선택)
poetry self add poetry-plugin-shell
poetry shell
```

---

## 3. 개념 비교 — Python 웹 스택 ↔ Spring

### 전체 매핑

| 역할 | Python | Spring (Java) |
|---|---|---|
| **앱 프레임워크** | FastAPI, Django, Flask | Spring MVC, Spring WebFlux |
| **스펙 (인터페이스)** | ASGI (비동기) / WSGI (동기) | Servlet API / Reactive Streams |
| **스펙 구현체 = WAS** | uvicorn, hypercorn, gunicorn | Tomcat, Jetty, Undertow, Netty |
| **패키지 관리자** | Poetry / uv / pip | Maven / Gradle |
| **가상환경** | venv (내장) | (불필요 — JVM이 격리) |

### 요청 흐름

```
[브라우저]
    ↓ HTTP
[uvicorn]            ← WAS 역할 (Tomcat 자리)
    ↓ ASGI 프로토콜    ← 스펙 (Servlet API 자리)
[FastAPI 앱]         ← 비즈니스 코드 (Spring 컨트롤러 자리)
```

### ASGI는 WAS가 아님 — 스펙이다

자주 헷갈리는 부분. **ASGI = 약속 문서**, **uvicorn = 그 약속을 구현한 실제 서버**.

| 비유 | Python | Java |
|---|---|---|
| 약속 (인터페이스) | ASGI | Servlet API |
| 약속의 구현 | uvicorn | Tomcat |
| 약속을 따르는 앱 | FastAPI | Spring MVC |

스펙이 표준화돼 있어서 **서버 교체 가능** (FastAPI 코드 안 바꾸고 uvicorn ↔ hypercorn 갈아끼움). Spring이 Tomcat ↔ Jetty 갈아끼우는 거랑 동일 원리.

### uvicorn vs hypercorn

| | uvicorn | hypercorn |
|---|---|---|
| 컨셉 | 빠르고 가벼움 (Netty 느낌) | 풀스택 기능 (Undertow 느낌) |
| 기반 | `uvloop` (Cython으로 빨라진 이벤트 루프) | trio/asyncio |
| HTTP/2, HTTP/3 | ❌ | ✅ |
| 추천 시점 | 일반 FastAPI 프로젝트 | HTTP/2+ 필요할 때 |

대부분 프로젝트는 uvicorn. 책도 uvicorn 씀.

### Spring Boot vs FastAPI 실행 방식

- **Spring Boot**: 서버가 jar에 내장 → `java -jar app.jar` 한 줄로 끝
- **FastAPI**: 앱과 서버 분리 → `uvicorn main:app --reload`로 직접 띄움

`main:app` = "main.py 파일의 app 객체를 띄워라". Spring Boot이라면 자동인 부분을 손으로 지정.

### `uvicorn[standard]`의 `[standard]`는?

**extras** — 옵션 의존성. `[standard]` 붙이면 Cython 기반 고성능 모듈(`uvloop`, `httptools`)과 편의 기능(`watchfiles`, `websockets`, `python-dotenv`, `pyyaml`)이 함께 깔림.

```bash
poetry add "uvicorn[standard]"   # 추천 (책 방식)
poetry add uvicorn               # 최소 설치 (순수 파이썬)
```

---

## 4. pip / pip3 헷갈림

| 명령 | 설명 |
|---|---|
| `pip` | macOS Homebrew Python에는 **없음**. 항상 `pip3` 쓸 것 |
| `pip3` | `/opt/homebrew/.../python@3.14/bin/pip3` — 시스템 전역. **PEP 668로 보호됨** (직접 설치 막혀있음) |
| `python3 -m pip` | 가장 안전한 호출 방식 (어떤 python인지 명시적) |
| venv 안의 `pip` | venv 활성화 후엔 그냥 `pip` 써도 됨 (venv 안에 격리됨) |

**규칙**: 전역에 뭔가 깔고 싶으면 → **pipx**. 프로젝트 의존성은 → **poetry add** (또는 venv 안에서 `pip install`).

---

## 5. Cython 짧게

- **Cython** = 파이썬 비슷한 문법을 C로 컴파일해 빠르게 돌리는 도구
- C 확장이라 OS/Python 버전별로 미리 빌드된 **wheel**이 필요. 없으면 소스 컴파일 (빌드 도구 필요)
- 최신 Python(3.14 등)은 wheel 준비 안 된 경우 多 → 패키지 설치 시 실패 가능성. **그래서 책 학습은 3.12로 통일**
- 대표 사례: `uvloop`, `httptools`, `pydantic-core`, `psycopg2-binary` 등

---

## 6. 자주 쓸 명령어 치트시트

```bash
# 프로젝트 진입 + venv 활성화
cd ~/work/projects/FastApiStudy/fastapi-ca
poetry shell

# 패키지 추가/제거
poetry add fastapi
poetry add "uvicorn[standard]"
poetry remove <name>

# 의존성 동기화 (lock 기준 설치)
poetry install

# lock 파일만 재생성 (pyproject 수정 후)
poetry lock

# 현재 환경 정보
poetry env info
poetry env list

# Python 버전 변경
poetry env use python3.12

# 서버 띄우기 (책 1.3절 이후)
uvicorn main:app --reload
```
