from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Room, Player
from .serializers import (
    RoomDetailSerializer,
    LeaveRoomSerializer,
    JoinRoomSerializer,
    GameStartSerializer
)
from django.utils import timezone


class RoomDetailView(APIView):
    """
    방 상세 정보 조회 API
    GET /api/rooms/{room_id}/
    """
    def get(self, request, room_id):
        # 방 조회 (없으면 자동 404)
        room = get_object_or_404(Room, room_id=room_id)

        # Serializer로 변환
        serializer = RoomDetailSerializer(room)

        # 응답 반환 (200은 기본값이라 생략)
        return Response(serializer.data)


class LeaveRoomView(APIView):
    """
    방 퇴장 API
    POST /api/rooms/{room_id}/leave/
    Body: {"player_id": "p123"}
    """
    def post(self, request, room_id):
        # 1. player_id 검증
        serializer = LeaveRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Room과 Player 조회
        player_id = serializer.validated_data['player_id']
        room = get_object_or_404(Room, room_id=room_id)
        player = get_object_or_404(Player, player_id=player_id, room=room)

        # 3. 호스트 퇴장 시 방 삭제
        if player.is_host:
            room_code = room.room_code  # 삭제 전 저장
            room.delete()  # CASCADE로 모든 플레이어도 자동 삭제됨
            return Response({
                "message": "Room deleted (host left)",
                "room_code": room_code
            }, status=status.HTTP_200_OK)

        # 4. 일반 플레이어 삭제
        player.delete()

        # 5. 성공 응답
        return Response({"message": "Successfully left the room"})

class JoinRoomView(APIView):
    """
    방 참가 API
    POST /api/rooms/join/
    Body: {"room_code": "123456", "nickname": "철수"}

    제약사항:
    - 게임이 시작되지 않은 방(WAITING 상태)만 참가 가능
    - 방 인원이 max_players 미만이어야 함
    """
    def post(self, request):
        # 1. room_code와 nickname 검증
        serializer = JoinRoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )
        room_code = serializer.validated_data["room_code"]
        nickname = serializer.validated_data["nickname"]

        # 2. Room 찾기 (room_code로 찾기)
        room = get_object_or_404(Room, room_code=room_code)

        # 3. 게임 시작 여부 확인
        if room.status != Room.Status.WAITING:
            return Response(
                {"error": "Game already started"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. 방인원 확인
        current_players = room.players.count()
        if current_players >= room.max_players:
            return Response(
                {"error": "Room is full"},
                status=status.HTTP_400_BAD_REQUEST
            )


        # 5. Player 생성
        player = Player.objects.create(
            room=room,
            nickname=nickname,
            status=Player.Status.WAITING,  # TextChoices 사용
            is_host=False
        )

        # 6. 방 전체 정보 응답 (모든 플레이어 포함)
        room_serializer = RoomDetailSerializer(room)

        return Response(room_serializer.data, status=status.HTTP_200_OK)



class RoomDeleteView(APIView):
    """
    DELETE /api/rooms/{room_id}/?player_id={player_id}
    
    방 삭제 (방장 권한 필요)
    - 방 삭제 시 모든 플레이어 자동 삭제 (CASCADE)
    """
    
    def delete(self, request, room_id):
        # 1. player_id 검증
        player_id = request.query_params.get('player_id')
        if not player_id:
            return Response({
                "error": "player_id is required",
                "detail": "Add ?player_id=YOUR_ID to the request URL"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 2. Room과 Player 검증
        room = get_object_or_404(Room, room_id=room_id)
        player = get_object_or_404(Player, player_id=player_id, room=room)
        
        # 3. 방장 권한 검증
        if not player.is_host:
            return Response({
                "error": "Permission denied",
                "detail": "Only the host can delete the room"
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 4. 삭제 전 정보 저장 (응답용)
        room_code = room.room_code
        player_count = room.players.count()  # CASCADE 전에 카운트
        
        # 5. Room 삭제
        room.delete()
        
        # 6. 성공 응답
        return Response({
            "message": "Room deleted successfully",
            "room_code": room_code,
            "deleted_players": player_count
        }, status=status.HTTP_200_OK)
        

class GameStartView(APIView):
    """
    게임 시작 API
    POST /api/rooms/{room_id}/start/
    Body: {
        "player_id": "xxx",
        "mode": "steady_beat" | "pulse_rush",
        "time_limit_seconds": 120,
        "bpm_min": 60,
        "bpm_max": 120
    }

    요구사항:
    - 방장만 게임 시작 가능
    - 모든 플레이어가 READY 상태여야 함
    - 게임 시작 시 Room과 모든 Player 상태가 PLAYING으로 변경됨
    """
    def post(self, request, room_id):
        # 1. 게임 설정 데이터 검증
        serializer =  GameStartSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            ) 
        
        # 2. 검증된 데이터 추출
        player_id, mode, time_limit, bpm_min, bpm_max = (
        serializer.validated_data['player_id'],
        serializer.validated_data['mode'],
        serializer.validated_data['time_limit_seconds'],
        serializer.validated_data['bpm_min'],
        serializer.validated_data['bpm_max']
        )   


        # 3. Room, Player 찾기
        room = get_object_or_404(Room, room_id=room_id)
        player = get_object_or_404(Player, player_id=player_id, room=room)

        # 4. 방장 권한 검증
        if not player.is_host:
            return Response(
                {"error": "Only host can start the game"},  
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 5. 모든 플레이어 준비 확인
        # 방장 포함 모든 플레이어가 READY 상태여야 게임 시작 가능
        total_players = room.players.count()
        ready_players = room.players.filter(status=Player.Status.READY).count()

        if ready_players != total_players:
            return Response(
                {
                    "error": "Not all players are ready",
                    "detail": f"{ready_players}/{total_players} players ready"
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 6. Room에 게임 설정 저장
        room.mode = mode
        room.time_limit_seconds = time_limit
        room.bpm_min = bpm_min
        room.bpm_max = bpm_max
        room.status = Room.Status.PLAYING  # TextChoices 사용
        room.started_at = timezone.now()
        room.save()

        # 7. 모든 플레이어 상태를 PLAYING으로 변경
        room.players.update(status=Player.Status.PLAYING)

        # 8. 게임 시작 정보 응답
        return Response({
            "message": "Game started",
            "room_id": room.room_id,
            "status": room.status,
            "game_settings": {
                "mode": room.mode,
                "time_limit": room.time_limit_seconds,
                "bpm_min": room.bpm_min,
                "bpm_max": room.bpm_max
            },
            "started_at": room.started_at
        }, status=status.HTTP_200_OK)


class RoomCreateView(APIView):
    """
    방 생성 API
    POST /api/rooms/
    Body: {"host_nickname": "바다"}
    """
    def post(self, request):
        # 1. host_nickname 검증
        host_nickname = request.data.get('host_nickname')
        

        if not host_nickname:
            return Response(
                {"error": "host_nickname is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(host_nickname) < 2 or len(host_nickname) > 10:
            return Response(
                {"error": "Nickname must be between 2-10 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Room 생성 (room_id와 room_code는 모델의 save()에서 자동 생성)
        room = Room.objects.create(
            status=Room.Status.WAITING,  # TextChoices 사용
            mode=Room.Mode.STEADY_BEAT  # 기본 모드 설정 (안전장치)
        )

        # 3. 방장(Host) Player 생성
        Player.objects.create(
            room=room,
            nickname=host_nickname,
            status=Player.Status.WAITING,  # TextChoices 사용 (입장 직후)
            is_host=True
        )

        # 4. 응답 (RoomDetailSerializer 사용)
        serializer = RoomDetailSerializer(room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


        
