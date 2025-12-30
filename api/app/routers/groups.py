from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime
from app.database import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.map import Map
from app.models.group import Group, GroupMember, GroupMap, GroupInvite
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupResponse,
    GroupWithMembers,
    GroupWithMaps,
    GroupMemberCreate,
    GroupMemberUpdate,
    GroupMemberInfo,
    GroupMapInfo,
    ShareMapWithGroup,
    GroupInviteCreate,
    GroupInviteResponse,
    GroupInviteAction,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])


# ============ Group CRUD ============

@router.post("", response_model=GroupWithMembers, status_code=status.HTTP_201_CREATED)
async def create_group(
    group_data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new group. The creator is automatically added as owner.
    Other members receive invitations.
    """
    # Create group
    group = Group(
        name=group_data.name,
        icon=group_data.icon,
        description=group_data.description,
        owner_id=current_user.id
    )
    db.add(group)
    await db.flush()
    
    # Add owner as member
    owner_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="owner"
    )
    db.add(owner_member)
    
    # Send invites to other members
    for member_id in group_data.member_ids:
        if member_id != current_user.id:
            # Check if user exists
            user_result = await db.execute(
                select(User).where(User.id == member_id)
            )
            user = user_result.scalar_one_or_none()
            if user:
                # Create invite
                invite = GroupInvite(
                    group_id=group.id,
                    invited_user_id=member_id,
                    invited_by_id=current_user.id,
                    status="pending"
                )
                db.add(invite)
    
    await db.commit()
    
    # Return with members
    return await get_group_with_members(group.id, db)


@router.get("", response_model=List[GroupResponse])
async def get_my_groups(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all groups the current user is a member of.
    """
    # Get group IDs where user is a member
    member_result = await db.execute(
        select(GroupMember.group_id).where(GroupMember.user_id == current_user.id)
    )
    group_ids = [row[0] for row in member_result.all()]
    
    if not group_ids:
        return []
    
    # Get groups with member count
    groups = []
    for group_id in group_ids:
        group_result = await db.execute(
            select(Group).where(Group.id == group_id)
        )
        group = group_result.scalar_one_or_none()
        
        if group:
            # Get member count
            count_result = await db.execute(
                select(func.count(GroupMember.id))
                .where(GroupMember.group_id == group_id)
            )
            member_count = count_result.scalar() or 0
            
            groups.append(GroupResponse(
                id=group.id,
                name=group.name,
                icon=group.icon,
                description=group.description,
                owner_id=group.owner_id,
                created_at=group.created_at,
                updated_at=group.updated_at,
                member_count=member_count
            ))
    
    return groups


@router.get("/{group_id}", response_model=GroupWithMaps)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get group details including members and shared maps.
    User must be a member of the group.
    """
    # Check if user is a member
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    return await get_group_with_maps(group_id, db)


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(
    group_id: str,
    group_data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a group. Only the owner or admins can update.
    """
    # Get group
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is owner or admin
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
        .where(GroupMember.role.in_(["owner", "admin"]))
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this group"
        )
    
    # Update fields
    if group_data.name is not None:
        group.name = group_data.name
    if group_data.icon is not None:
        group.icon = group_data.icon
    if group_data.description is not None:
        group.description = group_data.description
    
    await db.commit()
    await db.refresh(group)
    
    # Get member count
    count_result = await db.execute(
        select(func.count(GroupMember.id))
        .where(GroupMember.group_id == group_id)
    )
    member_count = count_result.scalar() or 0
    
    return GroupResponse(
        id=group.id,
        name=group.name,
        icon=group.icon,
        description=group.description,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=member_count
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a group. Only the owner can delete.
    """
    # Get group
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can delete the group"
        )
    
    await db.delete(group)
    await db.commit()


# ============ Member Management ============

@router.get("/{group_id}/members", response_model=list[GroupMemberInfo])
async def get_group_members(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all members of a group. Only members can see the member list.
    """
    # Check if group exists
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is a member
    member_check = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    if not member_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member to view the member list"
        )
    
    # Get all members with profiles
    members_result = await db.execute(
        select(GroupMember, Profile)
        .outerjoin(Profile, GroupMember.user_id == Profile.user_id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at)
    )
    
    members = []
    for member, profile in members_result.all():
        members.append(GroupMemberInfo(
            id=member.id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None
        ))
    
    return members


@router.post("/{group_id}/members", response_model=GroupMemberInfo, status_code=status.HTTP_201_CREATED)
async def add_member(
    group_id: str,
    member_data: GroupMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a member to the group. Only owner/admins can add members.
    """
    # Check if group exists
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is owner or admin
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
        .where(GroupMember.role.in_(["owner", "admin"]))
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add members"
        )
    
    # Check if user to add exists
    user_result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == member_data.user_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Add member
    member = GroupMember(
        group_id=group_id,
        user_id=member_data.user_id,
        role=member_data.role if member_data.role != "owner" else "member"  # Can't add another owner
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)
    
    # Get profile
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == member_data.user_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    return GroupMemberInfo(
        id=member.id,
        user_id=member.user_id,
        role=member.role,
        joined_at=member.joined_at,
        username=profile.username if profile else None,
        avatar_url=profile.avatar_url if profile else None
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a member from the group. Owner/admins can remove anyone except owner.
    Users can remove themselves (leave).
    """
    # Get group
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Can't remove the owner
    if user_id == group.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the owner from the group"
        )
    
    # Check permissions (must be owner, admin, or self)
    is_self = user_id == current_user.id
    if not is_self:
        member_result = await db.execute(
            select(GroupMember)
            .where(GroupMember.group_id == group_id)
            .where(GroupMember.user_id == current_user.id)
            .where(GroupMember.role.in_(["owner", "admin"]))
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove members"
            )
    
    # Find and remove member
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == user_id)
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    await db.delete(member)
    await db.commit()


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Leave the group. Owner cannot leave (must transfer ownership or delete).
    """
    # Get group
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    if group.owner_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot leave the group. Transfer ownership or delete the group."
        )
    
    # Find and remove member
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not a member of this group"
        )
    
    await db.delete(member)
    await db.commit()


# ============ Map Sharing ============

@router.get("/{group_id}/maps", response_model=List[GroupMapInfo])
async def get_group_maps(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all maps shared with this group.
    User must be a member of the group.
    """
    # Check if user is a member
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Get shared maps
    result = await db.execute(
        select(GroupMap, Map, Profile)
        .join(Map, Map.id == GroupMap.map_id)
        .outerjoin(Profile, Profile.user_id == GroupMap.shared_by)
        .where(GroupMap.group_id == group_id)
    )
    rows = result.all()
    
    return [
        GroupMapInfo(
            id=group_map.id,
            map_id=map_obj.id,
            map_name=map_obj.name,
            map_icon=map_obj.icon,
            shared_by=group_map.shared_by,
            shared_by_username=profile.username if profile else None,
            shared_at=group_map.shared_at
        )
        for group_map, map_obj, profile in rows
    ]


@router.post("/{group_id}/maps", response_model=GroupMapInfo, status_code=status.HTTP_201_CREATED)
async def share_map_with_group(
    group_id: str,
    share_data: ShareMapWithGroup,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Share a map with the group. User must be a member and must own or have access to the map.
    """
    # Check if user is a member
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Check if map exists and user has access
    map_result = await db.execute(
        select(Map).where(Map.id == share_data.map_id)
    )
    map_obj = map_result.scalar_one_or_none()
    
    if not map_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map not found"
        )
    
    # Check if user owns the map or is a member
    if map_obj.created_by != current_user.id:
        # TODO: Check map_members table
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this map"
        )
    
    # Check if already shared
    existing_result = await db.execute(
        select(GroupMap)
        .where(GroupMap.group_id == group_id)
        .where(GroupMap.map_id == share_data.map_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Map is already shared with this group"
        )
    
    # Create share
    group_map = GroupMap(
        group_id=group_id,
        map_id=share_data.map_id,
        shared_by=current_user.id
    )
    db.add(group_map)
    await db.commit()
    await db.refresh(group_map)
    
    # Get profile
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    
    return GroupMapInfo(
        id=group_map.id,
        map_id=map_obj.id,
        map_name=map_obj.name,
        map_icon=map_obj.icon,
        shared_by=current_user.id,
        shared_by_username=profile.username if profile else None,
        shared_at=group_map.shared_at
    )


@router.delete("/{group_id}/maps/{map_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_map(
    group_id: str,
    map_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a shared map from the group. 
    Only the person who shared it or group owner/admin can remove.
    """
    # Get the group map share
    share_result = await db.execute(
        select(GroupMap)
        .where(GroupMap.group_id == group_id)
        .where(GroupMap.map_id == map_id)
    )
    share = share_result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map is not shared with this group"
        )
    
    # Check permissions
    is_sharer = share.shared_by == current_user.id
    if not is_sharer:
        member_result = await db.execute(
            select(GroupMember)
            .where(GroupMember.group_id == group_id)
            .where(GroupMember.user_id == current_user.id)
            .where(GroupMember.role.in_(["owner", "admin"]))
        )
        if not member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove this map"
            )
    
    await db.delete(share)
    await db.commit()


# ============ Invites ============

@router.get("/invites/pending", response_model=List[GroupInviteResponse])
async def get_my_pending_invites(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all pending group invites for the current user.
    """
    result = await db.execute(
        select(GroupInvite)
        .where(GroupInvite.invited_user_id == current_user.id)
        .where(GroupInvite.status == "pending")
    )
    invites = result.scalars().all()
    
    invite_responses = []
    for invite in invites:
        # Get group
        group_result = await db.execute(
            select(Group).where(Group.id == invite.group_id)
        )
        group = group_result.scalar_one_or_none()
        
        if not group:
            continue
        
        # Get inviter profile
        profile_result = await db.execute(
            select(Profile).where(Profile.user_id == invite.invited_by_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        invite_responses.append(GroupInviteResponse(
            id=invite.id,
            group_id=group.id,
            group_name=group.name,
            group_icon=group.icon,
            invited_user_id=invite.invited_user_id,
            invited_by_id=invite.invited_by_id,
            invited_by_username=profile.username if profile else None,
            invited_by_avatar=profile.avatar_url if profile else None,
            status=invite.status,
            created_at=invite.created_at,
            responded_at=invite.responded_at
        ))
    
    return invite_responses


@router.post("/{group_id}/invites", response_model=GroupInviteResponse, status_code=status.HTTP_201_CREATED)
async def invite_to_group(
    group_id: str,
    invite_data: GroupInviteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invite a user to the group. Only owner/admins can invite.
    """
    # Check if group exists
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Check if user is owner or admin
    member_result = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == current_user.id)
        .where(GroupMember.role.in_(["owner", "admin"]))
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to invite members"
        )
    
    # Check if user to invite exists
    user_result = await db.execute(
        select(User).where(User.id == invite_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing_member = await db.execute(
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .where(GroupMember.user_id == invite_data.user_id)
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Check if there's already a pending invite
    existing_invite = await db.execute(
        select(GroupInvite)
        .where(GroupInvite.group_id == group_id)
        .where(GroupInvite.invited_user_id == invite_data.user_id)
        .where(GroupInvite.status == "pending")
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There's already a pending invite for this user"
        )
    
    # Create invite
    invite = GroupInvite(
        group_id=group_id,
        invited_user_id=invite_data.user_id,
        invited_by_id=current_user.id,
        status="pending"
    )
    db.add(invite)
    await db.commit()
    await db.refresh(invite)
    
    # Get inviter profile
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    
    return GroupInviteResponse(
        id=invite.id,
        group_id=group.id,
        group_name=group.name,
        group_icon=group.icon,
        invited_user_id=invite.invited_user_id,
        invited_by_id=invite.invited_by_id,
        invited_by_username=profile.username if profile else None,
        invited_by_avatar=profile.avatar_url if profile else None,
        status=invite.status,
        created_at=invite.created_at,
        responded_at=invite.responded_at
    )


@router.post("/invites/{invite_id}/respond", response_model=GroupInviteResponse)
async def respond_to_invite(
    invite_id: str,
    action_data: GroupInviteAction,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept or reject a group invite.
    """
    # Get invite
    result = await db.execute(
        select(GroupInvite).where(GroupInvite.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    if invite.invited_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invite is not for you"
        )
    
    if invite.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invite has already been responded to"
        )
    
    if action_data.action not in ["accept", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'accept' or 'reject'"
        )
    
    # Get group
    group_result = await db.execute(
        select(Group).where(Group.id == invite.group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group no longer exists"
        )
    
    # Update invite
    invite.status = "accepted" if action_data.action == "accept" else "rejected"
    invite.responded_at = datetime.utcnow()
    
    # If accepted, add as member
    if action_data.action == "accept":
        member = GroupMember(
            group_id=invite.group_id,
            user_id=current_user.id,
            role="member"
        )
        db.add(member)
    
    await db.commit()
    await db.refresh(invite)
    
    # Get inviter profile
    profile_result = await db.execute(
        select(Profile).where(Profile.user_id == invite.invited_by_id)
    )
    profile = profile_result.scalar_one_or_none()
    
    return GroupInviteResponse(
        id=invite.id,
        group_id=group.id,
        group_name=group.name,
        group_icon=group.icon,
        invited_user_id=invite.invited_user_id,
        invited_by_id=invite.invited_by_id,
        invited_by_username=profile.username if profile else None,
        invited_by_avatar=profile.avatar_url if profile else None,
        status=invite.status,
        created_at=invite.created_at,
        responded_at=invite.responded_at
    )


@router.delete("/invites/{invite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invite(
    invite_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending invite. Only the inviter or group owner can cancel.
    """
    # Get invite
    result = await db.execute(
        select(GroupInvite).where(GroupInvite.id == invite_id)
    )
    invite = result.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found"
        )
    
    if invite.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending invites can be cancelled"
        )
    
    # Check permissions
    is_inviter = invite.invited_by_id == current_user.id
    if not is_inviter:
        # Check if owner
        group_result = await db.execute(
            select(Group).where(Group.id == invite.group_id)
        )
        group = group_result.scalar_one_or_none()
        
        if not group or group.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to cancel this invite"
            )
    
    await db.delete(invite)
    await db.commit()


# ============ Helper Functions ============

async def get_group_with_members(group_id: str, db: AsyncSession) -> GroupWithMembers:
    """Get a group with its members."""
    group_result = await db.execute(
        select(Group).where(Group.id == group_id)
    )
    group = group_result.scalar_one_or_none()
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get members
    members_result = await db.execute(
        select(GroupMember).where(GroupMember.group_id == group_id)
    )
    members = members_result.scalars().all()
    
    member_infos = []
    for member in members:
        profile_result = await db.execute(
            select(Profile).where(Profile.user_id == member.user_id)
        )
        profile = profile_result.scalar_one_or_none()
        
        member_infos.append(GroupMemberInfo(
            id=member.id,
            user_id=member.user_id,
            role=member.role,
            joined_at=member.joined_at,
            username=profile.username if profile else None,
            avatar_url=profile.avatar_url if profile else None
        ))
    
    return GroupWithMembers(
        id=group.id,
        name=group.name,
        icon=group.icon,
        description=group.description,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=len(members),
        members=member_infos
    )


async def get_group_with_maps(group_id: str, db: AsyncSession) -> GroupWithMaps:
    """Get a group with its members and shared maps."""
    group_with_members = await get_group_with_members(group_id, db)
    
    # Get shared maps
    maps_result = await db.execute(
        select(GroupMap).where(GroupMap.group_id == group_id)
    )
    group_maps = maps_result.scalars().all()
    
    map_infos = []
    for gm in group_maps:
        # Get map
        map_result = await db.execute(
            select(Map).where(Map.id == gm.map_id)
        )
        map_obj = map_result.scalar_one_or_none()
        
        if map_obj:
            # Get sharer profile
            profile_result = await db.execute(
                select(Profile).where(Profile.user_id == gm.shared_by)
            )
            profile = profile_result.scalar_one_or_none()
            
            map_infos.append(GroupMapInfo(
                id=gm.id,
                map_id=map_obj.id,
                map_name=map_obj.name,
                map_icon=map_obj.icon,
                shared_by=gm.shared_by,
                shared_by_username=profile.username if profile else None,
                shared_at=gm.shared_at
            ))
    
    return GroupWithMaps(
        id=group_with_members.id,
        name=group_with_members.name,
        icon=group_with_members.icon,
        description=group_with_members.description,
        owner_id=group_with_members.owner_id,
        created_at=group_with_members.created_at,
        updated_at=group_with_members.updated_at,
        member_count=group_with_members.member_count,
        members=group_with_members.members,
        shared_maps=map_infos
    )
