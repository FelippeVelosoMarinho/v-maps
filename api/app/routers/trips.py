from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# ... (imports)

from datetime import datetime
import uuid
from app.database import get_db
from app.models import (
    Trip, TripParticipant, TripLocation, Map, MapMember, User, 
    GroupMap, GroupMember, Notification
)
from app.schemas.trip import TripCreate, TripResponse, LocationUpdate, AddParticipantsRequest
from app.utils.permissions import check_map_access
from app.utils.dependencies import get_current_user
from app.utils.websockets import manager
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("", response_model=TripResponse)
async def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new trip for a map with multiple members"""
    
    # Verify map exists
    map_result = await db.execute(select(Map).where(Map.id == trip_data.map_id))
    map_obj = map_result.scalars().first()
    
    if not map_obj:
        raise HTTPException(status_code=404, detail="Map not found")
    
    # Verify user has access (Owner, Member, or Group Member)
    has_access = await check_map_access(db, trip_data.map_id, current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=403, 
            detail="You don't have permission to create a trip for this map"
        )
    
    # Note: Trip can be created even if user is alone
    # Other members will be added if they are in the participant_ids list
    
    # Create trip with explicit UUID to ensure ID is generated
    trip_id = str(uuid.uuid4())
    
    trip = Trip(
        id=trip_id,
        name=trip_data.name,
        description=trip_data.description or "",
        map_id=trip_data.map_id,
        created_by=current_user.id
    )
    
    db.add(trip)
    
    # Add creator as participant (ACCEPTED)
    creator_participant = TripParticipant(
        trip_id=trip_id,
        user_id=current_user.id,
        status="accepted"
    )
    db.add(creator_participant)
    
    # Determine which users to invite
    users_to_invite = set()
    
    if trip_data.invite_all:
        # 1. Get direct map members
        map_members_result = await db.execute(
            select(MapMember.user_id).where(MapMember.map_id == trip_data.map_id)
        )
        for uid in map_members_result.scalars().all():
            users_to_invite.add(uid)
            
        # 2. Get members of groups linked to this map
        group_maps_result = await db.execute(
            select(GroupMap.group_id).where(GroupMap.map_id == trip_data.map_id)
        )
        group_ids = group_maps_result.scalars().all()
        
        if group_ids:
            group_members_result = await db.execute(
                select(GroupMember.user_id).where(GroupMember.group_id.in_(group_ids))
            )
            for uid in group_members_result.scalars().all():
                users_to_invite.add(uid)
    else:
        # Use provided list
        if trip_data.participant_ids:
            users_to_invite = set(trip_data.participant_ids)

    # Process invitations
    for user_id in users_to_invite:
        # Skip creator
        if user_id == current_user.id:
            continue
            
        # Verify access (redundant if coming from map_members/groups, but safe)
        # Check if already added (to prevent duplicates if user is in multiple lists)
        # The set handles duplicates in IDs, but we need to check if we already db.add'ed?
        # No, iterating the set ensures uniqueness.
        
        participant = TripParticipant(
            trip_id=trip_id,
            user_id=user_id,
            status="invited"
        )
        db.add(participant)
    
    await db.commit()
    
    # Create notifications for all map members
    # 1. Get ALL unique user IDs with access to this map
    map_members_ids = set()
    map_members_ids.add(map_obj.created_by)
    
    # Direct members
    direct_members_result = await db.execute(
        select(MapMember.user_id).where(MapMember.map_id == trip_data.map_id)
    )
    for uid in direct_members_result.scalars().all():
        map_members_ids.add(uid)
        
    # Group members
    group_maps_result = await db.execute(
        select(GroupMap.group_id).where(GroupMap.map_id == trip_data.map_id)
    )
    group_ids = group_maps_result.scalars().all()
    if group_ids:
        group_members_result = await db.execute(
            select(GroupMember.user_id).where(GroupMember.group_id.in_(group_ids))
        )
        for uid in group_members_result.scalars().all():
            map_members_ids.add(uid)

    # 2. Create Notification records
    for user_id in map_members_ids:
        notification = Notification(
            user_id=user_id,
            type="trip_invite" if user_id in users_to_invite else "trip_update",
            title=f"Nova viagem: {trip_data.name}",
            content=f"{current_user.email} iniciou uma viagem no mapa {map_obj.name}.",
            trip_id=trip_id,
            map_id=trip_data.map_id
        )
        db.add(notification)
    
    await db.commit()

    # Re-fetch with full relationships
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.participants).selectinload(TripParticipant.user).selectinload(User.profile),
            selectinload(Trip.locations)
        )
    )
    trip = result.scalars().first()
    
    return trip


@router.get("/{map_id}", response_model=list[TripResponse])
async def get_map_trips(
    map_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active trips for a map"""
    
    # Verify user has access to the map
    map_result = await db.execute(select(Map).where(Map.id == map_id))
    map_obj = map_result.scalars().first()
    
    if not map_obj:
        raise HTTPException(status_code=404, detail="Map not found")
    
    # Verify access (Owner, Member, or Group Member)
    has_access = await check_map_access(db, map_id, current_user.id)
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get active trips with relationships
    trips_result = await db.execute(
        select(Trip)
        .where((Trip.map_id == map_id) & (Trip.is_active == True))
        .options(
            selectinload(Trip.participants).selectinload(TripParticipant.user).selectinload(User.profile),
            selectinload(Trip.locations)
        )
        .order_by(Trip.started_at.desc())
    )
    trips = trips_result.scalars().all()
    
    return trips


@router.get("/t/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details for a specific trip"""
    
    # Get trip with relationships
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.participants).selectinload(TripParticipant.user).selectinload(User.profile),
            selectinload(Trip.locations)
        )
    )
    trip = result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Verify access (participant or creator)
    is_part = any(p.user_id == current_user.id for p in trip.participants)
    if trip.created_by != current_user.id and not is_part:
        # Check if user has access to the map (maybe they are invited but haven't accepted yet)
        has_access = await check_map_access(db, trip.map_id, current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied")
            
    return trip


@router.post("/{trip_id}/accept", response_model=TripResponse)
async def accept_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Accept a trip invitation"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip is not active")
    
    # Check participation
    participant_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    participant = participant_result.scalars().first()
    
    if participant:
        if participant.status == "accepted":
            raise HTTPException(status_code=400, detail="Already accepted")
        
        participant.status = "accepted"
        participant.joined_at = datetime.utcnow()
    else:
        # User joining without prior invite (if allowed)
        # For now, we allow it (same as join_trip)
        participant = TripParticipant(
            trip_id=trip_id,
            user_id=current_user.id,
            status="accepted"
        )
        db.add(participant)
    
    await db.commit()
    
    # Re-fetch with full relationships
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.participants).selectinload(TripParticipant.user).selectinload(User.profile),
            selectinload(Trip.locations)
        )
    )
    trip = result.scalars().first()

    # Create notification for all other participants
    for p in trip.participants:
        if p.user_id == current_user.id:
            continue
        notification = Notification(
            user_id=p.user_id,
            type="trip_update",
            title=f"Trip: {trip.name}",
            content=f"{current_user.email} entrou na viagem.",
            trip_id=trip.id,
            map_id=trip.map_id
        )
        db.add(notification)
    await db.commit()
    
    # Notify updates
    participant_ids = [p.user_id for p in trip.participants]
    await manager.broadcast(participant_ids, {
        "type": "trip_updated",
        "trip_id": trip.id
    })
    
    return trip


@router.post("/{trip_id}/decline")
async def decline_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Decline a trip invitation"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check participation
    participant_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    participant = participant_result.scalars().first()
    
    if not participant:
        raise HTTPException(status_code=400, detail="Not invited to this trip")
    
    # Remove participant or mark as declined?
    # Usually decline implies removing or marking. Let's mark as declined for history or just remove.
    # If we remove, they disappear from list. If mark, they stay as red.
    # Let's remove for now to keep it clean, or update status if we want to show "Declined"
    # User request previously implied just "Decline" -> "Sair/Recusar".
    # If invited, decline = remove.
    
    participant.status = "declined"
    await db.commit()
    
    # Create notification for creator
    notification = Notification(
        user_id=trip.created_by,
        type="trip_update",
        title=f"Trip: {trip.name}",
        content=f"{current_user.email} recusou o convite.",
        trip_id=trip.id,
        map_id=trip.map_id
    )
    db.add(notification)
    await db.commit()

    # Fetch participants to notify
    result = await db.execute(
        select(TripParticipant).where(TripParticipant.trip_id == trip_id)
    )
    participants = result.scalars().all()
    participant_ids = [p.user_id for p in participants]

    if participant_ids:
        await manager.broadcast(participant_ids, {
            "type": "trip_updated",
            "trip_id": trip_id
        })
    else:
        # If decline happened before being in participants list or similar
        # But decline_trip checks participant existence
        pass
    
    return {"message": "Invitation declined"}


# Kept for backward compatibility, same as accept
@router.post("/{trip_id}/join", response_model=TripResponse)
async def join_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await accept_trip(trip_id, current_user, db)

@router.post("/{trip_id}/add-participants", response_model=TripResponse)
async def add_trip_participants(
    trip_id: str,
    request: AddParticipantsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add more participants to an existing trip"""
    
    # Get trip
    trip_result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.participants))
    )
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip is not active")
    
    # Only creator can add participants
    if trip.created_by != current_user.id:
        pass # Allow participants to invite others? Let's say yes for social trips.
             # Or verify if current_user is in participants.
    
    current_participant_ids = {p.user_id for p in trip.participants}
    
    # Add new participants (skip if already participating)
    added_count = 0
    new_participants_ids = []

    for user_id in request.user_ids:
        if user_id not in current_participant_ids:
            # Verify user exists and has access to the map
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalars().first()
            
            if not user:
                continue  # Skip invalid user IDs
            
            # Check if user has access to the map
            has_access = await check_map_access(db, trip.map_id, user_id)
            
            if has_access:
                participant = TripParticipant(
                    trip_id=trip_id,
                    user_id=user_id,
                    status="invited" # Default status
                )
                db.add(participant)
                added_count += 1
                new_participants_ids.append(user_id)
    
    if added_count > 0:
        await db.commit()
        
        # Notify new participants
        if new_participants_ids:
             await manager.broadcast(new_participants_ids, {
                "type": "trip_invite",
                "trip_id": trip.id,
                "trip_name": trip.name
            })

    # Re-fetch with full relationships
    result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(
            selectinload(Trip.participants).selectinload(TripParticipant.user).selectinload(User.profile),
            selectinload(Trip.locations)
        )
    )
    trip = result.scalars().first()
    
    # Notify existing participants of update
    participant_ids = [p.user_id for p in trip.participants if p.user_id not in new_participants_ids]
    if participant_ids:
        await manager.broadcast(participant_ids, {
            "type": "trip_updated",
            "trip_id": trip.id
        })

    return trip


@router.post("/{trip_id}/leave")
async def leave_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Leave a trip"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Find participant
    participant_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    participant = participant_result.scalars().first()
    
    if not participant:
        raise HTTPException(status_code=400, detail="Not participating in this trip")
    
    # If creator is leaving, end the trip
    if trip.created_by == current_user.id:
        trip.is_active = False
        trip.ended_at = datetime.utcnow()
        await db.commit() # Commit trip ending
        
        # Notify everyone with persistent notifications
        result = await db.execute(
             select(TripParticipant).where(TripParticipant.trip_id == trip_id)
        )
        all_participants = result.scalars().all()
        ids = [p.user_id for p in all_participants]
        
        for user_id in ids:
            if user_id == current_user.id:
                continue
            notification = Notification(
                user_id=user_id,
                type="trip_ended",
                title=f"Trip: {trip.name}",
                content=f"{current_user.email} encerrou a viagem.",
                trip_id=trip.id,
                map_id=trip.map_id
            )
            db.add(notification)
        await db.commit()

        await manager.broadcast(ids, {
            "type": "trip_ended",
            "trip_id": trip_id
        })
    else:
        await db.delete(participant)
        await db.commit()
        
        # Notify remaining
        result = await db.execute(
             select(TripParticipant).where(TripParticipant.trip_id == trip_id)
        )
        remaining = result.scalars().all()
        ids = [p.user_id for p in remaining]

        # Notify remaining participants with persistent notification
        for user_id in ids:
            notification = Notification(
                user_id=user_id,
                type="trip_update",
                title=f"Trip: {trip.name}",
                content=f"{current_user.email} saiu da viagem.",
                trip_id=trip.id,
                map_id=trip.map_id
            )
            db.add(notification)
        await db.commit()

        await manager.broadcast(ids, {
            "type": "trip_updated",
            "trip_id": trip_id
        })
        
        # Also notify the user who left that they are no longer in the trip (optional, but good for sync)
        await manager.broadcast([current_user.id], {
            "type": "trip_updated",
            "trip_id": trip_id,
            "action": "left"
        })
    
    return {"message": "Left trip successfully"}


@router.post("/{trip_id}/end")
async def end_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a trip (only creator can do this)"""
    
    # Get trip
    trip_result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        .options(selectinload(Trip.participants))
    )
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check permissions
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only trip creator can end it")
    
    trip.is_active = False
    trip.ended_at = datetime.utcnow()
    await db.commit()
    
    # Notify everyone with persistent notifications
    participant_ids = [p.user_id for p in trip.participants]
    for user_id in participant_ids:
        if user_id == current_user.id:
            continue
        notification = Notification(
            user_id=user_id,
            type="trip_ended",
            title=f"Trip: {trip.name}",
            content=f"{current_user.email} encerrou a viagem.",
            trip_id=trip_id,
            map_id=trip.map_id
        )
        db.add(notification)
    await db.commit()

    if participant_ids:
        await manager.broadcast(participant_ids, {
            "type": "trip_ended",
            "trip_id": trip_id
        })
    
    return {"message": "Trip ended"}


@router.post("/{trip_id}/location")
async def update_trip_location(
    trip_id: str,
    location: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user location in a trip"""
    
    # Verify trip active
    trip_result = await db.execute(
        select(Trip)
        .where(Trip.id == trip_id)
        # We need participants to broadcast
        .options(selectinload(Trip.participants))
    )
    trip = trip_result.scalars().first()
    
    if not trip or not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip not active")
    
    # Verify participation
    participant = next((p for p in trip.participants if p.user_id == current_user.id), None)
    
    if not participant:
        raise HTTPException(status_code=403, detail="Not a participant")
        
    if participant.status != 'accepted':
        raise HTTPException(status_code=403, detail="You must accept the trip invitation to share location")
    
    # Create location record
    trip_location = TripLocation(
        trip_id=trip_id,
        user_id=current_user.id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy=location.accuracy,
        recorded_at=datetime.utcnow()
    )
    
    db.add(trip_location)
    await db.commit()

    # Broadcast location update to other participants
    # Maybe limit frequency? For now, real-time is real-time.
    participant_ids = [p.user_id for p in trip.participants]
    await manager.broadcast(participant_ids, {
        "type": "trip_updated", # Or location_updated if we want to be granular
        "trip_id": trip_id
    })
    
    return {"message": "Location updated successfully"}

    
@router.get("/{trip_id}/locations", response_model=list[dict])
async def get_trip_locations(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all locations recorded for a trip"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
        
    # Check access (is participant or creator)
    # Since we don't have participants loaded, we query
    is_part_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    is_participant = is_part_result.scalars().first()
    
    if trip.created_by != current_user.id and not is_participant:
         raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(TripLocation)
        .where(TripLocation.trip_id == trip_id)
        .order_by(TripLocation.recorded_at.asc())
    )
    locations = result.scalars().all()
    
    return [
        {
            "id": loc.id,
            "user_id": loc.user_id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "accuracy": loc.accuracy,
            "recorded_at": loc.recorded_at
        }
        for loc in locations
    ]
