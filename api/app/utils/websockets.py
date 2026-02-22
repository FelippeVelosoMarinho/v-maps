from fastapi import WebSocket
from typing import Dict, List, Any, Set
import asyncio
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 10


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self._connection_activity: Dict[WebSocket, float] = {}
        self._connection_user: Dict[WebSocket, str] = {}
        self._rooms: Dict[str, Set[WebSocket]] = {}
        self._connection_rooms: Dict[WebSocket, Set[str]] = {}
        self._friend_cache: Dict[str, List[str]] = {}

    def _record_activity(self, websocket: WebSocket):
        self._connection_activity[websocket] = time.monotonic()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self._record_activity(websocket)
        self._connection_user[websocket] = user_id
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        self._connection_activity.pop(websocket, None)
        self._connection_user.pop(websocket, None)
        for room_id in self._connection_rooms.pop(websocket, set()):
            s = self._rooms.get(room_id)
            if s:
                s.discard(websocket)
                if not s:
                    del self._rooms[room_id]
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"User {user_id} disconnected.")
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"No more active connections for user {user_id}.")

    def invalidate_friend_cache(self, user_id: str):
        """Call when friendship is accepted or removed (for either user)."""
        self._friend_cache.pop(user_id, None)

    async def send_personal_message(self, message: Any, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast(self, user_ids: List[str], message: Any):
        tasks = [self.send_personal_message(message, user_id) for user_id in user_ids]
        if tasks:
            await asyncio.gather(*tasks)

    def join_room(self, room_id: str, websocket: WebSocket):
        if room_id not in self._rooms:
            self._rooms[room_id] = set()
        self._rooms[room_id].add(websocket)
        if websocket not in self._connection_rooms:
            self._connection_rooms[websocket] = set()
        self._connection_rooms[websocket].add(room_id)

    def leave_room(self, room_id: str, websocket: WebSocket):
        self._connection_rooms.get(websocket, set()).discard(room_id)
        s = self._rooms.get(room_id)
        if s:
            s.discard(websocket)
            if not s:
                del self._rooms[room_id]

    async def broadcast_to_room(self, room_id: str, message: Any):
        sockets = self._rooms.get(room_id)
        if not sockets:
            return
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to room {room_id}: {e}")

    async def broadcast_trip_event(self, participant_ids: List[str], event_type: str, data: Dict[str, Any]):
        message = {"type": event_type, **data}
        await self.broadcast(participant_ids, message)

    async def broadcast_to_friends(self, user_id: str, message: Any, db: Any):
        friend_ids = self._friend_cache.get(user_id)
        if friend_ids is None:
            from sqlalchemy import select, or_, and_
            from app.models.friendship import Friendship, FriendshipStatus
            result = await db.execute(
                select(Friendship)
                .where(
                    and_(
                        Friendship.status == FriendshipStatus.ACCEPTED,
                        or_(
                            Friendship.requester_id == user_id,
                            Friendship.addressee_id == user_id
                        )
                    )
                )
            )
            friendships = result.scalars().all()
            friend_ids = [f.addressee_id if f.requester_id == user_id else f.requester_id for f in friendships]
            self._friend_cache[user_id] = friend_ids
        if friend_ids:
            await self.broadcast(friend_ids, message)

    async def _heartbeat_loop(self, websocket: WebSocket, user_id: str):
        """Send ping every HEARTBEAT_INTERVAL; close if no activity for HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                last = self._connection_activity.get(websocket)
                if last is not None and (time.monotonic() - last) > (HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT):
                    logger.info(f"Heartbeat timeout for user {user_id}, closing connection")
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                    return
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    return
        except asyncio.CancelledError:
            pass

    def record_activity(self, websocket: WebSocket):
        """Call when any message is received from the client (e.g. pong or any other)."""
        self._record_activity(websocket)


manager = ConnectionManager()
