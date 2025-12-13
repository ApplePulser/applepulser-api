# Applepulser - 실시간 심박수 동기화 멀티플레이어 게임

## 1. Target (시스템 개요)

**Applepulser**는 실시간 심박수 동기화 멀티플레이어 게임 플랫폼이다.

사용자들은 방을 생성하고, QR코드를 통해 다른 사용자를 초대하며, 실시간으로 심박수 데이터를 공유하면서 게임을 진행할 수 있다.

**주요 기능:**
- 게임 방 생성 및 관리
- QR코드 기반 방 참가
- 실시간 심박수 데이터 브로드캐스트
- 플레이어 상태 관리 (대기 → 준비 → 플레이 → 종료)
- 연결 끊김 자동 감지 및 처리

**시스템 구성:**
- Backend: Django + Django Channels (Python)
- Android App: Kotlin
- Hardware: Arduino + 심박수 센서

---

## 2. Motivation (개발 동기)

현대인들의 건강에 대한 관심이 높아지면서 심박수 측정 기능을 활용한 다양한 애플리케이션이 등장하고 있다.

기존의 운동 앱들은 대부분 개인 기록 관리에 초점이 맞춰져 있어, 친구들과 함께 실시간으로 경쟁하거나 협동하는 기능이 부족하다.

본 프로젝트는 여러 사용자가 실시간으로 심박수를 공유하며 함께 운동할 수 있는 멀티플레이어 게임 플랫폼을 개발하여, 운동의 재미와 동기부여를 높이고자 한다.

---

## 3. Problem / Challenge (문제 및 어려움)

### 3.1 기술적 문제

<!-- TODO: 팀원들이 작성 -->

### 3.2 프로젝트 진행 중 어려웠던 점

<!-- TODO: 팀원들이 작성 -->

---

## 4. Solution (해결 방법)

### 4.1 기술적 해결

<!-- TODO: 팀원들이 작성 -->

### 4.2 문제 해결 과정

<!-- TODO: 팀원들이 작성 -->

---

## 5. System Design (시스템 설계)

### 5.1 시스템 아키텍처

```
┌─────────────────┐                      ┌─────────────────┐
│    Arduino      │  Bluetooth/Serial    │                 │
│  (심박 센서)     │ ──────────────────► │  Android App    │
└─────────────────┘                      │  (클라이언트)    │
                                         └────────┬────────┘
                                                  │
                                         HTTP/REST & WebSocket
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │ Django Backend  │
                                         │    (서버)        │
                                         └────────┬────────┘
                                                  │
                                                  ▼
                                         ┌─────────────────┐
                                         │     SQLite      │
                                         │   (Database)    │
                                         └─────────────────┘
```

### 5.2 데이터베이스 설계 (ERD)

```
┌─────────────────────────────────────┐
│               Room                  │
├─────────────────────────────────────┤
│ PK  room_id        VARCHAR(8)       │
│     room_code      VARCHAR(6)       │
│     status         VARCHAR(20)      │
│     mode           VARCHAR(20)      │
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
│ PK  player_id      VARCHAR(36)      │
│ FK  room_id        VARCHAR(8)       │
│     nickname       VARCHAR(10)      │
│     status         VARCHAR(20)      │
│     is_host        BOOLEAN          │
│     joined_at      DATETIME         │
└─────────────────────────────────────┘
```

### 5.3 API 설계

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/rooms/` | 방 생성 |
| GET | `/api/rooms/{room_id}/` | 방 상세 조회 |
| POST | `/api/rooms/join/` | 방 참가 |
| POST | `/api/rooms/{room_id}/leave/` | 방 퇴장 |
| POST | `/api/rooms/{room_id}/start/` | 게임 시작 |
| DELETE | `/api/rooms/{room_id}/` | 방 삭제 |

**WebSocket:** `ws://server/ws/game/{room_id}/`

---

## 6. Implementation (구현)

### 6.1 개발 환경

| 구분 | Backend | Android | Hardware |
|------|---------|---------|----------|
| 언어 | Python 3.13 | Kotlin | C++ |
| 프레임워크 | Django 5.1, DRF, Channels | Android SDK | Arduino |
| 통신 | REST API, WebSocket | OkHttp, WebSocket | Serial/Bluetooth |
| 데이터베이스 | SQLite | - | - |

### 6.2 핵심 구현 내용

**Backend - WebSocket 실시간 통신:**
```python
class GameConsumer(AsyncWebsocketConsumer):
    async def receive(self, text_data):
        data = json.loads(text_data)

        if data['type'] == 'heart_rate':
            # 심박수 데이터를 모든 클라이언트에 브로드캐스트
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'send_heart_rate', 'bpm': data['bpm']}
            )
```

**연결 끊김 감지:**
- 5초마다 Ping 체크
- 15초 이상 응답 없으면 자동 탈락 처리

---

## 7. Lessons Learned (배운 점)

### 7.1 기술적으로 배운 점

<!-- TODO: 팀원들이 작성 -->

### 7.2 협업에서 배운 점

<!-- TODO: 팀원들이 작성 -->

---

## 8. Role per Member (팀원별 역할)

| 이름 | 역할 | 담당 업무 |
|------|------|----------|
| <!-- TODO --> | Backend | <!-- TODO --> |
| <!-- TODO --> | Android | <!-- TODO --> |
| <!-- TODO --> | Hardware | <!-- TODO --> |
| <!-- TODO --> | <!-- TODO --> | <!-- TODO --> |

---

## 9. 참고문헌

- Django 공식 문서. https://docs.djangoproject.com/
- Django REST Framework 공식 문서. https://www.django-rest-framework.org/
- Django Channels 공식 문서. https://channels.readthedocs.io/
- Android Developers. https://developer.android.com/
- Arduino 공식 문서. https://www.arduino.cc/reference/en/
