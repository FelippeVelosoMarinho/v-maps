from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
from app.database import get_db
from app.models import Trip, TripParticipant, TripLocation, Map, MapMember, User
from app.schemas.trip import TripCreate, TripResponse, LocationUpdate, AddParticipantsRequest
from app.utils.dependencies import get_current_user

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
    
    # Verify user is owner or member of the map
    if map_obj.created_by != current_user.id:
        member_result = await db.execute(
            select(MapMember).where(
                (MapMember.map_id == trip_data.map_id) & 
                (MapMember.user_id == current_user.id)
            )
        )
        if not member_result.scalars().first():
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
    
    # Add creator as participant
    creator_participant = TripParticipant(
        trip_id=trip_id,
        user_id=current_user.id
    )
    db.add(creator_participant)
    
    # Add selected participants (if any)
    if trip_data.participant_ids:
        for user_id in trip_data.participant_ids:
            # Skip if user is the creator (already added)
            if user_id == current_user.id:
                continue
                
            # Verify user is a member of the map
            member_check = await db.execute(
                select(MapMember).where(
                    (MapMember.map_id == trip_data.map_id) & 
                    (MapMember.user_id == user_id)
                )
            )
            if member_check.scalars().first():
                participant = TripParticipant(
                    trip_id=trip_id,
                    user_id=user_id
                )
                db.add(participant)
    
    await db.commit()
    await db.refresh(trip)
    
    # Load relationships
    await db.refresh(trip, ["participants", "locations"])
    
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
    
    # Check access (owner or member)
    if map_obj.created_by != current_user.id:
        member_result = await db.execute(
            select(MapMember).where(
                (MapMember.map_id == map_id) & 
                (MapMember.user_id == current_user.id)
            )
        )
        if not member_result.scalars().first():
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Get active trips
    trips_result = await db.execute(
        select(Trip)
        .where((Trip.map_id == map_id) & (Trip.is_active == True))
        .order_by(Trip.started_at.desc())
    )
    trips = trips_result.scalars().all()
    
    # Load relationships
    for trip in trips:
        await db.refresh(trip, ["participants", "locations"])
    
    return trips


@router.post("/{trip_id}/join", response_model=TripResponse)
async def join_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join an active trip"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip is not active")
    
    # Check if already participating
    existing_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    
    if existing_result.scalars().first():
        raise HTTPException(status_code=400, detail="Already participating in this trip")
    
    # Add as participant
    participant = TripParticipant(
        trip_id=trip_id,
        user_id=current_user.id
    )
    
    db.add(participant)
    await db.commit()
    
    # Load relationships
    await db.refresh(trip, ["participants", "locations"])
    
    return trip


@router.post("/{trip_id}/add-participants", response_model=TripResponse)
async def add_participants(
    trip_id: str,
    request: AddParticipantsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add multiple participants to a trip (only trip creator can do this)"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip is not active")
    
    # Only creator can add participants
    if trip.created_by != current_user.id:
        raise HTTPException(
            status_code=403, 
            detail="Only the trip creator can add participants"
        )
    
    # Get current participants
    current_participants_result = await db.execute(
        select(TripParticipant).where(TripParticipant.trip_id == trip_id)
    )
    current_participant_ids = {p.user_id for p in current_participants_result.scalars().all()}
    
    # Add new participants (skip if already participating)
    added_count = 0
    for user_id in request.user_ids:
        if user_id not in current_participant_ids:
            # Verify user exists and has access to the map
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalars().first()
            
            if not user:
                continue  # Skip invalid user IDs
            
            # Check if user has access to the map
            map_result = await db.execute(select(Map).where(Map.id == trip.map_id))
            map_obj = map_result.scalars().first()
            
            if map_obj:
                has_access = map_obj.created_by == user_id
                if not has_access:
                    member_result = await db.execute(
                        select(MapMember).where(
                            (MapMember.map_id == trip.map_id) & 
                            (MapMember.user_id == user_id)
                        )
                    )
                    has_access = member_result.scalars().first() is not None
                
                if has_access:
                    participant = TripParticipant(
                        trip_id=trip_id,
                        user_id=user_id
                    )
                    db.add(participant)
                    added_count += 1
    
    if added_count > 0:
        await db.commit()
    
    # Load relationships
    await db.refresh(trip, ["participants", "locations"])
    
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
    
    await db.delete(participant)
    await db.commit()
    
    return {"message": "Left trip successfully"}


@router.post("/{trip_id}/end")
async def end_trip(
    trip_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a trip (only creator can do this)"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check permissions
    if trip.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only trip creator can end it")
    
    trip.is_active = False
    trip.ended_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Trip ended successfully"}


@router.post("/{trip_id}/location", response_model=dict)
async def update_location(
    trip_id: str,
    location: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user location for a trip"""
    
    # Get trip
    trip_result = await db.execute(select(Trip).where(Trip.id == trip_id))
    trip = trip_result.scalars().first()
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if not trip.is_active:
        raise HTTPException(status_code=400, detail="Trip is not active")
    
    # Check if user is participant
    participant_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    
    if not participant_result.scalars().first():
        raise HTTPException(status_code=403, detail="Not a participant in this trip")
    
    # Create location record
    trip_location = TripLocation(
        trip_id=trip_id,
        user_id=current_user.id,
        latitude=location.latitude,
        longitude=location.longitude,
        accuracy=location.accuracy
    )
    
    db.add(trip_location)
    await db.commit()
    
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
    
    # Check if user is participant
    participant_result = await db.execute(
        select(TripParticipant).where(
            (TripParticipant.trip_id == trip_id) & 
            (TripParticipant.user_id == current_user.id)
        )
    )
    
    if not participant_result.scalars().first():
        raise HTTPException(status_code=403, detail="Not a participant in this trip")
    
    # Get locations
    locations_result = await db.execute(
        select(TripLocation)
        .where(TripLocation.trip_id == trip_id)
        .order_by(TripLocation.recorded_at.desc())
    )
    locations = locations_result.scalars().all()
    
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
