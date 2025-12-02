"""
Django Admin 설정
Room과 Player 모델을 관리자 페이지에서 관리
"""
from django.contrib import admin
from .models import Room, Player


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Room 모델 관리자 설정"""
    list_display = ["room_id", "room_code", "status", "max_players", "created_at",
                    "mode", "time_limit_seconds", "bpm_min", "bpm_max", "started_at"]
    list_filter = ["status", "mode"]
    search_fields = ["room_id", "room_code"]
    readonly_fields = ['room_id', 'room_code', 'created_at']


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Player 모델 관리자 설정"""
    list_display = ['player_id', 'nickname', 'room', 'status', 'is_host', 'joined_at']
    list_filter = ['status', 'is_host']
    search_fields = ['nickname', 'player_id']
    readonly_fields = ['player_id', 'joined_at']
