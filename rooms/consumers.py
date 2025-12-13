import json
import asyncio
from datetime import datetime, timedelta
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Player, Room

# 방별 게임 상태 저장 (메모리)
game_states = {}

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ WebSocket 연결 시 실행 """
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'game_{self.room_id}'
        self.last_ping = datetime.now()
        self.player_id = None
        self.ping_check_task = None

        # 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # WebSocket 연결 수락
        await self.accept()

    async def disconnect(self, close_code):
        """ WebSocket 연결 해제 시 실행 """
        if self.ping_check_task:
            self.ping_check_task.cancel()

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """ 클라이언트로부터 메시지 받을 때 실행 """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({'error': 'Invalid JSON'}))
            return

        message_type = data.get('type')

        # Ping/Pong 처리
        if message_type == 'ping':
            self.last_ping = datetime.now()
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return

        # 플레이어 ready 상태 변경
        if message_type == 'player_ready':
            player_id = data.get('player_id')
            is_ready = data.get('is_ready', True)

            result = await self.set_player_ready_status(player_id, is_ready)

            if result:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_player_ready',
                        'player_id': player_id,
                        'is_ready': is_ready
                    }
                )
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Player not found'
                }))
            return

        # 심박수 데이터 처리
        if message_type in ['heart_rate', 'heartbeat']:
            player_id = data.get('player_id')
            bpm = data.get('bpm')

            if not self.player_id:
                self.player_id = player_id

            # 게임 상태에 bpm 저장
            if self.room_id in game_states:
                game_state = game_states[self.room_id]
                player_info = await self.get_player_info(player_id)
                nickname = player_info['nickname'] if player_info else 'Unknown'

                # 현재 bpm 저장
                game_state['current_bpm'][player_id] = {
                    'bpm': bpm,
                    'nickname': nickname
                }

                # bpm 기록 저장 (min, max 계산용)
                if player_id not in game_state['bpm_history']:
                    game_state['bpm_history'][player_id] = []
                game_state['bpm_history'][player_id].append(bpm)
            return

    # ==================== 브로드캐스트 핸들러 ====================

    async def send_player_ready(self, event):
        """플레이어 ready 상태 전송"""
        await self.send(text_data=json.dumps({
            'type': 'player_ready',
            'player_id': event['player_id'],
            'is_ready': event['is_ready']
        }))

    async def player_joined(self, event):
        """새 플레이어 참가 알림"""
        await self.send(text_data=json.dumps({
            'type': 'player_joined',
            'player': event['player'],
            'total_players': event['total_players']
        }))

    async def send_heart_rate(self, event):
        """심박수 전송 (레거시 지원)"""
        await self.send(text_data=json.dumps({
            'type': 'heart_rate',
            'player_id': event['player_id'],
            'bpm': event['bpm'],
        }))

    async def game_start(self, event):
        """게임 시작 브로드캐스트"""
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'total_time': event['total_time'],
            'min_bpm': event['min_bpm'],
            'max_bpm': event['max_bpm'],
            'target_bpm': event['target_bpm'],
            'players': event['players']
        }))

    async def bpm_update(self, event):
        """1초마다 정렬된 bpm 리스트 전송"""
        await self.send(text_data=json.dumps({
            'type': 'bpm_update',
            'rankings': event['rankings']
        }))

    async def game_end(self, event):
        """게임 종료 결과 전송"""
        await self.send(text_data=json.dumps({
            'type': 'game_end',
            'results': event['results']
        }))

    async def player_disconnected(self, event):
        """플레이어 연결 끊김 알림"""
        try:
            await self.send(text_data=json.dumps({
                'type': 'player_disconnected',
                'player_id': event['player_id'],
                'nickname': event['nickname']
            }))
        except Exception:
            pass

    # ==================== DB 헬퍼 함수 ====================

    @database_sync_to_async
    def is_player_playing(self, player_id):
        try:
            player = Player.objects.get(player_id=player_id)
            return player.status == Player.Status.PLAYING
        except Player.DoesNotExist:
            return False

    @database_sync_to_async
    def get_player_info(self, player_id):
        try:
            player = Player.objects.get(player_id=player_id)
            return {
                'player_id': player.player_id,
                'nickname': player.nickname,
                'status': player.status,
                'is_host': player.is_host
            }
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def set_player_ready_status(self, player_id, is_ready):
        try:
            player = Player.objects.get(player_id=player_id)
            player.status = Player.Status.READY if is_ready else Player.Status.WAITING
            player.save()
            return True
        except Player.DoesNotExist:
            return None

    @database_sync_to_async
    def set_player_finished(self, player_id):
        try:
            player = Player.objects.get(player_id=player_id)
            player.status = Player.Status.FINISHED
            player.save()
            return True
        except Player.DoesNotExist:
            return False

    async def check_ping_timeout(self):
        """5초마다 ping 타임아웃 체크"""
        try:
            while True:
                await asyncio.sleep(5)

                if datetime.now() - self.last_ping > timedelta(seconds=15):
                    player_info = await self.get_player_info(self.player_id)

                    if player_info:
                        await self.set_player_finished(self.player_id)
                        await self.channel_layer.group_send(
                            self.room_group_name,
                            {
                                'type': 'player_disconnected',
                                'player_id': self.player_id,
                                'nickname': player_info['nickname']
                            }
                        )

                    await self.close()
                    break

        except asyncio.CancelledError:
            pass


# ==================== 게임 루프 함수 (views.py에서 호출) ====================

async def start_game_loop(room_id, total_time, min_bpm, max_bpm, target_bpm, players, channel_layer):
    """게임 루프: 1초마다 bpm_update 브로드캐스트, 게임 종료 시 game_end 브로드캐스트"""

    room_group_name = f'game_{room_id}'

    # 게임 상태 초기화
    game_states[room_id] = {
        'current_bpm': {},  # {player_id: {'bpm': 80, 'nickname': '홍길동'}}
        'bpm_history': {},  # {player_id: [80, 82, 85, ...]}
        'mae_history': {},  # {player_id: [5, 3, 7, ...]}
        'target_bpm': target_bpm,
        'min_bpm': min_bpm,
        'max_bpm': max_bpm,
        'players': players
    }

    game_state = game_states[room_id]

    # 플레이어 초기화
    for player in players:
        game_state['current_bpm'][player['player_id']] = {
            'bpm': target_bpm,  # 초기값은 목표 bpm
            'nickname': player['nickname']
        }
        game_state['bpm_history'][player['player_id']] = []
        game_state['mae_history'][player['player_id']] = []

    # 게임 루프 (1초마다)
    for second in range(total_time):
        await asyncio.sleep(1)

        # 랭킹 계산
        rankings = []
        for player_id, data in game_state['current_bpm'].items():
            bpm = data['bpm']
            nickname = data['nickname']
            diff = abs(bpm - target_bpm)

            # MAE 기록
            game_state['mae_history'][player_id].append(diff)

            rankings.append({
                'player_id': player_id,
                'nickname': nickname,
                'bpm': bpm,
                'diff': diff
            })

        # 정렬: diff 낮은 순, 같으면 bpm 낮은 순
        rankings.sort(key=lambda x: (x['diff'], x['bpm']))

        # 브로드캐스트
        await channel_layer.group_send(
            room_group_name,
            {
                'type': 'bpm_update',
                'rankings': rankings
            }
        )

    # 게임 종료 - 결과 계산
    results = []
    for player_id, mae_list in game_state['mae_history'].items():
        if mae_list:
            avg_mae = sum(mae_list) / len(mae_list)
        else:
            avg_mae = 999

        bpm_list = game_state['bpm_history'].get(player_id, [])
        min_bpm_player = min(bpm_list) if bpm_list else 0
        max_bpm_player = max(bpm_list) if bpm_list else 0

        nickname = game_state['current_bpm'].get(player_id, {}).get('nickname', 'Unknown')

        results.append({
            'player_id': player_id,
            'nickname': nickname,
            'min_bpm': min_bpm_player,
            'max_bpm': max_bpm_player,
            'avg_mae': round(avg_mae, 2)
        })

    # 등수 정렬: avg_mae 낮은 순
    results.sort(key=lambda x: x['avg_mae'])

    # rank 추가
    for i, result in enumerate(results):
        result['rank'] = i + 1

    # game_end 브로드캐스트
    await channel_layer.group_send(
        room_group_name,
        {
            'type': 'game_end',
            'results': results
        }
    )

    # 게임 상태 정리
    del game_states[room_id]
