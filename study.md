# 클린 아키텍처 학습 정리

> 책(**FastAPI로 배우는 백엔드 프로그래밍 with 클린 아키텍처**)을 따라가며
> 파일·주제별로 질문하고 정리하는 개념 노트.
> (환경 세팅 관련은 [notes.md](notes.md)에 따로 정리됨)

## 기본 환경 (빠른 참조)

| 항목 | 이 프로젝트 | 책 | 비고 |
|---|---|---|---|
| Python | 3.12 | 3.11 | 호환 |
| FastAPI | 0.136 | 0.111 | 마이너 차이 |
| SQLAlchemy | 2.0 | 2.0 | 일치 |
| DB | **PostgreSQL** | MySQL | 다름 → 방언 주의 |
| 패키지 관리 | Poetry | Poetry | 일치 |

**⚠️ 명령 실행 위치**: 파이썬 앱은 git 루트가 아니라 **`fastapi-ca/`** 안에 있다. `poetry add` 등은 반드시 거기서.

```
FastApiStudy/          ← git 루트 (notes.md, rules.md, study.md). pyproject.toml 없음 ❌
└── fastapi-ca/        ← 실제 앱. poetry 명령은 여기서 ✅
    ├── pyproject.toml
    ├── main.py
    └── user/{domain, application, infra, interface}
```

> 상세 환경·설치 시행착오는 [notes.md](notes.md), 스택 비교/방언 주의점은 [rules.md](rules.md) 참고.

## 목차

1. [도메인 모델과 값 객체](#1-도메인-모델과-값-객체)
2. [데이터베이스 계층 — 도메인 모델 vs DB 모델, 리포지토리 패턴](#2-데이터베이스-계층--도메인-모델-vs-db-모델-리포지토리-패턴)
3. [추상 클래스(ABCMeta)로 리포지토리 인터페이스 — 의존성 역전(DIP)](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip)
4. [UUID vs ULID — 엔티티 id 생성](#4-uuid-vs-ulid--엔티티-id-생성)

---

## 1. 도메인 모델과 값 객체

### 도메인 계층이 뭔가

클린 아키텍처에서 **가장 안쪽**, 비즈니스의 핵심 개념이 사는 곳.
"유저란 무엇인가" 같은 **순수한 업무 규칙**만 둔다.

핵심 원칙: **도메인은 바깥(FastAPI, DB, 라이브러리)을 몰라야 한다.**

```
user/
├── domain/        ← 여기. FastAPI도 DB도 모름. 순수 파이썬만.
│   └── user.py
├── application/   ← 유스케이스(서비스 로직)
├── infra/         ← DB 구현 (SQLAlchemy 등)
└── interface/     ← 컨트롤러 (FastAPI 라우터)
```

그래서 `domain/user.py`의 `User`는 `@dataclass` 같은 **순수 파이썬**으로 만든다.
여기에 `from fastapi import ...`나 `from sqlalchemy import ...`가 들어오면 그 순간 도메인 오염.

> **Spring 비교**: 도메인 객체(POJO)가 특정 프레임워크 애너테이션에 안 묶이게 하는 것과 같은 원리.

### 엔티티 vs 값 객체

구분 기준은 딱 하나 — **"식별자(id)로 구별하느냐, 값으로 구별하느냐"**.

| | 엔티티 (Entity) | 값 객체 (Value Object) |
|---|---|---|
| 정체성 | **id로 구별** | **값으로 구별** (id 없음) |
| "같다"의 의미 | id 같으면 같음 | 모든 속성 같으면 같음 |
| 변경 | 가변 — 속성 바뀌어도 같은 객체 | **불변(immutable)이어야 함** |
| 예시 | `User`, `Post` | 돈(₩1000), 좌표(x,y), 이메일주소 |

비유:
- **엔티티 = 사람**. 이름 바꾸고 살쪄도 "주민번호 같으면 같은 사람".
- **값 객체 = 만원짜리 지폐**. 일련번호 안 따짐. "만원이라는 값"이 같으면 그냥 같은 것. 바꾸려면 새 지폐로 교체.

### `User`는 엔티티

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass            # frozen 없음 = 가변. 엔티티에 자연스러움
class User:
    id: str           # ← 이 id로 구별. 그래서 엔티티
    name: str
    email: str
    password: str
    created_at: datetime
    updated_at: datetime
```

이름·비번이 바뀌어도 `id`가 같으면 같은 유저 → **엔티티**. 가변 dataclass가 맞다.

### 값 객체로 만들려면 `frozen=True`

id 없이 값만으로 구별하고 싶은 개념(예: 프로필 묶음)을 따로 뺄 때:

```python
@dataclass(frozen=True)     # ← 이게 핵심. 한번 만들면 못 바꿈
class Profile:
    name: str
    email: str
```

`frozen=True`를 붙이면:
- `p.name = "새이름"` → **에러** (수정 불가 = 불변)
- 두 `Profile`은 `name`, `email`이 다 같으면 `==`가 `True` (값으로 비교)
- 바꾸려면 새 객체로 통째 교체: `user.profile = Profile("새이름", email)`

**주의**: `frozen` 안 붙인 그냥 `@dataclass`는 id가 없어도 *가변*이라 진짜 값 객체가 아니다. "불변"이 값 객체의 필수 조건.

> 📌 `Profile`은 책 설계가 아니라 개념 설명용 예시. 책은 보통 `User` 안에 `name`, `email`을 바로 둔다. 실제 구현은 책 흐름을 따른다.

### 왜 한 파일에 여러 클래스를 둬도 되나 (Java 습관 탈피)

파이썬은 **파일명 = 클래스명** 규칙이 없다. 한 파일에 클래스 여러 개 OK.

| | Java | Python |
|---|---|---|
| `public` 클래스 | 파일당 1개, 파일명과 일치 강제 | 규칙 없음, 몇 개든 가능 |
| 파일명 | `User.java` (PascalCase) | `user.py` (snake_case), 클래스명 무관 |

기준은 클래스 개수가 아니라 **응집도(같이 변경/이해되는가)**:
- ✅ 같은 파일: 엔티티 + 그에 종속된 값 객체, 같은 도메인 Enum
- 🔪 분리: 다른 도메인(User vs Post), **계층이 다른 것**(도메인 모델 vs DB 모델 vs 요청/응답 DTO)

---

## 2. 데이터베이스 계층 — 도메인 모델 vs DB 모델, 리포지토리 패턴

> ⚠️ **미리보기**: 이 주제는 책에서 뒤에 나오는 내용(SQLAlchemy/리포지토리 장).
> 현재 코드엔 아직 없고, "왜 이렇게 나누는지" 개념만 정리. 실제 구현은 책 진도에 맞춰서.

### 핵심 질문: `User` 도메인 모델을 그냥 DB에 저장하면 안 되나?

안 된다(고 책은 말한다). 도메인 모델과 DB 모델을 **분리**하는 게 클린 아키텍처의 핵심.

| | 도메인 모델 (`User`) | DB 모델 (`UserModel`) |
|---|---|---|
| 위치 | `domain/user.py` | `infra/db_models/user.py` |
| 정체 | 순수 파이썬 dataclass | SQLAlchemy ORM 클래스 (테이블 매핑) |
| 아는 것 | 비즈니스 규칙만 | 컬럼·타입·인덱스·관계 등 DB 사정 |
| 의존성 | 아무것도 import 안 함 | `sqlalchemy` import |

**왜 나누나?**
- 도메인이 SQLAlchemy에 묶이면 → DB를 바꾸거나 ORM을 바꿀 때 비즈니스 코드까지 다 흔들림.
- 도메인은 "유저란 무엇인가"에만 집중하고, DB 사정(컬럼 길이, 인덱스, nullable)은 infra가 떠안게 함.
- → **관심사 분리**. 테스트할 때 도메인은 DB 없이도 검증 가능.

### 3종 세트로 보는 User (계층마다 다른 User)

같은 "유저"라도 계층마다 모양이 다르다. 헷갈리기 쉬우니 정리:

| 클래스 | 계층 | 용도 | 예시 라이브러리 |
|---|---|---|---|
| `User` | domain | 비즈니스 핵심 | 순수 dataclass |
| `UserModel` | infra | DB 테이블 매핑 | SQLAlchemy |
| `CreateUserBody` / `UserResponse` | interface | API 요청·응답 검증 | Pydantic |

→ 그래서 **계층이 다른 클래스는 파일도 다른 폴더로 분리**한다(1장 응집도 기준).

### 리포지토리 패턴 — 의존성 역전(DIP)의 핵심

"저장/조회"라는 행위를 추상화. **인터페이스는 도메인에, 구현은 인프라에** 둔다.

```
domain/repository/user_repo.py     ← 인터페이스(추상). "save(user) 할 수 있다"는 약속만
        ↑ 의존
application/user_service.py        ← 이 약속에만 의존. 실제 DB는 모름
        ↑ 주입(DI)
infra/repository/user_repo.py      ← 진짜 구현. SQLAlchemy로 INSERT/SELECT
```

```python
# domain/repository/user_repo.py  (추상 — 도메인 계층)
from abc import ABCMeta, abstractmethod
from user.domain.user import User


class IUserRepository(metaclass=ABCMeta):
    @abstractmethod
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User: ...
```

```python
# infra/repository/user_repo.py  (구현 — 인프라 계층)
class UserRepository(IUserRepository):
    def save(self, user: User) -> None:
        # 1. 도메인 User → DB UserModel 변환(매핑)
        # 2. SQLAlchemy 세션으로 저장
        ...
```

**왜 이렇게 뒤집나 (의존성 역전)?**
- 보통은 "서비스 → DB 코드"로 의존하지만, 그러면 서비스가 DB에 종속됨.
- 인터페이스를 도메인 쪽에 두면 **화살표가 바깥(infra) → 안(domain)** 으로만 흐름.
- 서비스는 `IUserRepository`라는 *약속*만 알면 되고, 진짜 구현체는 실행 시점에 **주입(DI)** 받음.
- → DB를 PostgreSQL → 다른 걸로 바꿔도 서비스 코드는 그대로. 테스트 땐 가짜(mock) 리포지토리 끼우면 됨.

> **Spring 비교**: `interface UserRepository` + `@Repository` 구현 + 생성자 주입과 똑같은 그림.
> FastAPI는 `Depends()`로 주입한다.

### 매퍼 (domain ↔ DB model 변환)

도메인과 DB 모델이 분리됐으니, 둘 사이를 **변환**해주는 코드가 리포지토리 구현 안에 필요하다.

```python
# 저장할 때:  도메인 User → UserModel
user_model = UserModel(id=user.id, name=user.name, email=user.email, ...)

# 조회할 때:  UserModel → 도메인 User
return User(id=row.id, name=row.name, email=row.email, ...)
```

귀찮아 보여도 이게 **계층 간 격리**의 대가이자 목적. 도메인은 끝까지 SQLAlchemy를 모른 채로 산다.

### 이 프로젝트 DB 환경 메모

(상세 비교는 [rules.md](rules.md) 참고)

- 책은 **MySQL**, 이 프로젝트는 **PostgreSQL 18.3**.
- ORM은 **SQLAlchemy 2.0** (책과 일치).
- DB URL 형식: `postgresql+psycopg://...` (동기) 또는 `postgresql+asyncpg://...` (비동기).
- SQLAlchemy ORM 레벨에선 DB 차이가 대부분 추상화되지만, **Alembic 마이그레이션·raw SQL은 PostgreSQL 방언**으로 작성해야 함 (예: `AUTO_INCREMENT` ❌ → `SERIAL`/`IDENTITY`).

---

## 3. 추상 클래스(ABCMeta)로 리포지토리 인터페이스 — 의존성 역전(DIP)

> 책 **코드 3.3** — `user/domain/repository/user_repo.py`

```python
from abc import ABCMeta

class IUserRepository(metaclass=ABCMeta):
    pass
```

### `ABCMeta`가 뭔가

`abc` = **A**bstract **B**ase **C**lass 모듈. 파이썬엔 자바의 `interface` 키워드가 **없어서** 이걸로 인터페이스를 흉내 낸다.

```python
from abc import ABCMeta, abstractmethod

class IUserRepository(metaclass=ABCMeta):
    @abstractmethod                       # ← 책에서 곧 채워질 부분
    def save(self, user: User) -> None: ...

    @abstractmethod
    def find_by_email(self, email: str) -> User: ...
```

`metaclass=ABCMeta` + `@abstractmethod` 한 세트:
- 추상 메서드를 **다 구현 안 하면 인스턴스 생성 불가**(`TypeError`)
- "이 메서드들을 반드시 구현하라"고 **강제**하는 장치

| Python | Java |
|---|---|
| `IUserRepository(metaclass=ABCMeta)` | `interface IUserRepository` |
| `@abstractmethod def save(...)` | 인터페이스 메서드 선언 |

### ⚠️ 지금 `pass`는 아직 강제 안 함 (마커일 뿐)

`@abstractmethod`가 하나도 없고 `pass`만 있으면 **인스턴스화도 그냥 된다**(안 막힘). 지금은 "여기가 인터페이스다"라는 **표시**일 뿐. 진짜 강제력은 책이 `@abstractmethod` 메서드를 채울 때 생긴다. (책이 뼈대부터 단계적으로 보여주는 것)

### `metaclass=ABCMeta` vs `ABC` — 같음

```python
from abc import ABC
class IUserRepository(ABC):     # 위와 100% 동일. 책은 명시적인 쪽 선택
    ...
```

### 이름 앞의 `I`

문법 아님, **컨벤션**. "구현체 아니라 인터페이스(약속)"임을 이름으로 표시 (자바/C#의 `IList`, `IRepository` 관습).

### 핵심 — "의존성이 역전돼 있다"의 의미

**두 가지 방향을 분리**하면 이해된다:

| 방향 | 흐름 |
|---|---|
| **런타임 호출** (실행 시) | 서비스 → 구현체 ("저장해!"라고 호출) |
| **소스 의존** (import 관계) | 서비스 → 추상(domain) ← 구현체(infra) |

DIP 없이 평범하게 (❌):
```
application(고수준)  ───→  infra(저수준, DB코드)
                    의존    # 고수준이 저수준에 묶임 → DB 바꾸면 서비스도 흔들림
```

리포지토리 인터페이스를 domain에 두면 (✅):
```
application(고수준)  ──→  IUserRepository(추상, domain)  ←──  infra(구현)
                    의존                                의존
                                              # infra 화살표가 위로 꺾임 = 역전
```

- 서비스는 **약속(추상)** 만 import, 진짜 구현체는 모름.
- 구현체(infra)가 거꾸로 domain의 추상을 바라보며 구현.
- **런타임엔 서비스→infra 호출(위→아래)**, **소스 의존은 infra→domain(아래→위)**. 호출 방향과 의존 방향이 **반대** = **의존성 역전(DIP)**.

책 문장 해석:
- *"도메인의 이 모듈은 어느 계층에서나 사용 가능"* → domain은 가장 안쪽이라 누구나 의존 OK.
- *"인프라보다 고수준(=application)에서 쓸 때 의존성이 역전"* → 서비스가 이 추상에 의존함으로써, 원래 infra로 향했을 화살표가 뒤집힌다.

> **Spring 비교**: `interface UserRepository`(도메인) + `@Repository UserRepositoryImpl`(인프라) + 서비스는 인터페이스에 `@Autowired`. FastAPI는 `Depends()`로 구현체 주입.

---

## 4. UUID vs ULID — 엔티티 id 생성

> 책에서 User `id`를 만들 때 등장. **`py-ulid` 설치 완료**, `user_service.py`에서 사용 중.

### 왜 필요한가 — id를 누가 만드나

| 방식 | 누가 만드나 | 클린 아키텍처 궁합 |
|---|---|---|
| DB auto-increment (1,2,3…) | DB가 INSERT 시 | ❌ 저장 전엔 id 없음, DB에 종속 |
| **UUID** | 앱이 미리 생성 | ✅ DB 없이 id 확보 |
| **ULID** | 앱이 미리 생성 | ✅✅ UUID 장점 + 시간 정렬 |

**핵심**: 클린 아키텍처는 **id를 애플리케이션 계층에서 직접 생성**한다. 저장 전에 이미 `User`가 자기 id를 가져야 도메인이 DB에 안 묶임. UUID/ULID는 DB 왕복 없이 유일 id를 만들 수 있어 이걸 가능케 함. (Spring의 DB `@GeneratedValue` 대신 앱 생성 방식)

### UUID vs ULID 비교

| | UUID (v4) | ULID |
|---|---|---|
| 크기 | 128비트 | 128비트 (동일) |
| 문자열 길이 | 36자 (하이픈 포함) | **26자** |
| 예시 | `550e8400-e29b-41d4-a716-446655440000` | `01ARZ3NDEKTSV4RRFFQ69G5FAV` |
| 인코딩 | 16진수 + 하이픈 | Crockford Base32 (하이픈 없음) |
| 구성 | v4는 완전 랜덤 | **48비트 타임스탬프(ms) + 80비트 랜덤** |
| **시간순 정렬** | ❌ (랜덤) | ✅ **생성 시각 순 정렬됨** |

### ULID 핵심 장점 — 정렬 가능

앞부분이 생성 시각(ms)이라 문자열을 그냥 정렬하면 **만든 순서대로** 줄선다.

```
01ARZ3NDEK...  ← 먼저 생성
01ARZ3NDFM...  ← 나중 (앞 타임스탬프가 큼)
```

→ **DB 인덱스 성능**: UUID4는 랜덤이라 B-tree 여기저기 꽂혀 단편화. ULID는 맨 뒤에 차곡차곡 쌓여 인덱스 지역성↑. 정렬·페이징도 id만으로 가능.

### 코드 (책 방식 — `py-ulid`)

```python
from ulid import ULID

class UserService:
    def __init__(self):
        self.ulid = ULID()

    def create_user(self, name, email, password):
        user = User(
            id=self.ulid.generate(),   # ← py-ulid: .generate()가 26자 ULID 문자열 반환
            name=name, email=email, password=password,
            created_at=now, updated_at=now,
        )
        self.user_repo.save(user)
        return user
```

설치:
```bash
cd fastapi-ca            # poetry는 반드시 여기서 (git 루트 ❌)
poetry add py-ulid       # 이 책/프로젝트가 쓰는 패키지 (이미 설치됨)
```

⚠️ **ULID 패키지가 여러 개라 헷갈림** — 셋 다 import 이름이 `ulid`로 같아서 충돌. **하나만 설치**. 이 프로젝트는 `py-ulid`.

| 패키지 (PyPI) | import | id 생성 API |
|---|---|---|
| **`py-ulid`** ← 이 프로젝트 | `from ulid import ULID` | `ULID().generate()` → 26자 str |
| `python-ulid` | `from ulid import ULID` | `str(ULID())` |
| `ulid-py` | `from ulid import ULID` | `ulid.new()` 계열 |

> 📝 (정정 메모) 처음엔 `python-ulid`로 안내했으나, 책 코드의 `.generate()` API는 **`py-ulid`** 것이다. 설치된 패키지로 직접 확인함.

### 참고 — UUIDv7 (요즘 표준)

2024년 RFC 9562에 추가. **UUID 포맷 그대로 + 앞부분 타임스탬프** → ULID처럼 시간 정렬. "UUID 호환 + ULID 장점"이라 신규 프로젝트 기본이 되는 추세. **단 책은 ULID 기준** → 학습은 책 따르고 "요즘 UUIDv7도 있다"만 인지.

### 우리 환경 메모 (PostgreSQL)

- 책 MySQL(VARCHAR 저장) ↔ 우리 PostgreSQL.
- ULID는 `CHAR(26)` 문자열 저장이 단순. (128비트라 네이티브 `uuid` 타입에도 저장 가능)
- 학습 단계는 책처럼 **문자열 컬럼**으로. 도달 시 컬럼 타입 확정.
