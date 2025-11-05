from django.db import models
import uuid

import uuid
from django.db import models


class Room(models.Model):
    """게임 방 모델"""
    
    # ===== Choices 정의 =====
    class Mode(models.TextChoices):
        STEADY_BEAT = 'steady_beat', 'Steady Beat'
        PULSE_RUSH = 'pulse_rush', 'Pulse Rush'
    
    class Status(models.TextChoices):
        WAITING = 'waiting', '대기 중'
        PLAYING = 'playing', '플레이 중'
        FINISHED = 'finished', '완료'
    
    # ===== 필드 정의 =====
    # 방 고유 ID (시스템 내부용)
    room_id = models.CharField(max_length=8, primary_key=True, editable=False)
    
    # 방 코드 (사용자 초대용, 중복 불가)
    room_code = models.CharField(max_length=6, unique=True, editable=False)
    
    # 방 상태 (기본값: 대기 중)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.WAITING
    )
    
    # 최대 인원 (기본값: 4명)
    max_players = models.IntegerField(default=4)
    
    # 방 생성 시간 (자동 저장)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # 게임 모드 (필수 선택)
    mode = models.CharField(
        max_length=20,
        choices=Mode.choices
    )
    
    # 게임 제한 시간 (기본값: 120초 = 2분)
    time_limit_seconds = models.IntegerField(default=120)
    
    # BPM 범위 (선택 사항)
    bpm_min = models.IntegerField(null=True, blank=True)
    bpm_max = models.IntegerField(null=True, blank=True)
    
    # 게임 시작 시간 (게임 시작 전에는 None)
    started_at = models.DateTimeField(null=True, blank=True)
    
    # ===== 메서드 =====
    def save(self, *args, **kwargs):
        """room_id와 room_code 자동 생성"""
        if not self.room_id:
            self.room_id = str(uuid.uuid4())[:8]
        if not self.room_code:
            self.room_code = str(uuid.uuid4().int)[:6]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Room {self.room_code}"
    
    # ===== 메타 정보 =====
    class Meta:
        ordering = ['-created_at']  # 최근 생성 순



class Player(models.Model):

    # 플레이어의 상태 정의
    class Status(models.TextChoices):
        WAITING = 'waiting', '대기 중'      # 방 입장 직후 (준비 전)
        READY = 'ready', '준비 완료'         # 준비 버튼 클릭
        PLAYING = 'playing', '플레이 중'    # 게임 시작됨
        FINISHED = 'finished', '완료'       # 게임 종료

    player_id = models.CharField(max_length=36, primary_key=True, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    nickname = models.CharField(max_length=10)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.WAITING)
    is_host = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    @property
    def host(self):
        """방장 플레이어 반환"""
        return self.players.filter(is_host=True).first()
    
    def save(self, *args, **kwargs):
        if not self.player_id:
            self.player_id = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nickname} in {self.room.room_code}"
    
    class Meta:
        ordering = ['joined_at']







# Create your models here.
