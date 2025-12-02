import json
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Player

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ WebSocket 연결 시 실행 """
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'
        self.last_ping = datetime.now()  # 마지막 ping 시간 초기화
        self.player_id = None  # player_id는 나중에 설정됨
        self.ping_check_task = None  # ping 체크 태스크

        # 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # WebSocket 연결 수락
        await self.accept()

    async def disconnect(self, close_code):
        """ WebSocket 연결 해제 시 실행 """
        # ping 체크 태스크 취소
        if self.ping_check_task:
            self.ping_check_task.cancel()

        # 그룹에서 나가기
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """ 클라이언트로부터 메시지 받을 때 실행 """
        # json 파싱
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error':'Invalid JSON'}))
            return

        message_type = data.get('type')

        # Ping/Pong 처리 (연결 유지 확인)
        if message_type == 'ping':
            self.last_ping = datetime.now()  # ping 받으면 시간 갱신
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))
            return

        # 심박수 데이터 처리
        if message_type == 'heart_rate':
            # 심박수 데이터 브로드캐스트
            player_id = data.get('player_id')
            bpm = data.get('bpm')

            # player_id 저장 (처음 심박수 받을 때)
            if not self.player_id:
                self.player_id = player_id
                # ping 체크 태스크 시작 (게임 중일 때만)
                if await self.is_player_playing(player_id):
                    self.ping_check_task = asyncio.create_task(self.check_ping_timeout())

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'send_heart_rate',
                    'player_id': player_id,
                    'bpm': bpm,
                }
            )
    async def send_heart_rate(self, event):
        """그룹의 모든 클라이언트에게 심박수 전송"""
        # WebSocket으로 메시지 보내기
        await self.send(text_data=json.dumps({
            'type': 'heart_rate',
            'player_id': event['player_id'],
            'bpm': event['bpm'],
        }))

    async def player_disconnected(self, event):
        """플레이어 연결 끊김 알림을 모든 클라이언트에게 전송"""
        await self.send(text_data=json.dumps({
            'type': 'player_disconnected',
            'player_id': event['player_id'],
            'nickname': event['nickname']
        }))

    @database_sync_to_async
    def is_player_playing(self, player_id):
        """플레이어가 PLAYING 상태인지 확인"""
        try:
            player = Player.objects.get(player_id=player_id)
            return player.status == Player.Status.PLAYING
        except Player.DoesNotExist:
            return False

    @database_sync_to_async
    def get_player_info(self, player_id):
        """플레이어 정보 가져오기"""
        try:
            player = Player.objects.get(player_id=player_id)
            return {
                'nickname': player.nickname,
                'status': player.status
            }
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def set_player_finished(self, player_id):
        """플레이어 상태를 FINISHED로 변경"""
        try:
            player = Player.objects.get(player_id=player_id)
            player.status = Player.Status.FINISHED
            player.save()
            return True
        except Player.DoesNotExist:
            return False

    async def check_ping_timeout(self):
        """
        5초마다 ping 타임아웃 체크
        15초(3번 실패) 동안 ping이 없으면 연결 끊김 처리
        """
        try:
            while True:
                await asyncio.sleep(5)  # 5초마다 체크

                # 마지막 ping이 15초 이상 지났으면
                if datetime.now() - self.last_ping > timedelta(seconds=15):
                    # 플레이어 정보 가져오기
                    player_info = await self.get_player_info(self.player_id)

                    if player_info:
                        # 플레이어 상태를 FINISHED로 변경
                        await self.set_player_finished(self.player_id)

                        # 방의 모든 사람에게 알림
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'player_disconnected',
                                'player_id': self.player_id,
                                'nickname': player_info['nickname']
                            }
                        )

                    # WebSocket 연결 끊기
                    await self.close()
                    break

        except asyncio.CancelledError:
            # 태스크가 취소되면 조용히 종료
            pass