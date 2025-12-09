# Applepulser API 명세서

## REST API

### 1. 방 생성
**POST** `/api/rooms/`

**Request:**
```json
{
    "host_nickname": "바다"
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| host_nickname | string | O | 방장 닉네임 (2-10자) |

**Response:** `201 Created`
```json
{
    "room_id": "a1b2c3d4",
    "room_code": "123456",
    "status": "waiting",
    "max_players": 4,
    "players": [
        {
            "player_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
            "nickname": "바다",
            "status": "waiting",
            "is_host": true
        }
    ],
    "created_at": "2025-12-09T12:00:00.000000Z"
}
```

---

### 2. 방 조회
**GET** `/api/rooms/{room_id}/`

**Request:** 없음 (URL에 room_id만 필요)

**Response:** `200 OK`
```json
{
    "room_id": "a1b2c3d4",
    "room_code": "123456",
    "status": "waiting",
    "max_players": 4,
    "players": [
        {
            "player_id": "uuid-1",
            "nickname": "바다",
            "status": "waiting",
            "is_host": true
        },
        {
            "player_id": "uuid-2",
            "nickname": "철수",
            "status": "waiting",
            "is_host": false
        }
    ],
    "created_at": "2025-12-09T12:00:00.000000Z"
}
```

---

### 3. 방 참가
**POST** `/api/rooms/join/`

**Request:**
```json
{
    "room_code": "123456",
    "nickname": "철수"
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| room_code | string | O | 방 코드 (6자리) |
| nickname | string | O | 닉네임 (2-10자) |

**Response:** `200 OK`
```json
{
    "player_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "room_id": "a1b2c3d4",
    "room_code": "123456",
    "status": "waiting",
    "max_players": 4,
    "players": [
        {
            "player_id": "uuid-host",
            "nickname": "바다",
            "status": "waiting",
            "is_host": true
        },
        {
            "player_id": "uuid-new",
            "nickname": "철수",
            "status": "waiting",
            "is_host": false
        }
    ],
    "created_at": "2025-12-09T12:00:00.000000Z"
}
```

**Error:** `400 Bad Request`
```json
{"error": "Game already started"}
{"error": "Room is full"}
```

---

### 4. 방 퇴장
**POST** `/api/rooms/{room_id}/leave/`

**Request:**
```json
{
    "player_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| player_id | string | O | 퇴장할 플레이어 ID |

**Response (일반 플레이어):** `200 OK`
```json
{
    "message": "Successfully left the room"
}
```

**Response (방장 퇴장 시 방 삭제):** `200 OK`
```json
{
    "message": "Room deleted (host left)",
    "room_code": "123456"
}
```

---

### 5. 게임 시작
**POST** `/api/rooms/{room_id}/start/`

**Request:**
```json
{
    "player_id": "방장-uuid",
    "mode": "steady_beat",
    "time_limit_seconds": 120,
    "bpm_min": 60,
    "bpm_max": 120
}
```
| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| player_id | string | O | 방장 ID |
| mode | string | O | "steady_beat" 또는 "pulse_rush" |
| time_limit_seconds | int | O | 게임 시간 (초, 최소 1) |
| bpm_min | int | O | 최소 BPM (50-200) |
| bpm_max | int | O | 최대 BPM (50-200, bpm_min보다 커야함) |

**Response:** `200 OK`
```json
{
    "message": "Game started",
    "room_id": "a1b2c3d4",
    "status": "playing",
    "game_settings": {
        "mode": "steady_beat",
        "time_limit": 120,
        "bpm_min": 60,
        "bpm_max": 120
    },
    "started_at": "2025-12-09T12:05:00.000000Z"
}
```

**Error:** `403 Forbidden`
```json
{"error": "Only host can start the game"}
```

**Error:** `400 Bad Request`
```json
{
    "error": "Not all players are ready",
    "detail": "2/4 players ready"
}
```

---

### 6. 방 삭제
**DELETE** `/api/rooms/{room_id}/?player_id={방장-uuid}`

**Request:** Query Parameter로 player_id 전달

**Response:** `200 OK`
```json
{
    "message": "Room deleted successfully",
    "room_code": "123456",
    "deleted_players": 4
}
```

**Error:** `403 Forbidden`
```json
{
    "error": "Permission denied",
    "detail": "Only the host can delete the room"
}
```

---

## WebSocket API

**URL:** `ws://localhost:8000/ws/game/{room_id}/`

### 메시지 타입

#### 1. Ping/Pong (연결 유지)
```json
// 클라이언트 → 서버 (5초마다)
{"type": "ping"}

// 서버 → 클라이언트
{"type": "pong"}
```

#### 2. 심박수 전송
```json
// 클라이언트 → 서버
{"type": "heart_rate", "player_id": "uuid", "bpm": 85}

// 서버 → 모든 클라이언트
{"type": "heart_rate", "player_id": "uuid", "bpm": 85}
```

#### 3. Ready 상태 변경
```json
// 클라이언트 → 서버
{"type": "player_ready", "player_id": "uuid"}

// 서버 → 모든 클라이언트
{"type": "player_ready", "player_id": "uuid", "nickname": "철수"}
```

#### 4. 연결 끊김 알림
```json
// 서버 → 모든 클라이언트 (15초 타임아웃 시)
{"type": "player_disconnected", "player_id": "uuid", "nickname": "철수"}
```

---

## 상태값 정리

### Room Status
| 값 | 설명 |
|---|------|
| waiting | 대기 중 (참가 가능) |
| playing | 게임 중 |
| finished | 게임 종료 |

### Player Status
| 값 | 설명 |
|---|------|
| waiting | 대기 중 (준비 전) |
| ready | 준비 완료 |
| playing | 게임 중 |
| finished | 게임 종료 / 연결 끊김 |

### Game Mode
| 값 | 설명 |
|---|------|
| steady_beat | 스테디 비트 모드 |
| pulse_rush | 펄스 러시 모드 |
