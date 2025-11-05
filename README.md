# applepulser-api

# Heart Sync Backend Architecture

## 📊 현재 프로젝트 상태 (2025-11-05)

### ✅ **Phase 1 완료!** 🎉

#### 1. Models (데이터베이스 설계) ✅
- **Room 모델**: 게임 방 관리 (room_id, room_code 자동 생성)
- **Player 모델**: 플레이어 관리 (4단계 상태: WAITING → READY → PLAYING → FINISHED)
- TextChoices로 타입 안전성 보장
- ForeignKey 관계 설정 (CASCADE)

#### 2. Serializers (데이터 변환) ✅
- **PlayerSerializer**: 플레이어 정보 직렬화
- **RoomSerializer**: 방 목록용 (QR 코드 URL 동적 생성)
- **RoomDetailSerializer**: 방 상세 정보 (전체 플레이어 포함)
- **JoinRoomSerializer**: 방 참가 요청
- **LeaveRoomSerializer**: 방 퇴장 요청
- **GameStartSerializer**: 게임 시작 (커스텀 BPM 검증)

#### 3. Views (REST API) ✅
- **RoomCreateView**: 방 생성
- **RoomDetailView**: 방 조회
- **JoinRoomView**: 방 참가
- **LeaveRoomView**: 방 퇴장
- **GameStartView**: 게임 시작 (준비 상태 체크)
- **RoomDeleteView**: 방 삭제 (방장 권한)

#### 4. Admin (관리자 페이지) ✅
- **RoomAdmin**: 방 관리 (필터, 검색 기능)
- **PlayerAdmin**: 플레이어 관리 (상태별 필터)

#### 5. URL 라우팅 & 테스트 ✅
- **URL 구성**: rooms/urls.py + 메인 URLs 연결
- **마이그레이션**: 데이터베이스 스키마 생성 완료
- **Postman 테스트**: 전체 API 엔드포인트 검증 완료

### 🚀 **다음 작업: Phase 2 시작!**

**Phase 2: WebSocket 실시간 통신**
- Django Channels 설치 및 설정
- GameConsumer 구현
- 심박수 실시간 브로드캐스트

**Phase 3: 최적화 및 배포 준비**
- 코드 최적화
- 에러 핸들링 강화
- 안드로이드 앱 연동

### 📈 **진행률: Phase 1 - 100% 완료** ✅ → **Phase 2 시작 준비!**

---

## 🚀 시작하기 (팀원용 가이드)

### 1️⃣ 프로젝트 클론 (처음 한 번만)

```bash
# 프로젝트 클론
git clone <repository-url>
cd applepulser-api
```

### 2️⃣ Python 가상환경 설정

**Mac/Linux:**
```bash
# 가상환경 생성
python3 -m venv heartsync

# 가상환경 활성화
source heartsync/bin/activate

# 활성화 확인: 터미널 앞에 (heartsync) 표시됨
```

**Windows:**
```bash
# 가상환경 생성
python -m venv heartsync

# 가상환경 활성화
heartsync\Scripts\activate

# 활성화 확인: 터미널 앞에 (heartsync) 표시됨
```

### 3️⃣ 패키지 설치

```bash
# requirements.txt에 있는 모든 패키지 설치
pip install -r requirements.txt
```

**설치되는 패키지:**
- Django 5.1
- Django REST Framework 3.15
- 기타 필요한 라이브러리들

### 4️⃣ 데이터베이스 마이그레이션

```bash
# 데이터베이스 스키마 생성
python manage.py migrate

# 성공 메시지:
# Applying rooms.0001_initial... OK
```

### 5️⃣ 관리자 계정 생성 (선택)

```bash
# Admin 페이지 접속용 계정 생성
python manage.py createsuperuser

# 입력 정보:
# - Username: admin (원하는 이름)
# - Email: (선택사항, 엔터로 스킵 가능)
# - Password: (안전한 비밀번호)
```

### 6️⃣ 서버 실행

```bash
# Django 개발 서버 시작
python manage.py runserver

# 성공 메시지:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

### 7️⃣ 접속 확인

**브라우저에서 접속:**
- **API 루트**: http://127.0.0.1:8000/api/
- **Admin 페이지**: http://127.0.0.1:8000/admin/
  - Username과 Password 입력 (5️⃣에서 생성한 계정)

---

## 📡 API 사용법

### **방 생성 (POST)**
```bash
POST http://127.0.0.1:8000/api/rooms/
Content-Type: application/json

{
  "host_nickname": "바다"
}
```

**응답:**
```json
{
  "room_id": "a1b2c3d4",
  "room_code": "123456",
  "qr_code_url": "https://api.qrserver.com/v1/create-qr-code/?data=123456",
  "host": {
    "player_id": "uuid...",
    "nickname": "바다",
    "status": "waiting",
    "is_host": true
  },
  "status": "waiting",
  "created_at": "2025-11-05T..."
}
```

### **방 조회 (GET)**
```bash
GET http://127.0.0.1:8000/api/rooms/{room_id}/
```

### **방 참가 (POST)**
```bash
POST http://127.0.0.1:8000/api/rooms/{room_id}/join/
Content-Type: application/json

{
  "nickname": "플레이어1"
}
```

### **방 퇴장 (POST)**
```bash
POST http://127.0.0.1:8000/api/rooms/{room_id}/leave/
Content-Type: application/json

{
  "player_id": "플레이어_uuid"
}
```

### **게임 시작 (POST)**
```bash
POST http://127.0.0.1:8000/api/rooms/{room_id}/start/
Content-Type: application/json

{
  "player_id": "방장_uuid",
  "mode": "steady_beat",
  "time_limit_seconds": 120,
  "bpm_min": 100,
  "bpm_max": 150
}
```

### **방 삭제 (DELETE)**
```bash
DELETE http://127.0.0.1:8000/api/rooms/{room_id}/?player_id={방장_uuid}
```

---

## 🛠️ 개발 팁

### 서버 재시작이 필요한 경우:
- 모델 변경 후 마이그레이션 실행 시
- settings.py 변경 시

### 서버 재시작이 필요 없는 경우:
- views.py, serializers.py 수정
- Python 파일 일반 수정 (자동 재시작됨)

### 가상환경 종료:
```bash
deactivate
```

### 다음 작업 시 가상환경 다시 활성화:
```bash
# Mac/Linux
source heartsync/bin/activate

# Windows
heartsync\Scripts\activate
```

---

## 시스템 아키텍처

[안드로이드 앱] 
    ↓ HTTP/WebSocket
[Django Backend]
    ↓
[SQLite Database]
---

## 프로젝트 구조

```
applepulser-api/
│
├── heart_sync_backend/      # Django 프로젝트 설정 폴더
│   ├── settings.py          # Django 설정 파일
│   ├── urls.py              # 메인 URL 라우팅
│   ├── asgi.py              # WebSocket용 (Phase 2)
│   └── wsgi.py              # HTTP 서버용
│
├── rooms/                   # 게임 방 관리 앱
│   ├── models.py            # Room, Player 모델
│   ├── serializers.py       # 데이터 직렬화
│   ├── views.py             # REST API 뷰
│   ├── urls.py              # API 엔드포인트 라우팅
│   ├── admin.py             # Admin 페이지 설정
│   └── tests.py             # 테스트 코드
│
├── heartsync/               # Python 가상환경 (git 제외)
├── db.sqlite3               # SQLite 데이터베이스 (git 제외)
├── manage.py                # Django 관리 명령어
├── requirements.txt         # Python 패키지 목록
├── .gitignore               # Git 제외 파일 설정
└── README.md                # 프로젝트 문서 (이 파일)
```

**주요 폴더 설명:**
- `heart_sync_backend/`: Django 프로젝트 설정 및 전역 URL 관리
- `rooms/`: 게임 방 및 플레이어 관리 기능 (핵심 앱)
- `heartsync/`: 가상환경 폴더 (로컬에만 존재)

---

## 데이터베이스 설계

### Room (방)
```python
class Room(models.Model):
    # 기본 정보
    room_id = CharField(max_length=8, primary_key=True)   # UUID 앞 8자리, 자동생성
    room_code = CharField(max_length=6, unique=True)      # 6자리 숫자, 자동생성, 초대 코드용
    status = CharField(max_length=20, default='waiting')  # waiting/playing/finished (TextChoices)
    max_players = IntegerField(default=4)                 # 최대 4명
    created_at = DateTimeField(auto_now_add=True)         # 방 생성 시간 자동

    # 게임 설정 (방 생성 시 필수 입력)
    mode = CharField(max_length=20)                       # steady_beat/pulse_rush (TextChoices)
    time_limit_seconds = IntegerField(default=120)        # 게임 시간 (기본 2분)

    # BPM 설정 (선택 사항)
    bpm_min = IntegerField(null=True, blank=True)         # 최소 심박수
    bpm_max = IntegerField(null=True, blank=True)         # 최대 심박수

    # 게임 진행 정보
    started_at = DateTimeField(null=True, blank=True)     # 게임 시작 시간 (시작 전에는 None)
```

**주요 특징:**
- `room_id`: UUID 앞 8자리 사용 (Primary Key), 시스템 내부 식별용
- `room_code`: UUID 기반 6자리 숫자, QR코드/초대 코드용
- `status`와 `mode`: `TextChoices`로 타입 안전성 보장
- `save()` 메서드에서 room_id와 room_code 자동 생성
- `related_name='players'`로 역참조 가능
- Meta 클래스에서 최근 생성 순으로 정렬 (`-created_at`)

### Player (플레이어)
```python
class Player(models.Model):
    # 기본 정보
    player_id = CharField(max_length=36, primary_key=True)           # UUID 전체, 자동생성
    room = ForeignKey(Room, on_delete=CASCADE, related_name='players') # 소속 방
    nickname = CharField(max_length=10)                              # 닉네임 (최대 10자)

    # 플레이어 상태 (4단계)
    class Status(models.TextChoices):
        WAITING = 'waiting', '대기 중'      # 방 입장 직후 (준비 전)
        READY = 'ready', '준비 완료'         # 준비 버튼 클릭
        PLAYING = 'playing', '플레이 중'    # 게임 시작됨
        FINISHED = 'finished', '완료'       # 게임 종료

    status = CharField(max_length=20, default=WAITING)               # 플레이어 상태
    is_host = BooleanField(default=False)                            # 방장 여부
    joined_at = DateTimeField(auto_now_add=True)                     # 입장 시간 자동
```

**주요 특징:**
- `player_id`: UUID 전체(36자)를 사용 (Primary Key)
- `room`: Room 모델과 ForeignKey 관계, 방 삭제 시 플레이어도 삭제 (CASCADE)
- `status`: **4단계 상태 관리** (WAITING → READY → PLAYING → FINISHED)
- `save()` 메서드에서 player_id 자동 생성
- `related_name='players'`로 Room에서 `room.players.all()` 접근 가능
- Meta 클래스에서 입장 순서대로 정렬 (`joined_at`)

**게임 플로우:**
1. 플레이어 입장 → `WAITING` (대기 중)
2. 준비 버튼 클릭 → `READY` (준비 완료)
3. 게임 시작 → `PLAYING` (모든 플레이어가 READY여야 시작 가능)
4. 게임 종료 → `FINISHED`

### GameResult (게임 결과, 선택사항)
```python
class GameResult(models.Model):
    room = ForeignKey (Room)
    player = ForeignKey (Player)
    rank = IntegerField
    score = IntegerField

    # 통계
    workout_time = IntegerField
    avg_bpm = IntegerField
    min_bpm = IntegerField
    max_bpm = IntegerField
    time_in_zone = IntegerField

    finished_at = DateTimeField
```

---

## Serializer 레이어 ✅

Django REST Framework의 Serializer를 사용하여 모델과 JSON 데이터 변환을 담당합니다.

### rooms/serializers.py

#### 1. PlayerSerializer
```python
# 플레이어 기본 정보 직렬화
fields: ['player_id', 'nickname', 'status', 'is_host']
read_only: ['player_id', 'is_host']  # 자동 생성 필드
```

#### 2. RoomSerializer (목록용)
```python
# 방 목록 간단 정보 + QR 코드
fields: ['room_id', 'room_code', 'qr_code_url', 'host', 'status', 'created_at']
특징:
- qr_code_url: SerializerMethodField로 동적 생성 (qrserver.com API 사용)
- host: PlayerSerializer 중첩 (방장 정보)
```

#### 3. RoomDetailSerializer (상세용)
```python
# 방 상세 정보 + 전체 플레이어 목록
fields: ['room_id', 'room_code', 'status', 'max_players', 'players', 'created_at']
특징:
- players: PlayerSerializer(many=True) - 모든 플레이어 포함
```

#### 4. 액션 Serializers
```python
# JoinRoomSerializer - 방 참가
- nickname: 2-10자 닉네임

# LeaveRoomSerializer - 방 퇴장
- player_id: 퇴장할 플레이어 ID

# GameStartSerializer - 게임 시작 (커스텀 검증 포함)
- player_id: 시작 요청 플레이어 (방장)
- mode: steady_beat / pulse_rush
- time_limit_seconds: 게임 시간 (최소 1초)
- bpm_min, bpm_max: BPM 범위 (50-200)
- validate(): bpm_min < bpm_max 검증 로직 ⭐
```

**설계 포인트:**
- 용도별 Serializer 분리 (List/Detail)
- 읽기 전용 필드 명확히 구분
- 커스텀 검증 메서드 활용
- 중첩 Serializer로 관계 표현

---

## Views 레이어 ✅

Django REST Framework의 APIView를 사용한 REST API 엔드포인트 구현

### rooms/views.py

#### 1. RoomCreateView
```python
POST /api/rooms/
Body: {"host_nickname": "바다"}

기능:
- host_nickname 검증 (2-10자)
- Room 자동 생성 (room_id, room_code 자동 생성)
- 방장 Player 생성 (is_host=True, status=WAITING)
- QR 코드 URL 포함 응답

응답: 201 CREATED
```

#### 2. RoomDetailView
```python
GET /api/rooms/{room_id}/

기능:
- 방 상세 정보 조회
- 모든 플레이어 목록 포함
- 없는 방: 자동 404 처리

응답: 200 OK
```

#### 3. JoinRoomView
```python
POST /api/rooms/{room_id}/join/
Body: {"nickname": "플레이어1"}

기능:
- 닉네임 검증 (2-10자)
- 방 상태 확인 (WAITING만 입장 가능)
- 인원 제한 확인 (max_players)
- Player 생성 (status=WAITING, is_host=False)

응답: 200 OK (생성된 플레이어 정보)
```

#### 4. LeaveRoomView
```python
POST /api/rooms/{room_id}/leave/
Body: {"player_id": "uuid"}

기능:
- player_id 검증
- 방장은 퇴장 불가 (400 에러)
- Player 삭제

응답: 200 OK
```

#### 5. GameStartView
```python
POST /api/rooms/{room_id}/start/
Body: {
  "player_id": "uuid",
  "mode": "steady_beat",
  "time_limit_seconds": 120,
  "bpm_min": 100,
  "bpm_max": 150
}

기능:
- 게임 설정 검증 (bpm_min < bpm_max)
- 방장 권한 확인 (403 Forbidden)
- 모든 플레이어 준비 확인 (READY 상태)
- Room 상태 → PLAYING 변경
- 게임 시작 시간 기록

응답: 200 OK (게임 설정 정보)
```

#### 6. RoomDeleteView
```python
DELETE /api/rooms/{room_id}/?player_id={uuid}

기능:
- query parameter로 player_id 전달
- 방장 권한 확인 (403 Forbidden)
- Room 삭제 (플레이어 자동 삭제: CASCADE)
- 삭제 전 정보 저장하여 응답

응답: 200 OK (삭제된 정보)
```

**설계 포인트:**
- get_object_or_404로 자동 404 처리
- TextChoices로 타입 안전성 보장
- 권한 검증 (방장 전용 기능)
- 상태별 검증 로직 (게임 시작 여부, 인원 제한 등)
- 친절한 에러 메시지

---

## Admin 레이어 ✅

Django Admin을 통한 관리자 페이지 구현

### rooms/admin.py

#### RoomAdmin
```python
관리 기능:
- 목록 표시: room_id, room_code, status, max_players, created_at,
             mode, time_limit_seconds, bpm_min, bpm_max, started_at
- 필터: status, mode
- 검색: room_id, room_code
- 읽기 전용: room_id, room_code, created_at
```

#### PlayerAdmin
```python
관리 기능:
- 목록 표시: player_id, nickname, room, status, is_host, joined_at
- 필터: status, is_host
- 검색: nickname, player_id
- 읽기 전용: player_id, joined_at
```

**설계 포인트:**
- 자동 생성 필드는 읽기 전용 처리
- 상태별 필터링 기능
- 검색 기능으로 빠른 조회

---

## WebSocket 실시간 통신 (Phase 2 예정)

> **Phase 2에서 구현 예정**
> - Django Channels를 사용한 WebSocket 서버
> - 실시간 심박수 데이터 브로드캐스트
> - 게임 이벤트 실시간 동기화

---

## 데이터 흐름

### 1. 방 생성 흐름

[안드로이드 앱]
    ↓ POST /api/rooms/
    ↓ {"host_nickname": "바다"}
[Django View]
    ↓
[Serializer] → 유효성 검사
    ↓
[Model] → Room 생성 (room_code 자동생성)
    ↓
[Database] → 저장
    ↓
[Serializer] → JSON 변환
    ↓
[Response] ← {"room_id": "...", "room_code": "123456"}
    ↓
[안드로이드 앱] ← QR 코드 표시

### 2. 실시간 심박수 흐름 (Phase 2 예정)

> **WebSocket을 통한 실시간 통신 (Phase 2에서 구현 예정)**
>
> 플레이어들의 심박수 데이터를 실시간으로 모든 참가자에게 브로드캐스트하여
> 동기화된 게임 경험을 제공합니다.

---

## 기술 스택

### ✅ 현재 사용 중 (Phase 1)
- **Django 5.1**: 웹 프레임워크
- **Django REST Framework 3.15**: REST API 구현
- **SQLite**: 데이터베이스 (개발용)
- **Postman**: API 테스트

### 🔜 Phase 2 예정
- **Django Channels**: WebSocket 실시간 통신
- **Redis** (선택): 채널 레이어 (배포 시)

### 🛠️ 개발 도구
- **Git**: 버전 관리
- **Python 3.13**: 프로그래밍 언어

---

## 개발 단계

### Phase 1: REST API 백엔드 구현 ✅ **완료!**
- [x] Django 프로젝트 생성
- [x] **Models 구현** (Room, Player with 4-stage status)
- [x] **Serializers 구현** (6개 - QR 코드, 커스텀 검증)
- [x] **Views 구현** (6개 API 엔드포인트)
  - [x] RoomCreateView
  - [x] RoomDetailView
  - [x] JoinRoomView
  - [x] LeaveRoomView
  - [x] GameStartView (준비 상태 체크)
  - [x] RoomDeleteView (방장 권한)
- [x] **Admin 페이지 설정** (필터, 검색 기능)
- [x] **URL 라우팅 구성** ✅
  - [x] rooms/urls.py 생성
  - [x] heart_sync_backend/urls.py 연결
- [x] **데이터베이스 마이그레이션** ✅
- [x] **Postman API 테스트** ✅
  - [x] 방 생성 테스트
  - [x] 플레이어 참가 테스트
  - [x] 게임 시작 테스트
  - [x] 전체 플로우 테스트

**🎉 Phase 1 완료! 모든 REST API 정상 동작 확인!**

### Phase 2: WebSocket 실시간 통신
- [ ] Django Channels 설치 및 설정
- [ ] ASGI 설정 (asgi.py)
- [ ] GameConsumer 구현
  - [ ] WebSocket 연결/해제
  - [ ] 심박수 데이터 수신
  - [ ] 실시간 브로드캐스트
- [ ] 채널 레이어 설정 (Redis 선택)
- [ ] WebSocket 테스트

### Phase 3: 최적화 및 배포 준비
- [ ] 코드 리팩토링
- [ ] 성능 최적화
  - [ ] 쿼리 최적화 (select_related, prefetch_related)
  - [ ] 불필요한 DB 호출 제거
- [ ] 에러 핸들링 강화
- [ ] 로깅 시스템 추가
- [ ] 보안 강화 (CORS, 인증)
- [ ] 배포 준비
  - [ ] 환경 변수 분리
  - [ ] Production 설정
- [ ] 안드로이드 앱 연동 테스트

---