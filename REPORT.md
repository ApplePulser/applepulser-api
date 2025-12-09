# Applepulser API 기술보고서

## 1. 서론

### 1.1 개발 배경 및 목적
현대인들의 건강에 대한 관심이 높아지면서 심박수 측정 기능을 활용한 다양한 애플리케이션이 등장하고 있다. 본 프로젝트는 여러 사용자가 실시간으로 심박수를 공유하며 함께 운동할 수 있는 멀티플레이어 게임 플랫폼의 백엔드 서버를 개발하는 것을 목적으로 한다.

### 1.2 프로젝트 개요
**Applepulser**는 실시간 심박수 동기화 멀티플레이어 게임 플랫폼이다. 사용자들은 방을 생성하고, QR코드를 통해 다른 사용자를 초대하며, 실시간으로 심박수 데이터를 공유하면서 게임을 진행할 수 있다.

**주요 기능:**
- 게임 방 생성 및 관리
- QR코드 기반 방 참가
- 실시간 심박수 데이터 브로드캐스트
- 플레이어 상태 관리 (대기 → 준비 → 플레이 → 종료)
- 연결 끊김 자동 감지 및 처리

---

## 2. 시스템 설계

### 2.1 시스템 아키텍처

```
┌─────────────────┐     HTTP/REST      ┌─────────────────┐
│                 │ ◄─────────────────► │                 │
│  Android App    │                     │  Django Backend │
│  (클라이언트)    │ ◄─────────────────► │  (서버)          │
│                 │     WebSocket       │                 │
└─────────────────┘                     └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │     SQLite      │
                                        │   (Database)    │
                                        └─────────────────┘
```

- **HTTP/REST**: 방 생성, 참가, 게임 시작 등 일반 요청 처리
- **WebSocket**: 실시간 심박수 데이터 및 상태 변경 브로드캐스트

### 2.2 데이터베이스 설계 (ERD)

```
┌─────────────────────────────────────┐
│               Room                  │
├─────────────────────────────────────┤
│ PK  room_id        VARCHAR(8)       │  ◄── UUID 앞 8자리
│     room_code      VARCHAR(6)       │  ◄── 초대 코드 (QR용)
│     status         VARCHAR(20)      │  ◄── waiting/playing/finished
│     mode           VARCHAR(20)      │  ◄── steady_beat/pulse_rush
│     max_players    INTEGER          │
│     time_limit_seconds INTEGER      │
│     bpm_min        INTEGER (NULL)   │
│     bpm_max        INTEGER (NULL)   │
│     created_at     DATETIME         │
│     started_at     DATETIME (NULL)  │
└─────────────────────────────────────┘
                    │
                    │ 1:N
                    ▼
┌─────────────────────────────────────┐
│              Player                 │
├─────────────────────────────────────┤
│ PK  player_id      VARCHAR(36)      │  ◄── UUID 전체
│ FK  room_id        VARCHAR(8)       │
│     nickname       VARCHAR(10)      │
│     status         VARCHAR(20)      │  ◄── waiting/ready/playing/finished
│     is_host        BOOLEAN          │
│     joined_at      DATETIME         │
└─────────────────────────────────────┘
```

**관계 설명:**
- Room과 Player는 1:N 관계
- Room 삭제 시 관련 Player 자동 삭제 (CASCADE)

### 2.3 API 설계

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/rooms/` | 방 생성 |
| GET | `/api/rooms/{room_id}/` | 방 상세 조회 |
| POST | `/api/rooms/join/` | 방 참가 |
| POST | `/api/rooms/{room_id}/leave/` | 방 퇴장 |
| POST | `/api/rooms/{room_id}/start/` | 게임 시작 |
| DELETE | `/api/rooms/{room_id}/` | 방 삭제 |

**WebSocket Endpoint:**
- `ws://localhost:8000/ws/game/{room_id}/`

---

## 3. 구현

### 3.1 개발 환경

| 구분 | 내용 |
|------|------|
| 언어 | Python 3.13 |
| 프레임워크 | Django 5.1, Django REST Framework 3.15 |
| 실시간 통신 | Django Channels 4.3.1, Daphne 4.2.1 |
| 데이터베이스 | SQLite |
| 개발 도구 | Git, Postman |
| OS | macOS |

### 3.2 프로젝트 구조

```
applepulser-api/
├── heart_sync_backend/          # Django 프로젝트 설정
│   ├── settings.py              # 설정 파일
│   ├── urls.py                  # 메인 URL 라우팅
│   ├── asgi.py                  # ASGI 설정 (WebSocket)
│   └── wsgi.py                  # WSGI 설정
│
├── rooms/                       # 핵심 앱
│   ├── models.py                # Room, Player 모델
│   ├── serializers.py           # 데이터 직렬화
│   ├── views.py                 # REST API 뷰
│   ├── consumers.py             # WebSocket Consumer
│   ├── routing.py               # WebSocket 라우팅
│   ├── urls.py                  # API URL 패턴
│   └── admin.py                 # 관리자 페이지
│
├── manage.py
├── requirements.txt
└── db.sqlite3
```

### 3.3 핵심 기능 구현

#### 3.3.1 모델 설계 (models.py)

**Room 모델:**
```python
class Room(models.Model):
    room_id = models.CharField(max_length=8, primary_key=True)
    room_code = models.CharField(max_length=6, unique=True)
    status = models.CharField(max_length=20, choices=Status.choices)
    # ... 생략

    def save(self, *args, **kwargs):
        if not self.room_id:
            self.room_id = str(uuid.uuid4())[:8]  # 자동 생성
        if not self.room_code:
            self.room_code = str(uuid.uuid4().int)[:6]
        super().save(*args, **kwargs)
```

**Player 모델 - 4단계 상태 관리:**
```python
class Player(models.Model):
    class Status(models.TextChoices):
        WAITING = 'waiting', '대기 중'
        READY = 'ready', '준비 완료'
        PLAYING = 'playing', '플레이 중'
        FINISHED = 'finished', '완료'
```

#### 3.3.2 WebSocket 실시간 통신 (consumers.py)

**GameConsumer 핵심 로직:**
```python
class GameConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'ping':
            # Ping/Pong으로 연결 상태 확인
            await self.send(json.dumps({'type': 'pong'}))

        elif data['type'] == 'heart_rate':
            # 심박수 데이터를 모든 클라이언트에 브로드캐스트
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'send_heart_rate', ...}
            )
```

**연결 끊김 감지:**
- 5초마다 Ping 체크
- 15초(3회 실패) 이상 응답 없으면 자동 탈락 처리
- 플레이어 상태를 FINISHED로 변경 후 브로드캐스트

#### 3.3.3 REST API 구현 (views.py)

**게임 시작 API 예시:**
```python
class GameStartView(APIView):
    def post(self, request, room_id):
        # 1. 방장 권한 확인
        if not player.is_host:
            return Response({'error': '방장만 게임을 시작할 수 있습니다.'},
                          status=403)

        # 2. 모든 플레이어 준비 상태 확인
        not_ready = room.players.exclude(status=Player.Status.READY)
        if not_ready.exists():
            return Response({'error': '모든 플레이어가 준비되지 않았습니다.'},
                          status=400)

        # 3. 게임 시작 처리
        room.status = Room.Status.PLAYING
        room.save()
```

---

## 4. 테스트 및 결과

### 4.1 기능 테스트 결과

| 테스트 항목 | 결과 |
|------------|------|
| 방 생성 (POST /api/rooms/) | 성공 |
| 방 참가 (POST /api/rooms/join/) | 성공 |
| 방 조회 (GET /api/rooms/{id}/) | 성공 |
| 게임 시작 (POST /api/rooms/{id}/start/) | 성공 |
| 방 퇴장 (POST /api/rooms/{id}/leave/) | 성공 |
| 방 삭제 (DELETE /api/rooms/{id}/) | 성공 |
| WebSocket 연결 | 성공 |
| 심박수 브로드캐스트 | 성공 |
| 연결 끊김 감지 | 성공 |

### 4.2 API 테스트 예시

**방 생성 요청:**
```json
POST /api/rooms/
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
    "status": "waiting"
}
```

---

## 5. 결론

### 5.1 개발 결과 요약

본 프로젝트에서는 Django와 Django Channels를 활용하여 실시간 멀티플레이어 게임 백엔드를 성공적으로 구현하였다.

**구현 완료 기능:**
- REST API 6개 엔드포인트
- WebSocket 실시간 통신
- 플레이어 4단계 상태 관리
- Ping/Pong 기반 연결 끊김 자동 감지
- QR코드 기반 방 초대 시스템

### 5.2 한계점 및 개선 방향

**한계점:**
- 로컬 개발 환경에서만 테스트됨 (SQLite, InMemoryChannelLayer 사용)
- 동시 접속자 수에 대한 부하 테스트 미진행

**개선 방향:**
- 배포 환경 구축 시 Redis 채널 레이어 적용
- 사용자 인증 시스템 추가
- 게임 결과 저장 및 통계 기능 구현

---

## 6. 참고문헌

- Django 공식 문서. https://docs.djangoproject.com/
- Django REST Framework 공식 문서. https://www.django-rest-framework.org/
- Django Channels 공식 문서. https://channels.readthedocs.io/
