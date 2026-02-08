from fastapi import WebSocket
from typing import Dict, List, Any
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # user_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections for user: {len(self.active_connections[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                logger.info(f"User {user_id} disconnected.")
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                logger.info(f"No more active connections for user {user_id}.")

    async def send_personal_message(self, message: Any, user_id: str):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast(self, user_ids: List[str], message: Any):
        """Send message to a list of users in parallel."""
        import asyncio
        tasks = [self.send_personal_message(message, user_id) for user_id in user_ids]
        if tasks:
            await asyncio.gather(*tasks)

    async def broadcast_trip_event(self, participant_ids: List[str], event_type: str, data: Dict[str, Any]):
        """Helper for trip-related broadcasts."""
        message = {
            "type": event_type,
            **data
        }
        await self.broadcast(participant_ids, message)

    async def broadcast_to_friends(self, user_id: str, message: Any, db: Any):
        """Send message to all friends of a user."""
        from sqlalchemy import select, or_, and_
        from app.models.friendship import Friendship, FriendshipStatus
        
        # Find all accepted friendships
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
        
        # Extract friend IDs
        friend_ids = []
        for f in friendships:
            fid = f.addressee_id if f.requester_id == user_id else f.requester_id
            friend_ids.append(fid)
            
        if friend_ids:
            await self.broadcast(friend_ids, message)

manager = ConnectionManager()
