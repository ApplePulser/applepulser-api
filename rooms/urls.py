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
    path('', RoomCreateView.as_view(), name='room-create'),
    path('<str:room_id>/', RoomDetailView.as_view(), name='room-detail'),
    path('<str:room_id>/join/', JoinRoomView.as_view(), name='room-join'),
    path('<str:room_id>/leave/', LeaveRoomView.as_view(), name='room-leave'),
    path('<str:room_id>/start/', GameStartView.as_view(), name='game-start'),
    path('<str:room_id>/delete/', RoomDeleteView.as_view(), name='room-delete'),
]