"""
Heart Sync Backend - Serializers
방과 플레이어 데이터를 JSON으로 변환하는 Serializer 모음
"""

from rest_framework import serializers
from .models import Room, Player


class PlayerSerializer(serializers.ModelSerializer):
    """
    플레이어 정보 Serializer
    - 플레이어 ID, 닉네임, 상태, 방장 여부를 포함
    - player_id와 is_host는 자동 생성/설정되므로 읽기 전용
    """
    class Meta:
        model = Player
        fields = ['player_id', 'nickname', 'status', 'is_host']
        read_only_fields = ['player_id', 'is_host']


class RoomSerializer(serializers.ModelSerializer):
    """
    방 목록용 Serializer (간단한 정보만)
    - QR 코드 URL을 동적으로 생성
    - 방장 정보를 중첩 Serializer로 포함
    """
    host = PlayerSerializer(read_only=True)  # 방장 정보 포함
    qr_code_url = serializers.SerializerMethodField()  # QR 코드 URL 동적 생성

    class Meta:
        model = Room
        fields = ['room_id', 'room_code', 'qr_code_url', 'host', 'status', 'created_at']
        read_only_fields = ['room_id', 'room_code', 'status', 'created_at']

    def get_qr_code_url(self, obj):
        """
        room_code를 기반으로 QR 코드 이미지 URL 생성
        외부 API (qrserver.com) 사용
        """
        return f"https://api.qrserver.com/v1/create-qr-code/?data={obj.room_code}"


class RoomDetailSerializer(serializers.ModelSerializer):
    """
    방 상세 정보용 Serializer
    - 방에 속한 모든 플레이어 목록 포함
    - 방 정보를 더 자세하게 표시
    """
    players = PlayerSerializer(many=True, read_only=True)  # 방의 모든 플레이어

    class Meta:
        model = Room
        fields = ['room_id', 'room_code', 'status', 'max_players', 'players', 'created_at']
        read_only_fields = ['room_id', 'room_code', 'created_at']


class JoinRoomSerializer(serializers.Serializer):
    """
    방 참가 요청 Serializer
    - 닉네임만 입력 받음 (2-10자)
    """
    nickname = serializers.CharField(min_length=2, max_length=10)


class LeaveRoomSerializer(serializers.Serializer):
    """
    방 퇴장 요청 Serializer
    - 퇴장할 플레이어의 ID를 입력 받음
    """
    player_id = serializers.CharField()


class GameStartSerializer(serializers.Serializer):
    """
    게임 시작 요청 Serializer
    - 게임 모드, 제한 시간, BPM 범위 설정
    - bpm_min < bpm_max 검증 포함
    """
    player_id = serializers.CharField()  # 게임 시작 요청하는 플레이어 (방장이어야 함)
    mode = serializers.ChoiceField(choices=Room.Mode.choices)  # 게임 모드 선택
    time_limit_seconds = serializers.IntegerField(min_value=1)  # 게임 시간 (최소 1초)
    bpm_min = serializers.IntegerField(min_value=50, max_value=200)  # 최소 BPM (50-200)
    bpm_max = serializers.IntegerField(min_value=50, max_value=200)  # 최대 BPM (50-200)

    def validate(self, data):
        """
        BPM 범위 검증
        bpm_min이 bpm_max보다 작아야 함
        """
        if data['bpm_min'] >= data['bpm_max']:
            raise serializers.ValidationError(
                "bpm_min must be less than bpm_max"
            )
        return data

