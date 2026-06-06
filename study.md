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
| DB | **MySQL** | MySQL | 일치 (책과 동일) |
| 패키지 관리 | Poetry | Poetry | 일치 |

**⚠️ 명령 실행 위치**: 파이썬 앱은 git 루트가 아니라 **`fastapi-ca/`** 안에 있다. `poetry add` 등은 반드시 거기서.

```
FastApiStudy/          ← git 루트 (notes.md, rules.md, study.md). pyproject.toml 없음 ❌
└── fastapi-ca/        ← 실제 앱. poetry 명령은 여기서 ✅
    ├── pyproject.toml
    ├── main.py
    └── user/{domain, application, infra, interface}
```

> 상세 환경·설치 시행착오는 [notes.md](notes.md), 스택 비교/방언 주의점은 [rules.md](rules.md), **실행·API 테스트 명령은 [run.md](run.md)** 참고.

## 목차

1. [도메인 모델과 값 객체](#1-도메인-모델과-값-객체)
2. [데이터베이스 계층 — 도메인 모델 vs DB 모델, 리포지토리 패턴](#2-데이터베이스-계층--도메인-모델-vs-db-모델-리포지토리-패턴)
3. [추상 클래스(ABCMeta)로 리포지토리 인터페이스 — 의존성 역전(DIP)](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip)
4. [UUID vs ULID — 엔티티 id 생성](#4-uuid-vs-ulid--엔티티-id-생성)
5. [타입 힌트 — `: str`, `-> User` (자바와 결정적 차이)](#5-타입-힌트--str---user-자바와-결정적-차이)
6. [밑줄 `_` `__` — 네이밍 규칙 (private은 강제 아님)](#6-밑줄-__--네이밍-규칙-private은-강제-아님)
7. [`self`와 키워드 인자 (위치 인자 vs 키워드 인자)](#7-self와-키워드-인자-위치-인자-vs-키워드-인자)
8. [인스턴스 변수 `self.x` — 속성 vs 메서드](#8-인스턴스-변수-selfx--속성-vs-메서드)
9. [인스턴스 변수 vs 클래스 변수(static) vs 싱글톤](#9-인스턴스-변수-vs-클래스-변수static-vs-싱글톤)
10. [데코레이터(`@`) vs 어노테이션 — 닮았지만 다름](#10-데코레이터-vs-어노테이션--닮았지만-다름)
11. [Pydantic — 타입 힌트로 검증·직렬화 (interface 계층 DTO)](#11-pydantic--타입-힌트로-검증직렬화-interface-계층-dto)
12. [SQLAlchemy — ORM (DB 모델·엔진·세션)](#12-sqlalchemy--orm-db-모델엔진세션)
13. [엔티티(domain) vs 모델(DB) — Spring 통합 vs 클린 분리](#13-엔티티domain-vs-모델db--spring-통합-vs-클린-분리)
14. [with 문 (컨텍스트 매니저)](#14-with-문-컨텍스트-매니저)
15. [회원가입 e2e 디버깅 — 만난 함정들](#15-회원가입-e2e-디버깅--만난-함정들)
16. [의존성 주입(DI) — 객체를 밖에서 주입](#16-의존성-주입di--객체를-밖에서-주입)
17. [비동기 프로그래밍 — 동시성 vs 병렬성, async/await](#17-비동기-프로그래밍--동시성-vs-병렬성-asyncawait)
18. [JWT (JSON Web Token) — 인증/인가](#18-jwt-json-web-token--인증인가)

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
- → DB(MySQL)를 다른 걸로 바꿔도 서비스 코드는 그대로. 테스트 땐 가짜(mock) 리포지토리 끼우면 됨.

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

- **MySQL** 사용 (책과 동일). ORM은 **SQLAlchemy 2.0**.
- DB URL 형식: `mysql+pymysql://user:pass@localhost:3306/db`.
- ORM 레벨에선 DB 차이가 추상화되지만, **Alembic 마이그레이션·raw SQL은 MySQL 방언**으로 작성 (자동증가 `AUTO_INCREMENT`, 식별자 백틱 `` ` ``).

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

### 두 개의 `user_repo.py` — 왜 domain/infra 양쪽에?

같은 파일명이지만 **계층이 달라서** 역할이 정반대다. (DIP의 실물)

| | domain/repository/user_repo.py | infra/repository/user_repo.py |
|---|---|---|
| 클래스 | `IUserRepository` (추상) | `UserRepository(IUserRepository)` (구현) |
| 정체 | **계약/약속** — "무엇을 할 수 있나" | **이행** — "실제로 어떻게 하나" |
| 내용 | `@abstractmethod def save(...)` 선언만 | SQLAlchemy로 진짜 INSERT/SELECT |
| DB 아는가 | ❌ 순수 | ✅ DB 세부사항 앎 |
| import | `abc`, 도메인 모델 | sqlalchemy, db_model, + domain의 추상 |

```python
# domain/repository/user_repo.py  — 약속 (DB 모름)
from abc import ABCMeta, abstractmethod
from user.domain.user import User

class IUserRepository(metaclass=ABCMeta):
    @abstractmethod
    def save(self, user: User):      # "save 할 수 있다"는 명세만
        raise NotImplementedError
```
```python
# infra/repository/user_repo.py  — 이행 (DB 안다)
from user.domain.repository.user_repo import IUserRepository

class UserRepository(IUserRepository):   # 추상을 상속해 진짜로 구현
    def save(self, user: User):
        ...  # ← 책에서 SQLAlchemy로 채울 부분
```

**왜 둘로 쪼개나 (4가지):**
1. **의존성 역전** — 서비스는 추상(domain)에만 의존, infra는 추상을 따름. 화살표가 안쪽으로.
2. **교체 가능** — DB 바꿔도 domain/service 그대로, infra만 새로.
3. **테스트** — 진짜 DB 대신 가짜 구현(`FakeUserRepository`) 끼움.
4. **도메인 순수성** — domain이 끝까지 SQLAlchemy를 import 안 함.

```
application/user_service.py  ─ import ─→ IUserRepository  (domain 추상에 의존)
domain/repository/user_repo.py  (추상)  ←──────────────────┐  둘 다 추상을 바라봄
infra/repository/user_repo.py   (구현)  ─ import IUserRepository ┘  (화살표 위로 = 역전)
```

> ⚠️ **현재 상태**: infra `UserRepository`가 `save`를 아직 `pass`로 둬서 `@abstractmethod` 미구현 → `UserRepository()` 시 `TypeError`(추상 클래스 인스턴스화 불가). `user_service.py`는 아직 실행 불가. 책에서 infra `save`를 SQLAlchemy로 구현하면 해결.
>
> 흔한 실수 2개(직접 겪음): ① domain에서 `@abstractmethod` 쓰려면 `from abc import ABCMeta, abstractmethod`로 **둘 다 import**. ② 구현 클래스명 `UserRepository` 철자 — 서비스의 import와 정확히 일치해야 함.

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

### 환경 메모 (MySQL)

- **MySQL** 사용 (책과 동일).
- ULID는 `VARCHAR(26)`/`CHAR(26)` 문자열 컬럼으로 저장이 단순.
- 학습 단계는 책처럼 **문자열 컬럼**으로. 도달 시 컬럼 타입 확정.

---

## 5. 타입 힌트 — `: str`, `-> User` (자바와 결정적 차이)

### 함수 시그니처 뜯어보기

```python
def find_by_email(self, email: str) -> User:
```

| 조각 | 의미 | 자바 대응 |
|---|---|---|
| `def` | 함수 정의 키워드 | (자바는 리턴타입+이름이 그 역할) |
| `self` | 인스턴스 자신 | 자바의 **암묵적 `this`를 명시적으로** 받음 |
| `email: str` | 파라미터 + 타입 힌트 | `String email` |
| `-> User` | **반환 타입 힌트** | 메서드 이름 앞의 `User` |
| `:` | 본문 시작 | `{` |

```java
// Java
public User findByEmail(String email) { ... }
```
```python
# Python — 같은 의미
def find_by_email(self, email: str) -> User: ...
```

### `-> User` = 반환 타입 힌트

화살표 `->` 뒤에 반환 타입을 쓴다. "이 함수는 `User`를 돌려준다"는 **표시**.

### 핵심 — 강제되는가? (자바와 결정적 차이)

**답: "User 반환하겠다 선언했지만, 파이썬이 강제하진 않는다."**

| | 자바 | 파이썬 |
|---|---|---|
| 반환 타입 | **강제됨** (컴파일러 체크) | **강제 안 됨** — 그냥 힌트 |
| 다른 타입 반환 시 | **컴파일 에러** ❌ | 런타임 **그냥 통과** 😐 |
| 누가 체크 | 컴파일러 | mypy/Pylance(IDE)가 **경고만** |

- 파이썬은 힌트를 `__annotations__`에 저장만 하고 **실행 시 무시**.
- 그래서 `-> User`인데 `raise NotImplementedError`로 아무것도 안 돌려줘도 런타임 에러 없음.
- 힌트 = **사람·IDE·타입체커용 메모**. 런타임 규칙 아님. (생략도 가능하지만 [rules.md](rules.md) 방침상 적극 사용)

> ⚠️ **FastAPI 예외**: 라우터 함수의 파라미터/응답 타입 힌트는 FastAPI+Pydantic이 **런타임에 실제로 검증·변환**한다. 단 지금 같은 평범한 클래스 메서드에선 그냥 힌트.

### 힌트는 전부 생략 가능 + "타입" vs "값"

```python
def find_by_email(self, email: str) -> User: ...   # ① 다 붙임 (권장)
def find_by_email(self, email: str): ...            # ② 반환 타입 생략 — OK
def find_by_email(self, email): ...                 # ③ 파라미터까지 생략 — OK
```
셋 다 문법 정상, 런타임 동작 동일.

반환 **타입 힌트**와 반환 **값**은 별개:

| | 의무? | 안 쓰면 |
|---|---|---|
| 반환 타입 힌트 `-> User` | ❌ 선택 | 표시만 없음 |
| 반환 값 `return ...` | ❌ 선택 | 자동으로 **`None` 반환** |

> **자바 비교**: 자바는 리턴타입 자리가 **필수**(값 없으면 `void`라도 명시). 파이썬은 그 자리를 통째로 비워도 되고, "값 안 돌려줌"은 `return` 생략(= `None`)으로 끝.

---

## 6. 밑줄 `_` `__` — 네이밍 규칙 (private은 강제 아님)

밑줄은 **개수·위치에 따라 의미가 다르다.**

| 패턴 | 예 | 의미 |
|---|---|---|
| `__이름__` (앞뒤 2개) | `__init__` | **던더**. 파이썬 예약 특수 메서드 |
| `_이름` (앞 1개) | `_pwd_context`, `_user` | "내부용(private)" **관례** (강제 X) |
| `이름_` (뒤 1개) | `id_`, `class_` | 예약어 충돌 회피 |
| `__이름` (앞 2개만) | `__secret` | **네임 맹글링** (상속 충돌 방지) |
| `_` (단독) | `for _ in range(3)` | 안 쓰는 값 버림 |

### `__init__` — 던더 (앞뒤 2개)

**파이썬이 예약한 특수 메서드**. `__init__`은 **생성자** — `Crypto()`로 객체 만들 때 자동 호출(자바 `public Crypto(){}`). 다른 던더: `__str__`(toString), `__eq__`(equals), `__len__`. ⚠️ 던더는 새로 발명 금지, 정해진 것만 구현.

### `_이름` — 앞 1개 ("내부용" 관례)

"외부에서 직접 쓰지 마"라는 신호. **강제 아님** — 접근하면 됨.
```python
self._pwd_context = CryptContext(...)   # 내부용 표시일 뿐
```

### `이름_` — 뒤 1개 (예약어 회피)

```python
def f(class_):   # 'class'는 예약어 → class_
```

### `__이름` — 앞 2개만 (네임 맹글링)

자바 `private`에 가장 가깝지만 목적은 "상속 충돌 방지". 파이썬이 이름을 `_클래스명__이름`으로 바꿔치기.
```python
class A:
    def __init__(self):
        self.__secret = 1      # 실제 저장: self._A__secret
a = A()
a.__secret      # ❌ AttributeError
a._A__secret    # ✅ 1  ← 우회 가능 (진짜 private 아님)
```

### `_` 단독 — 버리는 값

```python
for _ in range(3): ...      # 인덱스 안 씀
name, _ = ("kim", 30)       # 두 번째 값 버림
```

### 핵심 — 자바와의 차이

| | 자바 | 파이썬 |
|---|---|---|
| 접근 제어 | `private`/`protected`/`public` 키워드 | 키워드 **없음** — 밑줄 관례뿐 |
| 진짜 막히나 | ✅ 컴파일 에러 | ❌ 다 접근 가능 (`__`도 우회) |
| 철학 | 컴파일러 강제 | **"다 큰 어른이니 알아서"** (관례) |

> 결론: 거의 다 **관례(네이밍 규칙)**. 던더(`__init__`)만 파이썬이 실제 의미를 부여하고, `_`/`__`로 private 표현하는 건 강제가 아니라 약속.

---

## 7. `self`와 키워드 인자 (위치 인자 vs 키워드 인자)

### `self` — 관례 (키워드 아님)

파이썬은 메서드 호출 시 **인스턴스 자신을 첫 인자로 자동 전달**한다. 그걸 받는 첫 파라미터를 관례로 `self`라 부를 뿐 — `this`로 바꿔도 작동(아무도 안 그럼).

```python
class Crypto:
    def encrypt(self, secret):
        return self.pwd_context.hash(secret)

c = Crypto()
c.encrypt("1234")     # 파이썬이 c를 self로 자동 전달 → 실제론 encrypt(c, "1234")
```

> **자바 차이**: 자바 `this`는 **키워드라 자동**(안 적음). 파이썬은 `this`가 없어 **첫 파라미터로 직접 받음** → 그래서 메서드마다 `self`가 보인다.

**본문에서 안 써도 첫 파라미터로 무조건 선언**해야 한다(파이썬이 인스턴스를 자동 전달하므로 받을 자리 필요). 빠뜨리면 `TypeError: ... takes 1 positional argument but 2 were given`.

"거의" 무조건인 이유 — 예외 2개:

| 종류 | 첫 파라미터 | 받는 것 |
|---|---|---|
| 일반 메서드 (대부분) | `self` | 인스턴스 (필수) |
| `@staticmethod` | (없음) | 안 받음 (인스턴스 불필요한 유틸) |
| `@classmethod` | `cls` | 인스턴스 대신 **클래스** |

### 키워드 인자 — `이름=값` (자바엔 없는 것)

```python
CryptContext(schemes=["bcrypt"], deprecated="auto")   # 키워드 인자
CryptContext(["bcrypt"], "auto")                       # 위치 인자 (순서로만)
```

| | 위치 인자 | 키워드 인자 |
|---|---|---|
| 형태 | 값만, 순서대로 | `이름=값` |
| 순서 | 지켜야 함 | 상관없음 |
| 가독성 | 뭐가 뭔지 모름 | 이름이 보임 |
| 일부만 지정 | 어려움 | 기본값 있는 건 생략 가능 |

혼합 가능하지만 **위치가 먼저, 키워드가 나중**:
```python
CryptContext(["bcrypt"], deprecated="auto")   # ✅
CryptContext(schemes=["bcrypt"], "auto")      # ❌ SyntaxError
```

> **자바 차이**: 자바는 **위치 인자만** 있어 이름 붙여 못 넘김 → 빌더 패턴(`.schemes(...).deprecated(...)`)으로 흉내. 파이썬은 `이름=값`을 문법으로 제공.

### 언패킹 `*` `**` — 펼치기 / 모으기

`UserVO(**row_to_dict(user))`의 `**`는 **딕셔너리를 키워드 인자로 펼치는** 것:
```python
d = {"id": "x", "name": "kim", "email": "a@b.com"}
UserVO(**d)              # ≡ UserVO(id="x", name="kim", email="a@b.com")
```

| 문맥 | `*` (시퀀스) | `**` (딕셔너리) |
|---|---|---|
| 호출 시 (펼치기) | `f(*[1,2])` → `f(1, 2)` 위치 인자 | `f(**{"a":1})` → `f(a=1)` 키워드 인자 |
| 정의 시 (모으기) | `def f(*args)` → 나머지 위치 인자를 튜플로 | `def f(**kwargs)` → 나머지 키워드 인자를 딕셔너리로 |

⚠️ `**dict`로 호출하려면 **dict의 key가 파라미터명과 정확히 일치**해야 함 (없는 key → `unexpected keyword argument`, 빠진 필수 인자 → `missing argument`). → `row_to_dict`는 `UserVO` 필드명(id, name, email, …)과 똑같은 key를 돌려줘야 함.

> 자바엔 `**` 언패킹 없음(키워드 인자 자체가 없으니). varargs `f(T...)`가 `*args`와 비슷한 정도.

### 리스트 컴프리헨션 `[식 for x in 반복]`

`return [UserVO(**row_to_dict(user)) for user in users]` 한 줄에 문법 **두 개**가 겹쳐 있음.

**① 컴프리헨션** = for문 + append를 한 줄로:
```python
# 컴프리헨션
[UserVO(**row_to_dict(user)) for user in users]

# 똑같은 풀어쓰기
result = []
for user in users:
    result.append(UserVO(**row_to_dict(user)))
```
`[ 식 for 요소 in 반복대상 ]` = "반복대상을 돌며 각 요소를 `식`으로 변환해 **리스트로 모은다**".

**② 그 안의 변환 단계** (user 하나):
```python
user                  # DB 행 (User 모델)
row_to_dict(user)     # → {"id":..., "name":..., ...}  (dict)
UserVO(**...)         # → UserVO(id=..., name=...)  (** 언패킹, 위 절)
```

→ 최종 반환은 **`list[UserVO]`** (도메인 객체 리스트). dict는 중간 단계일 뿐 dict를 반환하는 게 아님.

| | Python | Java/Spring |
|---|---|---|
| 변환+수집 | `[f(x) for x in xs]` | `xs.stream().map(this::f).toList()` |
| dict→생성자 | `UserVO(**d)` | (대응 없음, 필드 일일이) |

> 변형: `{k: v for ...}`(딕셔너리), `{x for ...}`(셋), `(x for ...)`(제너레이터=지연 평가).

> 📌 추상 메서드(`find_by_email`)가 파라미터를 본문에서 안 쓰는 건 [3번](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip) 참고 — "약속(시그니처)"만 박는 자리라서. 이건 자바 `interface` 메서드와 같음(자바에도 있음).

---

## 8. 인스턴스 변수 `self.x` — 속성 vs 메서드

예시 ([util/crypto.py](fastapi-ca/util/crypto.py)):
```python
class Crypto:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # 필드 생성
    def encrypt(self, secret):
        return self.pwd_context.hash(secret)        # 꺼내 씀
    def verify(self, secret, hash):
        return self.pwd_context.verify(secret, hash)
```

### `pwd_context`는 변수명(내가 지음), `CryptContext`가 라이브러리

- `pwd_context` = **내가 정한 이름**("password context" 약자). 우변 `CryptContext(...)`가 `passlib` 라이브러리 것.
- = "passlib `CryptContext` 객체를 만들어 `pwd_context`라는 이름표를 붙인 것."
- `CryptContext`: 비번 해싱 도구. `.hash()` 해시화, `.verify()` 일치 확인(True/False).

### `self.x = 값` = 인스턴스 변수(필드) 만들기

`__init__`에서 `self.X = 값` → 이 객체에 X 필드를 붙임. 다른 메서드가 `self.X`로 꺼내 씀.

> **자바 비교**: `this.pwdContext = new CryptContext(...)` 생성자 필드 초기화와 동일.
> **차이**: 자바는 클래스 상단에 `private CryptContext pwdContext;` 미리 **선언**. 파이썬은 선언 없이 **`self.X =` 처음 대입하는 순간 필드 생성**.

⚠️ 담긴 건 **함수가 아니라 객체**(CryptContext 인스턴스). 그래서 "함수변수"가 아니라 인스턴스 변수.

### 왜 `__init__`에 담나 — 한 번 생성 vs 매번 생성

```python
# 실제: 1번 만들고 재사용
self.pwd_context = CryptContext(...)   # __init__에서 1번
... self.pwd_context.hash(secret)      # 매 호출 같은 객체 재사용

# 인라인: 호출마다 새 객체 (결과는 같지만 낭비)
... CryptContext(...).hash(secret)     # 매번 새로 생성 ❌
```

결과(해시값)는 같아도 동작이 다르다. `__init__`에 담는 이유: ① 설정 객체를 **1번만 생성**해 재사용(효율), ② 설정을 **한 곳에서 관리**(`schemes` 바꿀 때 한 줄만). → 도구를 서랍에 사두고 꺼내 쓰기 vs 쓸 때마다 새로 사기.

### 속성 vs 메서드 (괄호 유무) — `c.pwd_context()`는 ❌

`pwd_context`는 **메서드가 아니라 객체를 담은 속성**. 괄호 붙여 호출 불가.

| | 정체 | 호출 |
|---|---|---|
| `c.pwd_context` | 속성 (객체 담음) | 괄호 ❌ (`c.pwd_context()` → TypeError) |
| `c.encrypt(...)` | 메서드 (함수) | 괄호 ⭕ |

```python
crypto = Crypto()
hashed = crypto.encrypt("1234")          # 공개 API. 내부적으로 self.pwd_context.hash(...)
ok     = crypto.verify("1234", hashed)   # → True/False
```

→ `pwd_context`는 **내부 도구**, 바깥엔 `encrypt`/`verify`만 노출. (내부용이면 [6번](#6-밑줄-__--네이밍-규칙-private은-강제-아님)처럼 `self._pwd_context`로 밑줄 가능)

---

## 9. 인스턴스 변수 vs 클래스 변수(static) vs 싱글톤

`self.pwd_context = CryptContext(...)`는 **싱글톤도 static도 아니다.** 그냥 인스턴스 변수.

```python
c1, c2 = Crypto(), Crypto()
c1.pwd_context is c2.pwd_context   # False — 인스턴스마다 따로 생김
```
> "한 번 생성"은 **인스턴스당 1개**(메서드 호출마다 새로 안 만듦)지, **전역 1개(싱글톤)**가 아니다. 헷갈리기 쉬움.

### 자바 ↔ 파이썬 대응

| 개념 | 자바 | 파이썬 | 지금 `Crypto`? |
|---|---|---|---|
| 인스턴스 변수 | `this.x` | `self.x` (`__init__` 안) | ✅ 이거임 |
| static 변수 | `static X` | 클래스 변수 (클래스 본문 `x =`) | ❌ |
| static 메서드 | `static m()` | `@staticmethod` | ❌ |
| 싱글톤 | private 생성자 + `getInstance()` | 모듈 레벨 인스턴스 | ❌ |

### static = 클래스 변수 (위치가 의미를 바꿈)

```python
class Crypto:
    pwd_context = CryptContext(...)    # 클래스 본문 → 모든 인스턴스 공유 (static스러움)

Crypto().pwd_context is Crypto().pwd_context   # True (공유)
```
- `self.pwd_context` (`__init__` 안) → **인스턴스마다 따로**
- `pwd_context` (클래스 본문) → **공유** (자바 static에 가까움)

### 싱글톤 = 전역에 인스턴스 1개

```java
// Java: private 생성자 + static getInstance()
private static final Crypto INSTANCE = new Crypto();
```
```python
# Python: 보통 모듈 레벨 인스턴스로 끝 (모듈은 최초 import 때 1번만 실행·캐시)
# util/crypto.py
crypto = Crypto()
# 사용처: from util.crypto import crypto  → 같은 객체 공유 = 사실상 싱글톤
```

> 지금 `Crypto`는 **셋 다 아닌 일반 클래스.** 다만 책/실무에선 한 번 만들어 재사용(DI·모듈 인스턴스)해 *결과적으로* 싱글톤처럼 쓰는 경우 많음 — 그건 **쓰는 쪽 선택**이지 클래스가 강제하는 게 아님.

---

## 10. 데코레이터(`@`) vs 어노테이션 — 닮았지만 다름

`@router.post(...)`(FastAPI) ↔ `@PostMapping`(Spring). 겉모습(@)과 역할(라우트 선언)은 닮았지만 **작동 방식이 근본적으로 다름.**

| | Python 데코레이터 | Java 어노테이션 |
|---|---|---|
| 본질 | 함수를 **감싸 바꾸는 실행 코드** | **메타데이터(꼬리표)** |
| 스스로 동작? | ✅ 정의 시점 **즉시 실행** | ❌ 혼자선 아무것도 안 함 |
| 누가 처리 | 데코레이터 자신 | 프레임워크가 **리플렉션**으로 읽음 |
| `@x` + `f` | `f = x(f)` (교체) | f에 x 태그 부착 |

> 비유: 어노테이션 = **스티커(라벨)** — 자체론 아무 일 안 함, 누가 읽고 행동. 데코레이터 = **포장지로 감싸기** — 감싸는 순간 실제로 달라짐.

### 데코레이터는 진짜 코드 (`@x` = `f = x(f)`)

```python
def log(func):
    def wrapper(*args, **kwargs):
        print("전"); r = func(*args, **kwargs); print("후")
        return r
    return wrapper

@log
def hello(): print("hello")
# ↑ 사실: hello = log(hello)
hello()   # 출력: 전 / hello / 후  ← log가 hello를 실제로 감쌌음
```

```python
@router.post("", status_code=201)
def create_user(): ...
# = create_user = router.post("", status_code=201)(create_user)
#   router.post(...)가 함수를 라우트에 등록하고 감싼 함수를 돌려줌 (정의 시 실행됨)
```

### Spring이라면 (어노테이션 = 수동 데이터)

```java
@PostMapping
@ResponseStatus(HttpStatus.CREATED)   // status_code=201 대응
public String createUser() { return "user created"; }
```
`@PostMapping`은 **그냥 꼬리표** — 스스로 아무것도 안 하고, Spring이 시작 시 **리플렉션으로 읽어** 라우팅 등록. 처리 주체가 따로.

> 정리: **데코레이터 = 능동적 코드(함수를 감쌈), 어노테이션 = 수동적 메타데이터(읽혀야 의미).** 웹 프레임워크에서 같은 "라우트 선언" 자리를 차지해 비슷해 보일 뿐.

---

## 11. Pydantic — 타입 힌트로 검증·직렬화 (interface 계층 DTO)

> 이 프로젝트: **Pydantic 2.13 (v2)**. 책(0.111)도 v2. 아래는 v2 문법.

### 정체 — "타입 힌트를 실제로 강제하는 도구"

[섹션 5](#5-타입-힌트--str---user-자바와-결정적-차이)에서 "타입 힌트는 보통 런타임에 강제 안 됨"이라 했는데, **Pydantic이 그 힌트를 런타임에 검증·변환하는 라이브러리**. FastAPI의 요청/응답 처리 엔진. (그때 말한 "FastAPI 예외"의 정체)

### `BaseModel` — 스키마 정의

```python
from pydantic import BaseModel, Field

class CreateUserBody(BaseModel):
    name: str = Field(min_length=2, max_length=32)
    email: str = Field(max_length=64)          # EmailStr 쓰려면 pydantic[email] 설치
    password: str = Field(min_length=8, max_length=32)
```
`BaseModel` 상속 → 자동으로 검증·파싱·직렬화. dict/JSON을 객체로 바꾸며 타입 검사, 안 맞으면 `ValidationError`.

### FastAPI 자동 검증 — 타입 힌트만 붙이면 끝

```python
@router.post("", status_code=201)
def create_user(user: CreateUserBody):   # ← 이 힌트만으로 자동 검증
    ...
```
들어온 JSON을 `CreateUserBody`로 파싱+검증, 틀리면 **자동 422 응답**. `Field` 제약은 Bean Validation(`@Size`, `@NotNull`)에 해당.

### `@dataclass`(도메인)와 뭐가 다른가

| | `@dataclass` (domain `User`) | Pydantic `BaseModel` (interface DTO) |
|---|---|---|
| 목적 | 순수 데이터 담기 | **검증 + 직렬화** |
| 타입 강제 | ❌ (그냥 힌트) | ✅ 런타임 검증 |
| 의존성 | 표준 라이브러리만 | `pydantic` |
| 위치 | domain | interface |

### 클린 아키텍처에서의 위치 — interface 계층

Pydantic 모델 = **요청/응답 DTO** = `interface/` 계층. [섹션 2의 "3종 세트"](#2-데이터베이스-계층--도메인-모델-vs-db-모델-리포지토리-패턴) 기억:

| 클래스 | 계층 | 도구 |
|---|---|---|
| `User` | domain | `@dataclass` |
| `UserModel` | infra | SQLAlchemy |
| `CreateUserBody`/`UserResponse` | **interface** | **Pydantic** |

→ 도메인 `User`와 **분리**한다. 이유: 도메인이 웹/검증 라이브러리(Pydantic)에 묶이지 않게. (interface DTO ↔ domain 엔티티 변환은 컨트롤러/서비스에서)

### Spring 비교

| 역할 | Spring | Pydantic |
|---|---|---|
| JSON ↔ 객체 | Jackson | Pydantic (둘 다 내장) |
| 검증 | Hibernate Validator(`@Valid`, `@Size`) | `Field(...)` 제약 |
| 요청 바디 | `@RequestBody @Valid Dto` | `def f(body: Dto)` |

> Pydantic은 **Jackson(직렬화) + Validator(검증)를 하나로 합친 것**. Spring은 둘이 분리돼 있는데 Pydantic은 한 클래스에서 다 함.

### v2 자주 쓰는 것 (책에서 등장 시)

| v2 | v1(구버전) | 용도 |
|---|---|---|
| `model.model_dump()` | `.dict()` | 객체 → dict |
| `Model.model_validate(obj)` | `.from_orm()`/`.parse_obj()` | dict/ORM → 객체 |
| `model_config = ConfigDict(from_attributes=True)` | `class Config: orm_mode=True` | ORM 객체에서 읽기 허용 |

### 왜 Pydantic을 쓰나 — 장점 4가지 (5.5)

interface 계층은 **외부와 소통**하는 역할 — 외부 데이터를 내부 형식으로 가공해 전달하고, 결과를 다시 가공해 내보냄. 그 검증·가공의 핵심 도구가 Pydantic.

1. **골치 아플 일 없음** — 새 스키마 정의 언어(JSON Schema 등) 따로 안 배워도 됨. **파이썬 타입 힌트만 알면** Pydantic 쓸 줄 아는 것.
2. **IDE·린터·직관에 잘 맞음** — Pydantic 데이터는 결국 **내가 정의한 클래스의 인스턴스**일 뿐 → 자동완성·린팅·Mypy·내 직관이 전부 *검증된 데이터* 위에서 작동.
3. **복잡한 구조도 검사** — 모델을 계층적으로 중첩(모델 안에 모델), `typing`의 `list`/`dict` 활용. 깊게 중첩된 JSON도 검증 + **JSON Schema로 자동 문서화**(= `/docs`).
4. **확장성** — 사용자 정의 타입 가능 + **`@field_validator`(v2) 데코레이터**로 커스텀 검증 로직 추가.

> **확장 검증 예 (v2):**
> ```python
> from pydantic import BaseModel, field_validator
>
> class CreateUserBody(BaseModel):
>     password: str
>     @field_validator("password")
>     @classmethod
>     def check_pw(cls, v: str) -> str:
>         if not any(c.isdigit() for c in v):
>             raise ValueError("숫자 포함 필수")
>         return v
> ```
> v1은 `@validator`. Spring의 커스텀 `ConstraintValidator`에 해당.

> **린터(linter)란**: 코드를 **실행하지 않고** 정적 분석해 잠재 오류·스타일 문제를 잡아 경고하는 도구(예: Ruff, flake8). Pydantic 모델은 평범한 클래스라 린터·Mypy가 그대로 이해함 (장점 2의 근거).

---

## 12. SQLAlchemy — ORM (DB 모델·엔진·세션)

> ⚠️ **미리보기**: 아직 미설치. 설치: `cd fastapi-ca && poetry add sqlalchemy pymysql`. 실제 구현은 책 진도에 맞춰서.

### 정체

파이썬 **ORM**(Object-Relational Mapper) — 파이썬 클래스 ↔ DB 테이블 매핑. 우리/책 모두 **2.0** 스타일.

> **Java 비교**: SQLAlchemy ≈ JPA/Hibernate, `Session` ≈ `EntityManager`, 모델 클래스 ≈ `@Entity`.

### 1) DB 모델 정의 (infra 계층)

```python
# user/infra/db_models/user.py
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase): pass

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(32))
    email: Mapped[str] = mapped_column(String(64), unique=True)
    password: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
```
이게 [섹션 2](#2-데이터베이스-계층--도메인-모델-vs-db-모델-리포지토리-패턴)의 "DB 모델". 도메인 `User`(dataclass)와 **분리** — 도메인은 SQLAlchemy를 모름.

### 2) 엔진 + 세션 (DB 연결)

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://user:pass@localhost:3306/mydb"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
```
- **engine**: DB 연결(풀). URL이 어디 붙을지 결정.
- **Session**: 쿼리 실행 단위(트랜잭션). = Java `EntityManager`.

### 3) 리포지토리에서 사용 (매퍼 + 저장)

```python
# user/infra/repository/user_repo.py
class UserRepository(IUserRepository):     # 섹션 3의 추상을 진짜 구현
    def save(self, user: User):
        with SessionLocal() as db:
            user_model = UserModel(id=user.id, name=user.name, ...)  # 매퍼: domain→DB모델
            db.add(user_model)
            db.commit()
```
[섹션 3](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip)의 `IUserRepository`를 구현하는 자리. domain `User` → `UserModel` 변환(매퍼)이 여기서 일어남.

### DB 드라이버 (MySQL — 책과 동일)

| 항목 | 값 |
|---|---|
| 드라이버 | `pymysql` |
| URL | `mysql+pymysql://user:pass@localhost:3306/db` |
| 설치 | `poetry add sqlalchemy pymysql` |

> MySQL 8 기본 인증(`caching_sha2_password`)으로 연결 에러 나면: GUI 클라이언트는 `allowPublicKeyRetrieval=true`, 파이썬(pymysql)은 `poetry add cryptography` 추가. (자세한 건 [run.md](run.md))

### Java/Spring 대응

| 개념 | SQLAlchemy | JPA/Hibernate |
|---|---|---|
| 모델 | `DeclarativeBase` 상속 | `@Entity` |
| 컬럼 매핑 | `mapped_column(...)` | `@Column` |
| 세션 | `Session` | `EntityManager` |
| 마이그레이션 | Alembic | Flyway/Liquibase |

---

## 13. 엔티티(domain) vs 모델(DB) — Spring 통합 vs 클린 분리

### 별개 클래스다 (클린 아키텍처)

| | 엔티티 (domain) | 모델 (DB) |
|---|---|---|
| 클래스 | `User` (dataclass) | `UserModel` (SQLAlchemy) |
| 위치 | `domain/` | `infra/.../db_models/` |
| 아는 것 | 비즈니스 규칙만 | 컬럼·타입·테이블 |
| SQLAlchemy 앎? | ❌ | ✅ |

같은 "유저"를 **두 관점으로 표현한 별개 클래스**.

### ⚠️ 용어 함정 — "Entity"의 뜻이 다르다

| 단어 | Spring/JPA | 클린(DDD) |
|---|---|---|
| **Entity** | `@Entity` = **DB 매핑 클래스** (= 클린의 "Model") | **도메인 객체** (순수) |

→ Spring의 `@Entity`는 클린 용어로 **"Model(UserModel)"에 해당**. 같은 단어가 정반대를 가리켜 헷갈림.

### Spring 통합 vs 클린 분리

| | Spring 레이어드 | 클린 아키텍처 |
|---|---|---|
| 엔티티/모델 | **1개 `@Entity`로 통합** (도메인+영속 겸용) | **분리** (`User` ↔ `UserModel`) |
| 장점 | 매퍼 불필요, 코드 적음 | 도메인 순수·교체·테스트 쉬움 |
| 단점 | 도메인이 JPA에 묶임 | 매퍼 보일러플레이트 |

→ 틀린 게 아니라 **트레이드오프**. 클린은 도메인 순수성을 위해 매퍼 비용 감수.

### 관계 = 의존 방향 (`model → entity`), 상속 아님

클린 의존 규칙: **모든 의존성은 안쪽(도메인)을 향한다.**
```
interface(DTO) ─┐
application     ─┼──▶  domain: User (엔티티)  ← 아무것도 안 의존, 순수
infra(Model,    ─┘                              모두 이쪽을 향함
     Repository)
```
- `model → entity` (infra가 domain을 안다), 반대 ❌.
- **상속 아님** (`class UserModel(User)` ❌). `User`·`UserModel`은 형제 같은 별개 클래스.
- 둘 사이 변환은 **Repository(매퍼)** 담당:
```python
def save(self, user: User):                  # 엔티티 받아
    user_model = UserModel(id=user.id, ...)  # 모델로 변환(매핑)
    db.add(user_model)
```
`UserModel`은 `User`를 import조차 안 해도 됨 — 변환은 repository가 함.

---

## 14. with 문 (컨텍스트 매니저)

리포지토리 `save`에서 등장:
```python
with SessionLocal() as db:
    db.add(new_user)
    db.commit()
# 블록 끝나면 db.close()가 자동 호출 (예외 나도 보장)
```

### `with`가 하는 일

- `with X() as y:` → `X()`의 `__enter__()` 호출(반환값이 `y`), 블록 실행, 끝나면 `__exit__()` 호출(정리).
- `__exit__`은 **예외가 나도 반드시 실행** → 리소스 누수 방지.
- DB 세션·파일·락 등 "열면 반드시 닫아야 하는 것"에 사용.

### Java 비교 — try-with-resources

```java
try (Session db = factory.openSession()) {
    db.add(...);
}   // 자동 close
```
```python
with SessionLocal() as db:
    db.add(...)
# 자동 close
```
→ Python `with` = Java try-with-resources. `__enter__`/`__exit__` = `AutoCloseable.close()`.

### ⚠️ 지금 repo `save()`엔 중복이 있음

```python
with SessionLocal() as db:      # ① 세션 생성 (with가 자동 close 보장)
    try:
        db = SessionLocal()     # ② 또 세션 생성! db 덮어씀 → ①은 안 쓰임
        db.add(new_user)
        db.commit()
    finally:
        db.close()              # ②를 수동 close
```
- 세션이 **2개** 생김(①은 만들고 안 쓰고 with가 닫음, ②가 실제 작업). 동작은 하지만 낭비.
- `with`가 이미 close를 보장하므로 **try/finally + 두 번째 `SessionLocal()`은 불필요.** 깔끔한 형태:
```python
with SessionLocal() as db:
    db.add(new_user)
    db.commit()
```

---

## 15. 회원가입 e2e 디버깅 — 만난 함정들

`POST /users`가 201로 동작하기까지 막았던 것들 (재발 방지용):

| # | 증상 | 원인 | 해결 |
|---|---|---|---|
| 1 | 서버 import 실패 | `from utils.crypto` (폴더는 `util/`) | `utils` → `util` |
| 2 | 해싱 시 `password cannot be longer than 72 bytes` | bcrypt 5.x ↔ passlib 1.7.4 **비호환** | `bcrypt==4.0.1` 핀 고정 |
| 3 | `AttributeError: get_by_email` | service 호출명 ≠ repo 메서드명 | `find_by_email`로 일치 |
| 4 | 응답에 id·해시 없음 | controller가 `return user`(요청 그대로) | `return created_user` |
| 5 | `User() got unexpected kwarg 'name'` | 도메인 User에 Profile 넣었는데 service/repo는 flat 가정 | flat으로 복귀 (책 구조) |

> 💡 **제일 재사용성 높은 교훈 — passlib + bcrypt 버전.** passlib 1.7.4는 bcrypt 5.x와 안 맞아서 해싱이 터짐(`72 bytes` 에러 또는 `MissingBackendError`). → **`poetry add "bcrypt==4.0.1"`**. FastAPI 학습에서 가장 흔히 막히는 지점 중 하나.
>
> 교훈 2 — **계층 간 시그니처 일치.** 한 곳(도메인 User 모양, 메서드명, 반환값)을 바꾸면 그걸 쓰는 모든 계층(service·repo·controller)을 같이 맞춰야 함. Profile 도입(5번)이 대표 사례.

---

## 16. 의존성 주입(DI) — 객체를 밖에서 주입

> [섹션 3](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip)에서 "지금 `UserService`가 `UserRepository`를 직접 생성해서 DIP를 반만 지킨다"고 짚었던 부분의 **해결책**.

### DI란

객체가 필요한 의존성을 **스스로 만들지 않고 밖에서 받는** 패턴. 책 예: `user_controller` → `UserService` → `UserRepository` 의존 체인. 직접 생성하면 강결합 → 구현 바뀌면 생성하는 모든 곳을 수정해야 함.

### 지금 코드 (DI 안 함 — 직접 생성)

```python
class UserService:
    def __init__(self):
        self.user_repo: IUserRepository = UserRepository()   # 스스로 생성 = 강결합
        self.crypto = Crypto()
```

### DI 적용 (생성자 주입)

```python
class UserService:
    def __init__(self, user_repo: IUserRepository):   # 밖에서 주입받음
        self.user_repo = user_repo
```
누가 `UserRepository()`를 만들어 넣어줄지는 **DI 컨테이너/프레임워크**가 담당.

### 3가지 유형

| 유형 | 주입 방법 | 시점 |
|---|---|---|
| **생성자 주입** (constructor) | `__init__` 인자로 | 객체 생성 시 (가장 권장) |
| **세터 주입** (setter) | 세터 메서드로 | 생성 후 |
| **메서드 주입** (method) | 메서드 인자로 | 그 메서드 호출 시 |

### 장점 (의존성을 한 곳에서 관리)

- 공통 로직 공유 / DB 연결 공유 / 인증·권한 등 보안 강화
- 필요한 객체를 따로 생성할 필요 없음 (주입받으니까)
- **테스트 쉬움** — 진짜 대신 가짜(mock) 구현을 주입

### ⚠️ DI vs DIP (헷갈림 주의)

| | DIP (의존성 역전 원칙) | DI (의존성 주입) |
|---|---|---|
| 정체 | **원칙** — 추상에 의존하라 ([섹션 3](#3-추상-클래스abcmeta로-리포지토리-인터페이스--의존성-역전dip)) | **기법/패턴** — 의존성을 밖에서 주입하라 |
| 답하는 질문 | "무엇에 의존할까" | "어떻게 받을까" |

→ **DI는 보통 DIP를 실현하는 수단.** 추상(`IUserRepository`)에 의존(DIP)하고, 그 구현체를 밖에서 주입(DI)한다. 같이 감.

### 프레임워크

- **FastAPI 내장**: `Depends()` — 경량 DI
- **`dependency-injector`**: 파이썬 인기 DI 컨테이너 (책이 쓰는 것)
- 책은 **둘 다** 다룸 (FastAPI Depends → dependency-injector 순).

### Spring 비교

| 개념 | Spring | Python |
|---|---|---|
| DI 컨테이너 | `ApplicationContext` (IoC 컨테이너) | `dependency-injector` Container |
| 빈 등록 | `@Service`/`@Repository` | Container에 등록 |
| 생성자 주입 | 생성자 + (`@Autowired`) | `__init__` 인자 / `Depends()` |

> Spring은 **DI가 프레임워크의 핵심**(IoC)이라 거의 자동. 파이썬은 `Depends`나 `dependency-injector`로 명시적으로 구성. 원리는 동일.

### FastAPI `Depends` 동작 — 라우터 파라미터는 FastAPI가 채운다

```python
@router.post("", status_code=201)
def create_user(
    user: UserCreate,                                          # ← 요청 body에서 옴
    user_service: Annotated[UserService, Depends(UserService)] # ← FastAPI가 생성·주입
):
    return user_service.create_user(...)
```

- **이 함수는 내가 부르는 게 아니라 FastAPI가 부른다.** 라우터 함수의 파라미터는 "호출자가 넘기는 인자"가 아니라 **"FastAPI가 출처를 보고 채우는 자리"**. 클라이언트는 `user`(body)만 보내고, `user_service`는 아무도 안 보냄 → FastAPI가 채움.

| 파라미터 | 출처 |
|---|---|
| `user: UserCreate` (Pydantic) | HTTP 요청 body |
| `user_service: ...Depends(...)` | DI (FastAPI가 생성·주입) |
| path/query 파라미터 | URL |

- ⚠️ `Depends`는 **반드시 파라미터 자리**에. 함수 **본문 안** 변수 annotation으로 쓰면 무효 (파이썬이 지역변수 annotation을 실행 안 함 → `Depends` 호출조차 안 됨).
- `Depends(UserService)` = "이 자리 채울 때 `UserService()`를 호출해 결과를 넣어라" (요청마다 실행).

### Spring(클래스/싱글톤) vs FastAPI(함수/요청마다)

| | Spring | FastAPI |
|---|---|---|
| 컨트롤러 | **클래스** | **함수** |
| 주입 위치 | 생성자/필드 (클래스 레벨) | **함수 파라미터** (`Depends`) |
| 기본 스코프 | **싱글톤** (앱 전체 공유) | **요청마다** 새로 생성 |
| 메서드 파라미터 | 요청 데이터만 | 요청 + 주입 **섞임** |

- **이유**: Spring은 컨트롤러가 클래스 → 클래스에 주입 / FastAPI는 라우트가 함수 → 함수 파라미터에 주입. 구조에서 자연스럽게 나옴.
- **스코프 차이**로 DB 세션 등이 FastAPI에선 "요청마다 새 세션"으로 자연스럽게 떨어짐. Spring은 싱글톤이라 세션 스코프를 따로 다룸.
- 본질은 동일: **내가 안 만들고 프레임워크가 만들어 넣어준다.**

```python
# 기존: 본문에서 직접 생성
def create_user(user: UserCreate):
    user_service = UserService()

# DI: 파라미터 선언만 → FastAPI가 채움
def create_user(user: UserCreate,
                user_service: Annotated[UserService, Depends(UserService)]):
    ...
```

---

### 2단계: `dependency-injector` 컨테이너 (중앙 IoC 컨테이너)

1단계(FastAPI `Depends`)는 의존성을 **각 파라미터에 흩뿌려** 선언. 책은 한 발 더 나가 **컨테이너 한 곳에 모아** 관리 → Spring의 `ApplicationContext`에 해당.

**구성 요소 3개**

| 요소 | 역할 |
|---|---|
| `containers.py`의 `Container` | 어떤 의존성을 어떻게 만들지 **등록(설계도)** |
| `providers.Factory(X)` | "X 달라고 하면 `X()`를 새로 찍어내라"는 **공장** |
| `@inject` + `Provide[Container.x]` | 주입받는 **진입점**(컨트롤러)에서 컨테이너를 끌어옴 |

```python
# containers.py
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["user"])    # user 패키지에 주입 배선
    user_repo = providers.Factory(UserRepository)
    user_service = providers.Factory(UserService, user_repo=user_repo)   # ← user_repo를 UserService에 주입
```

```python
# user_controller.py — 진입점에 Provide
@router.post("", status_code=201)
@inject
def create_user(user: UserCreate,
                user_service: UserService = Depends(Provide[Container.user_service])):
    ...
```

```python
# user_service.py — 타입만 선언 (Provide 불필요!)
class UserService:
    @inject
    def __init__(self, user_repo: IUserRepository):   # 컨테이너 Factory가 user_repo를 넣어줌
        self.user_repo = user_repo
```

**⚠️ 헷갈렸던 핵심 — `UserService`에는 `Provide[...]`가 왜 없나**

주입 마커(`Provide`)를 거는 방식이 2가지:
- (X) 받는 자리에 직접: `user_repo: IUserRepository = Provide[Container.user_repo]`
- (O, 책) **컨테이너 Factory가 인자를 대신 넘김** → 받는 쪽은 **타입만 선언**

`user_service = providers.Factory(UserService, user_repo=user_repo)`의 `user_repo=user_repo`가 "UserService 만들 때 user_repo를 끼워넣어라"라서, `UserService.__init__`은 타입만 적으면 됨.

→ **`Provide`는 "컨테이너에서 직접 꺼내올 자리"에만 붙는다.** 컨트롤러는 컨테이너에서 `user_service`를 꺼내야 하니 `Provide` 필요. `UserService`는 자기가 컨테이너를 안 뒤지고 Factory가 넣어주니 불필요.
> 그래서 컨트롤러가 `Provide[Container.user_service]`를 쓰려면 **컨테이너에 `user_service` 팩토리가 등록돼 있어야** 함(위 컨테이너 예시의 마지막 줄). 이게 빠지면 `Container.user_service`를 못 찾아 터짐.
> 참고: 이 Factory 방식에선 `UserService.__init__`의 `@inject`는 `user_repo`에 대해 사실상 하는 일이 없지만(마커가 없음), 책대로 둬도 무해.

**`Depends` vs 컨테이너 — 같은 DI, 다른 관리**

| | FastAPI `Depends` (1단계) | dependency-injector (2단계) |
|---|---|---|
| 등록 위치 | 파라미터마다 흩어짐 | `Container` 한 곳 집중 |
| 적용 범위 | HTTP 라우트 안에서만 | 라우트 밖(서비스끼리)도 |
| 교체(테스트) | 코드 수정/override | `container.x.override(가짜)` 한 줄 |
| Spring 대응 | (FastAPI 고유) | `ApplicationContext` |

### wiring(배선) — `@inject`/`Provide`를 실제로 이어주는 단계 ⭐

dependency-injector에서 제일 많이 막히는 지점. `@inject`와 `Provide[...]`를 써놨다고 끝이 아니라, **컨테이너가 "이 모듈의 마커들을 실제 provider에 연결"하는 wiring을 해야** 비로소 주입이 됨.

```
@inject 데코레이터   : import 때 함수에 껍데기(_patched)만 씌움
wiring (container)  : 그 껍데기에 "어떤 provider를 넣을지" 실제 연결  ← 빠지면 주입 안 됨
```

**wiring 안 되면 나는 에러:**
```
AttributeError: 'Provide' object has no attribute 'create_user'
```
= `user_service` 자리에 진짜 객체가 아니라 **`Provide` 마커가 그대로** 들어옴(껍데기만 있고 연결 안 됨).

**wiring 거는 법** — `Container()` 인스턴스화 시 `wiring_config`가 자동 실행:
```python
# containers.py
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["user"])  # user 패키지를 wire 대상으로

# main.py
app.container = Container()   # ← 이 순간 packages=["user"] 안 모듈들이 wire됨
```

**⭐⭐ 진짜 함정 — `packages` wiring은 `__init__.py` 필수**

`packages=["user"]`는 그 패키지 **하위 모듈을 walk해서** wire함. 그런데 폴더에 **`__init__.py`가 없으면** 파이썬이 namespace package로 취급 → dependency-injector가 모듈을 **못 찾아 wire를 건너뜀** → 위 `'Provide' object...` 500.

- 앱 자체 import(`from user.infra... import`)는 `__init__.py` 없어도 namespace package로 **잘 됨** → 그래서 "import는 되는데 주입만 안 되는" 헷갈리는 상황.
- 해결: `user/` 트리 **모든 폴더에 빈 `__init__.py`** 추가. (이 프로젝트에서 실제로 겪고 9개 만들어 해결.)
- 빈 파일이지만 **지우면 안 됨** — 지우면 wiring 깨져 다시 500.

| | Spring | dependency-injector |
|---|---|---|
| 빈 스캔 | `@ComponentScan`이 패키지 자동 스캔 | `wiring_config(packages=[...])` |
| 패키지 인식 | 자바는 디렉터리=패키지(자동) | 파이썬은 **`__init__.py` 있어야 정식 패키지** |
| 빠지면 | 보통 알아서 됨 | `__init__.py` 없으면 **조용히 wire 안 함** |

### Spring IoC 컨테이너 = 팩토리 메서드 패턴인가?

**엄밀히는 아니다.** 층위를 나눠 봐야 함:

| 질문 | 답 |
|---|---|
| 컨테이너 **자체**의 본질은? | **IoC(제어의 역전) 원칙 + DI**. GoF 디자인 패턴이 아니라 **설계 원칙**. |
| GoF 팩토리 메서드 패턴인가? | ❌ 팩토리 메서드는 **서브클래스가 오버라이드해 구체 클래스 결정**(상속 기반). 컨테이너는 상속이 아니라 **설정/메타데이터 기반**으로 빈 생성·생명주기 관리 → 굳이 치면 레지스트리/**Service Locator**에 가까움. |
| 팩토리는 전혀 안 쓰나? | 쓴다. **빈을 "정의/생성하는 방법"**에 등장: `@Configuration`+`@Bean` 메서드(= 팩토리 메서드), `FactoryBean`, XML `factory-method`. |

→ **"컨테이너 = IoC/DI 원칙"** 과 **"빈 생성 메커니즘 = 팩토리"** 를 분리해서 이해.

**dependency-injector로 연결:** `providers.Factory(UserRepository)`는 이름부터 Factory — 호출 때마다 **새 인스턴스**를 찍는 공장. GoF "팩토리 메서드(상속 오버라이드)"라기보다 **생성 책임을 컨테이너로 분리한 팩토리**.

| provider | 동작 | Spring 스코프 대응 |
|---|---|---|
| `providers.Factory` | 매번 새 인스턴스 | `prototype` |
| `providers.Singleton` | 한 번만 생성·공유 | `singleton` (Spring 기본) |

### DI는 TDD가 낳은 패턴인가 — 유래/연표

**TDD에서 "태어난" 건 아니다. 뿌리는 더 먼저고, TDD는 DI를 대중화시킨 촉매.**

```
IoC (원칙, 1988~)  ──"우리한테 전화 마, 우리가 건다"(Hollywood Principle)
  └─ DIP (원칙, 1996, 엉클 밥)  ──"구체 말고 추상에 의존하라" (= 섹션 3)
       └─ DI (기법/패턴, 명명 2004 Fowler)  ──"그 추상 구현을 밖에서 주입"
            ↑
        TDD (2002, Kent Beck) 가 "테스트 가능한 설계"로 강하게 밀어줌 (촉매)
```

| 시기 | 사건 |
|---|---|
| 1988~ | **IoC(제어의 역전)** — 프레임워크 설계에서 논의. 내가 프레임워크를 부르는 게 아니라 프레임워크가 내 코드를 부름 |
| 1996 | **DIP** — Robert Martin(엉클 밥)이 정식화 (추상에 의존) |
| 2000 | **Mock Objects** 기법 — TDD 진영(London school) 논문 *Endo-Testing*. DI가 있어야 성립 |
| 2002 | **TDD** 대중화 — Kent Beck *TDD By Example* |
| 2004 | **"Dependency Injection"** 용어 작명 — Martin Fowler ("IoC는 너무 막연하다"). 같은 시기 Spring/PicoContainer가 무거운 EJB 반작용으로 DI를 밈 |

**왜 TDD가 DI를 밀었나:** 단위 테스트를 격리하려면 의존성을 가짜(Mock/Fake)로 갈아끼울 **틈(seam)**이 필요 → 그 틈을 만들어주는 게 DI. 진짜 DB 박힌 리포지토리를 직접 생성하면 DB 없이는 테스트 불가(섹션 16 "테스트가 가능해짐" 참고). → **TDD가 테스트 가능한 설계를 강제 → DI 가치 폭발 → 대중화.**

**관계 정리:** **DIP = 원칙**(무엇에 의존?), **DI = 기법**(어떻게 받지?), **TDD = DI를 키운 촉매**. "TDD가 낳은 패턴"이 아니라 **"TDD와 DI가 같이 자란 사이"**, DI의 뿌리는 IoC/DIP.

---

## 17. 비동기 프로그래밍 — 동시성 vs 병렬성, async/await

> 책 6장. FastAPI는 파이썬 `asyncio` 기반이라 `async`/`await`로 비동기 코드를 씀. 여러 요청을 동시에, I/O를 비동기로 처리 → 확장성·성능↑. 요청 많은 대규모 서비스에 적합.

### 파이썬 동시성 3가지 방법

| 방법 | 모듈 | 메모리 | 작업 전환 주체 | 적합 | 단점 |
|---|---|---|---|---|---|
| **멀티스레딩** | `threading` | 부모 프로세스 **공유** | OS 커널 | **I/O 바운드**, UI 응답성 | **GIL**로 CPU 작업엔 효과 X, 메모리 안전 위험 |
| **멀티프로세싱** | `multiprocessing` | **독립**(공유 X) | OS 커널 | **CPU 바운드** | 무겁고 프로세스 간 통신(IPC) 필요 |
| **비동기** | `asyncio` | 단일 프로세스 | **앱이 스스로**(이벤트 루프) | **I/O 바운드**, 동시 네트워크 多 | 전용 비동기 라이브러리 필요 |

→ 선택 기준: **I/O 바운드 = 비동기**, **CPU 바운드 = 스레드/멀티프로세싱**.

### ⚠️ GIL (Global Interpreter Lock)

파이썬(CPython) 인터프리터가 **한 번에 한 스레드만** 실행하게 막는 잠금. C 확장 모듈과의 안전성 보장용. → **CPU 바운드 작업은 멀티스레딩해도 동시성 향상이 거의 없음**(스레드가 GIL을 번갈아 잡을 뿐). 그래서 CPU 작업엔 멀티프로세싱(프로세스마다 별도 인터프리터 = 별도 GIL).

### 동시성(concurrency) ≠ 병렬성(parallelism) — 헷갈림 1순위

| | 동시성 (concurrency) | 병렬성 (parallelism) |
|---|---|---|
| 뜻 | 작업들이 서로의 **순서·결과에 영향 안 줌** (번갈아 처리해도 됨) | 여러 작업을 **물리적으로 동시에** 처리 |
| 비유 | 요리사 **1명**이 여러 냄비를 **번갈아** 봄 | 요리사 **여러 명**이 각자 동시에 |
| 핵심 | "동시에 **처리 중**" (꼭 같은 순간 X) | "같은 순간 **실제로 같이**" |

동시성 있는 작업을 **병렬화도 가능**(시간 단축). 많은 사람이 둘을 같다고 착각하지만 **다른 개념**.

### 🍔 햄버거 비유 (공식 문서 concurrent-burgers)

- **비동기(번호표 O)**: 주문 후 **번호표 받고 자리로 감** → 햄버거 기다리는 동안 **다른 일**(연인과 수다) 가능, 가끔 나왔나 확인. = "마냥 안 기다리고 다른 일 함" → 효율적.
- **병렬(번호표 X)**: 주문 후 **주문대에서 계속 기다림**. 주문받기·요리는 병렬로 돌지만 주문자는 **시간 허비**(수다 못 떰). = **병렬이라고 꼭 효율적인 건 아님.**

> 포인트: 비효율의 핵심은 "**기다리는 동안 노는 시간**". 비동기는 그 노는 시간에 다른 일을 시켜 절약.

### 병렬처리 — `concurrent.futures`

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
# ThreadPoolExecutor  : 스레드 풀 (I/O 바운드)
# ProcessPoolExecutor : 프로세스 풀 (CPU 바운드)
```
스레드/프로세스 **풀**을 만들어 작업을 병렬 실행.

### async/await + 이벤트 루프

- `async`/`await`는 **파이썬 3.5** 도입. **JS/Node.js와 같은 키워드**(이벤트 루프 동작도 유사) → JS 해봤으면 친숙.
- `async def`로 비동기 함수(코루틴) 정의, `await`로 비동기 호출을 기다림, `asyncio`가 **이벤트 루프** 제어.

```python
import asyncio

async def fetch():            # 비동기 함수(코루틴)
    await asyncio.sleep(1)    # await: 기다리는 동안 이벤트 루프가 다른 일 함
    return "done"

asyncio.run(fetch())          # 이벤트 루프 실행
```

### Java/Spring 비교

| 개념 | Python | Java/Spring |
|---|---|---|
| 스레드 | `threading` | `Thread`, `ExecutorService` |
| 스레드/프로세스 풀 | `concurrent.futures` | `ThreadPoolExecutor`, `ForkJoinPool` |
| 비동기 | `async`/`await` + `asyncio` | `CompletableFuture`, `@Async`, WebFlux(Reactor) |
| GIL | **있음** (CPU 병렬 제약) | **없음** (스레드로 진짜 CPU 병렬) |

> 자바는 GIL이 없어 스레드로 진짜 CPU 병렬이 됨 → "CPU 작업엔 멀티프로세싱" 같은 파이썬 특유 회피책이 자바엔 거의 불필요. 반대로 파이썬 비동기는 **Node.js 이벤트 루프와 거의 같은 모델**.

---

## 18. JWT (JSON Web Token) — 인증/인가

> 책 7장. 지금까지 API는 **누구나** 호출 가능했음. 하지만 내 게시물은 나만 보고/수정해야 함 → **인증/인가 + 로그인** 필요. 현대 웹 인증의 사실상 표준이 **JWT** (RFC 7519).

### 먼저: 인증(Authentication) vs 인가(Authorization)

| | 인증 (Authentication) | 인가 (Authorization) |
|---|---|---|
| 묻는 것 | **너 누구냐?** | **너 이거 할 권한 있냐?** |
| 예 | 로그인 (id/pw 확인) | "이 게시물 수정은 작성자만" |
| 순서 | 먼저 | 인증 후 |

### 왜 JWT — 매 요청마다 로그인할 순 없으니

매 요청마다 id/pw 입력시키면 아무도 안 씀. → 로그인 정보를 **클라이언트(브라우저/앱)에 저장**하고 이후 요청에 실어 보냄. 근데 클라이언트는 보안에 취약 → 그 보완책이 **JWT**. 서버가 세션을 따로 저장 안 하는 **무상태(stateless)** 인증.

### 구조 — `header.payload.signature` (점으로 3등분)

```
eyJhbGciOi...   .   eyJzdWIiOi...   .   SflKxwRJSM...
   헤더(Header)        페이로드(Payload)      시그니처(Signature)
```
- 헤더·페이로드는 **base64 인코딩** (암호화 아님! 그냥 인코딩) → 누구나 디코딩 가능.
- base64 쓰는 이유: HTTP 헤더/파라미터로 실어 나르기 좋고, JSON 문자열 직접 못 다루는 환경 대응.
- 동작 직접 보기: **https://jwt.io**

### ① 헤더 (Header) — 토큰의 메타정보

```json
{ "typ": "JWT", "alg": "HS256" }
```
- `typ`: 토큰 타입. "JWT"로 권고.
- `alg`: 서명/암호화 알고리즘. 안 하면 `"none"`, 하면 예: `HS256`.

### ② 페이로드 (Payload) — 클레임(claim) 담는 곳

클레임 = 토큰에 담는 정보 조각. 3종류:

**1. 등록된 클레임 (Registered)** — IANA에 등록된 표준. 필수는 아니나 상호호환성 위해 권장.

| 클레임 | 뜻 | 설명 |
|---|---|---|
| `iss` | issuer(발급자) | 누가 발급했나 |
| `sub` | subject(주제) | 토큰 주제 (보통 유저 식별) |
| `aud` | audience(수신자) | 누구에게 보내는가 (보통 보호 리소스 URL) |
| `exp` | expiration(만료) | 만료 시각 — 지나면 거부. **UNIX epoch** |
| `nbf` | not before | 이 시각 이후부터 유효 |
| `iat` | issued at(발급 시각) | 언제 발급됐나 |
| `jti` | JWT ID(식별자) | 토큰 고유 id — **재사용 공격 방지** |

**2. 공개 클레임 (Public)** — 공개돼도 무방한 것. 이름 충돌 막으려 URI 형식 권장. 예: `{"http://example.com/is_root": true}`

**3. 비공개 클레임 (Private)** — 발급자·사용자 간 약속한 것. 서비스 도메인 내 필요한 이름/값. 충돌 주의.

> ⚠️⚠️ **페이로드는 base64일 뿐 암호화 아님 → 누구나 읽음.** 비밀번호 같은 **민감 정보 절대 넣지 말 것.** (네 회원 코드의 해시된 password도 토큰엔 넣으면 안 됨)

### ③ 시그니처 (Signature) — 위변조 검증

헤더·페이로드는 그냥 base64라 **공격자가 값 바꿔 토큰 위조 가능** → 진짜인지 검증할 장치가 시그니처.

```
HMACSHA256(
  base64UrlEncode(header) + "." + base64UrlEncode(payload),
  secret          ← 서버만 아는 비밀키
)
```
- `alg`가 HS256이면 HMACSHA256으로 서명. **`secret`은 서버에서만 안전하게 보관.**
- 검증: 같은 secret으로 다시 서명해보고 일치하는지 봄. **시그니처만 잘 지키면** JWT가 공개돼도 "내가 만든 토큰 vs 공격자가 위조한 것"을 구분 가능.
- 페이로드 한 글자만 바꿔도 시그니처가 안 맞아 `Invalid Signature` → 위변조 탐지.

### 핵심 요약

| 부분 | 내용 | 비밀? |
|---|---|---|
| Header | typ, alg | ❌ 공개(base64) |
| Payload | 클레임(iss/sub/exp…) | ❌ 공개(base64) — **민감정보 X** |
| Signature | secret으로 서명 | secret만 서버 비밀 |

→ JWT의 안전성은 **암호화가 아니라 "서명으로 위변조를 막는 것"**. 내용은 다 보이지만 **바꾸면 들킨다**가 핵심.

### Spring 비교

| | Spring | FastAPI(책) |
|---|---|---|
| 인증 프레임워크 | Spring Security | 직접 구현 (PyJWT/python-jose 등) |
| JWT 생성/검증 | `jjwt`, `nimbus-jose-jwt` | `jwt.encode()` / `jwt.decode()` |
| 토큰 추출 | `OncePerRequestFilter` | `Depends`로 헤더에서 추출 |
| 무상태 | `SessionCreationPolicy.STATELESS` | 원래 무상태 |

> Spring은 Security가 많은 걸 자동화하지만, FastAPI 책에선 JWT 생성·검증을 **직접** 구현하며 원리를 익힘. 무상태(stateless)라 서버가 세션을 저장 안 하는 건 동일.
