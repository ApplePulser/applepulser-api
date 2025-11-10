"""
Rooms 앱 URL 설정
/api/rooms/ 하위의 모든 API 엔드포인트 정의
"""
from django.urls import path
from .views import (
    RoomCreateView,
    RoomDetailView,
    JoinRoomView,
    LeaveRoomView,
    GameStartView,
    RoomDeleteView
)

urlpatterns = [
    # POST /api/rooms/ - 방 생성
    path('', RoomCreateView.as_view(), name='room-create'),

    # GET /api/rooms/{room_id}/ - 방 상세 조회
    path('<str:room_id>/', RoomDetailView.as_view(), name='room-detail'),

    # POST /api/rooms/{room_id}/join/ - 방 참가
    path('<str:room_id>/join/', JoinRoomView.as_view(), name='room-join'),

    # POST /api/rooms/{room_id}/leave/ - 방 퇴장
    path('<str:room_id>/leave/', LeaveRoomView.as_view(), name='room-leave'),

    # POST /api/rooms/{room_id}/start/ - 게임 시작
    path('<str:room_id>/start/', GameStartView.as_view(), name='game-start'),

    # DELETE /api/rooms/{room_id}/delete/?player_id={player_id} - 방 삭제
    path('<str:room_id>/delete/', RoomDeleteView.as_view(), name='room-delete'),
]