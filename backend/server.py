from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
import uuid
from datetime import datetime, timezone, date
from enum import Enum
import random
import string

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Netly API", description="Tennis & Pickleball League Management API")
api_router = APIRouter(prefix="/api")

# Enums
class UserRole(str, Enum):
    PLAYER = "Player"
    LEAGUE_MANAGER = "League Manager"
    ADMIN = "Admin"

class SportType(str, Enum):
    TENNIS = "Tennis"
    PICKLEBALL = "Pickleball"

class SeasonStatus(str, Enum):
    DRAFT = "Draft"
    ACTIVE = "Active"
    COMPLETED = "Completed"

class MatchStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    PLAYED = "Played"
    CANCELLED = "Cancelled"

class PlayerSeatStatus(str, Enum):
    ACTIVE = "Active"
    RESERVE = "Reserve"
    BANNED = "Banned"

class AvailabilityStatus(str, Enum):
    YES = "Yes"
    NO = "No"
    MAYBE = "Maybe"

class LeagueFormat(str, Enum):
    SINGLES = "Singles"
    DOUBLES = "Doubles"

class NotificationType(str, Enum):
    LEAGUE_INVITE = "League Invite"
    MATCH_SCHEDULED = "Match Scheduled"
    SCORE_SUBMITTED = "Score Submitted"
    SEASON_CREATED = "Season Created"
    TIER_ADDED = "Tier Added"

# Utility functions
def generate_join_code():
    """Generate a unique 6-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def prepare_for_mongo(data):
    """Convert datetime objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, date):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse datetime strings back from MongoDB and remove ObjectId fields"""
    if isinstance(item, dict):
        # Remove MongoDB ObjectId field
        if '_id' in item:
            del item['_id']
        
        for key, value in item.items():
            if isinstance(value, str) and 'T' in value:
                try:
                    item[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass
    return item

# Enhanced Pydantic Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = Field(ge=3.0, le=5.5)
    photo_url: Optional[str] = None
    role: UserRole = UserRole.PLAYER
    sports_preferences: List[SportType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfileCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = Field(ge=3.0, le=5.5)
    photo_url: Optional[str] = None
    role: UserRole = UserRole.PLAYER

class SportPreferenceUpdate(BaseModel):
    sports_preferences: List[SportType]

# Notification Model
class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: NotificationType
    sport_type: Optional[SportType] = None
    related_entity_id: Optional[str] = None  # season_id, tier_id, match_id etc.
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: NotificationType
    sport_type: Optional[SportType] = None
    related_entity_id: Optional[str] = None

# 3-Tier League Structure Models with Sport Type
class MainSeason(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Season 14"
    sport_type: SportType
    description: Optional[str] = None
    start_date: date
    end_date: date
    status: SeasonStatus = SeasonStatus.DRAFT
    created_by: str  # League Manager ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MainSeasonCreate(BaseModel):
    name: str
    sport_type: SportType
    description: Optional[str] = None
    start_date: date
    end_date: date

class FormatTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    main_season_id: str
    name: str  # e.g., "Singles", "Doubles"
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FormatTierCreate(BaseModel):
    main_season_id: str
    name: str
    description: Optional[str] = None

class SkillTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    format_tier_id: str
    name: str  # e.g., "4.0", "4.5", "5.0"
    min_rating: float
    max_rating: float
    max_players: int = 36
    join_code: str = Field(default_factory=generate_join_code)
    region: str = "General"
    surface: str = "Hard Court"
    rules_md: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SkillTierCreate(BaseModel):
    format_tier_id: str
    name: str
    min_rating: float
    max_rating: float
    max_players: int = 36
    region: str = "General"
    surface: str = "Hard Court"
    rules_md: Optional[str] = None

# Updated Player Seat for Skill Tier
class PlayerSeat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_tier_id: str
    user_id: str
    status: PlayerSeatStatus = PlayerSeatStatus.ACTIVE
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JoinByCodeRequest(BaseModel):
    join_code: str

# Existing models with minor updates
class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_tier_id: str
    week_number: int
    format: LeagueFormat
    scheduled_at: Optional[datetime] = None
    venue_id: Optional[str] = None
    status: MatchStatus = MatchStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DoublesSet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    set_index: int
    team_a: List[str] = Field(min_length=2, max_length=2)
    team_b: List[str] = Field(min_length=2, max_length=2)
    score_a: int = Field(ge=0)
    score_b: int = Field(ge=0)

class Availability(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_tier_id: str
    user_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AvailabilityCreate(BaseModel):
    skill_tier_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None

class StandingSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    skill_tier_id: str
    player_id: str
    total_set_wins: int = 0
    total_sets_played: int = 0
    win_pct: float = 0.0
    rank: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Notification Helper Function
async def create_notification(notification_data: NotificationCreate):
    """Helper function to create notifications"""
    notification_obj = Notification(**notification_data.dict())
    notification_mongo = prepare_for_mongo(notification_obj.dict())
    await db.notifications.insert_one(notification_mongo)
    return notification_obj

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to Netly - Tennis & Pickleball League Management API"}

# User Profile Routes
@api_router.post("/users", response_model=UserProfile)
async def create_user(user_data: UserProfileCreate):
    user_dict = user_data.dict()
    user_obj = UserProfile(**user_dict)
    user_mongo = prepare_for_mongo(user_obj.dict())
    await db.users.insert_one(user_mongo)
    
    # Create welcome notification
    welcome_notification = NotificationCreate(
        user_id=user_obj.id,
        title="Welcome to Netly!",
        message=f"Welcome {user_obj.name}! You're ready to join tennis and pickleball leagues.",
        type=NotificationType.LEAGUE_INVITE
    )
    await create_notification(welcome_notification)
    
    return user_obj

@api_router.get("/users", response_model=List[UserProfile])
async def get_users():
    users = await db.users.find().to_list(100)
    return [UserProfile(**parse_from_mongo(user)) for user in users]

@api_router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**parse_from_mongo(user))

@api_router.patch("/users/{user_id}/sports", response_model=UserProfile)
async def update_user_sports(user_id: str, preferences: SportPreferenceUpdate):
    """Update user's sport preferences"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"sports_preferences": [sport.value for sport in preferences.sports_preferences]}}
    )
    
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**parse_from_mongo(updated_user))

# Notification Routes
@api_router.get("/users/{user_id}/notifications", response_model=List[Notification])
async def get_user_notifications(user_id: str, unread_only: bool = False):
    """Get user notifications"""
    query = {"user_id": user_id}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(query).sort("created_at", -1).to_list(50)
    return [Notification(**parse_from_mongo(notification)) for notification in notifications]

@api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification marked as read"}

# Main Season Routes (League Manager Only) - Enhanced with Sport Type
@api_router.post("/main-seasons", response_model=MainSeason)
async def create_main_season(season_data: MainSeasonCreate, created_by: str):
    # Verify user is League Manager
    user = await db.users.find_one({"id": created_by})
    if not user or user["role"] != UserRole.LEAGUE_MANAGER:
        raise HTTPException(status_code=403, detail="Only League Managers can create seasons")
    
    season_dict = season_data.dict()
    season_dict["created_by"] = created_by
    season_obj = MainSeason(**season_dict)
    season_mongo = prepare_for_mongo(season_obj.dict())
    await db.main_seasons.insert_one(season_mongo)
    
    # Create notification for season creation
    season_notification = NotificationCreate(
        user_id=created_by,
        title=f"New {season_obj.sport_type} Season Created",
        message=f"Successfully created {season_obj.name} for {season_obj.sport_type}",
        type=NotificationType.SEASON_CREATED,
        sport_type=season_obj.sport_type,
        related_entity_id=season_obj.id
    )
    await create_notification(season_notification)
    
    return season_obj

@api_router.get("/main-seasons", response_model=List[MainSeason])
async def get_main_seasons(sport_type: Optional[SportType] = None):
    query = {}
    if sport_type:
        query["sport_type"] = sport_type.value
    
    seasons = await db.main_seasons.find(query).to_list(100)
    return [MainSeason(**parse_from_mongo(season)) for season in seasons]

@api_router.get("/users/{user_id}/main-seasons", response_model=List[MainSeason])
async def get_user_main_seasons(user_id: str, sport_type: Optional[SportType] = None):
    query = {"created_by": user_id}
    if sport_type:
        query["sport_type"] = sport_type.value
    
    seasons = await db.main_seasons.find(query).to_list(100)
    return [MainSeason(**parse_from_mongo(season)) for season in seasons]

# Format Tier Routes
@api_router.post("/format-tiers", response_model=FormatTier)
async def create_format_tier(tier_data: FormatTierCreate):
    # Verify main season exists
    main_season = await db.main_seasons.find_one({"id": tier_data.main_season_id})
    if not main_season:
        raise HTTPException(status_code=404, detail="Main season not found")
    
    tier_dict = tier_data.dict()
    tier_obj = FormatTier(**tier_dict)
    tier_mongo = prepare_for_mongo(tier_obj.dict())
    await db.format_tiers.insert_one(tier_mongo)
    
    # Create notification for tier addition
    tier_notification = NotificationCreate(
        user_id=main_season["created_by"],
        title=f"{tier_obj.name} Format Added",
        message=f"Added {tier_obj.name} format to {main_season['name']}",
        type=NotificationType.TIER_ADDED,
        sport_type=SportType(main_season["sport_type"]),
        related_entity_id=tier_obj.id
    )
    await create_notification(tier_notification)
    
    return tier_obj

@api_router.get("/main-seasons/{main_season_id}/format-tiers", response_model=List[FormatTier])
async def get_format_tiers(main_season_id: str):
    tiers = await db.format_tiers.find({"main_season_id": main_season_id}).to_list(100)
    return [FormatTier(**parse_from_mongo(tier)) for tier in tiers]

# Skill Tier Routes
@api_router.post("/skill-tiers", response_model=SkillTier)
async def create_skill_tier(tier_data: SkillTierCreate):
    # Verify format tier exists
    format_tier = await db.format_tiers.find_one({"id": tier_data.format_tier_id})
    if not format_tier:
        raise HTTPException(status_code=404, detail="Format tier not found")
    
    # Get main season for notification
    main_season = await db.main_seasons.find_one({"id": format_tier["main_season_id"]})
    
    tier_dict = tier_data.dict()
    tier_obj = SkillTier(**tier_dict)
    tier_mongo = prepare_for_mongo(tier_obj.dict())
    await db.skill_tiers.insert_one(tier_mongo)
    
    # Create notification for skill tier creation
    if main_season:
        skill_notification = NotificationCreate(
            user_id=main_season["created_by"],
            title=f"Skill Tier {tier_obj.name} Created",
            message=f"Created {tier_obj.name} skill tier with join code: {tier_obj.join_code}",
            type=NotificationType.TIER_ADDED,
            sport_type=SportType(main_season["sport_type"]),
            related_entity_id=tier_obj.id
        )
        await create_notification(skill_notification)
    
    return tier_obj

@api_router.get("/format-tiers/{format_tier_id}/skill-tiers", response_model=List[SkillTier])
async def get_skill_tiers(format_tier_id: str):
    tiers = await db.skill_tiers.find({"format_tier_id": format_tier_id}).to_list(100)
    return [SkillTier(**parse_from_mongo(tier)) for tier in tiers]

@api_router.get("/skill-tiers/{skill_tier_id}", response_model=SkillTier)
async def get_skill_tier(skill_tier_id: str):
    tier = await db.skill_tiers.find_one({"id": skill_tier_id})
    if not tier:
        raise HTTPException(status_code=404, detail="Skill tier not found")
    return SkillTier(**parse_from_mongo(tier))

# Join by Code Route with Enhanced Notifications
@api_router.post("/join-by-code/{user_id}")
async def join_by_code(user_id: str, request: JoinByCodeRequest):
    # Find skill tier by join code
    skill_tier = await db.skill_tiers.find_one({"join_code": request.join_code})
    if not skill_tier:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user already joined
    existing_seat = await db.player_seats.find_one({"skill_tier_id": skill_tier["id"], "user_id": user_id})
    if existing_seat:
        raise HTTPException(status_code=400, detail="User already joined this tier")
    
    # Check rating compatibility
    if not (skill_tier["min_rating"] <= user["rating_level"] <= skill_tier["max_rating"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Rating {user['rating_level']} not suitable for tier {skill_tier['name']} ({skill_tier['min_rating']}-{skill_tier['max_rating']})"
        )
    
    # Count current players
    player_count = await db.player_seats.count_documents({
        "skill_tier_id": skill_tier["id"], 
        "status": PlayerSeatStatus.ACTIVE
    })
    
    # Determine status based on capacity
    status = PlayerSeatStatus.ACTIVE if player_count < skill_tier["max_players"] else PlayerSeatStatus.RESERVE
    
    seat_obj = PlayerSeat(skill_tier_id=skill_tier["id"], user_id=user_id, status=status)
    seat_mongo = prepare_for_mongo(seat_obj.dict())
    await db.player_seats.insert_one(seat_mongo)
    
    # Get sport type for notification
    format_tier = await db.format_tiers.find_one({"id": skill_tier["format_tier_id"]})
    main_season = await db.main_seasons.find_one({"id": format_tier["main_season_id"]}) if format_tier else None
    
    # Create join notification for player
    join_notification = NotificationCreate(
        user_id=user_id,
        title=f"Joined {skill_tier['name']} Tier",
        message=f"Successfully joined {skill_tier['name']} with {status} status",
        type=NotificationType.LEAGUE_INVITE,
        sport_type=SportType(main_season["sport_type"]) if main_season else None,
        related_entity_id=skill_tier["id"]
    )
    await create_notification(join_notification)
    
    # Notify league manager about new player
    if main_season:
        manager_notification = NotificationCreate(
            user_id=main_season["created_by"],
            title="New Player Joined",
            message=f"{user['name']} joined {skill_tier['name']} tier",
            type=NotificationType.LEAGUE_INVITE,
            sport_type=SportType(main_season["sport_type"]),
            related_entity_id=skill_tier["id"]
        )
        await create_notification(manager_notification)
    
    return {
        "message": f"Successfully joined {skill_tier['name']} with status: {status}",
        "status": status,
        "skill_tier": SkillTier(**parse_from_mongo(skill_tier))
    }

# Player Dashboard Routes with Sport Filtering
@api_router.get("/users/{user_id}/joined-tiers")
async def get_user_joined_tiers(user_id: str, sport_type: Optional[SportType] = None):
    # Get player seats
    seats = await db.player_seats.find({"user_id": user_id}).to_list(100)
    
    result = []
    for seat in seats:
        # Get skill tier details
        skill_tier = await db.skill_tiers.find_one({"id": seat["skill_tier_id"]})
        if not skill_tier:
            continue
            
        # Get format tier details
        format_tier = await db.format_tiers.find_one({"id": skill_tier["format_tier_id"]})
        if not format_tier:
            continue
            
        # Get main season details
        main_season = await db.main_seasons.find_one({"id": format_tier["main_season_id"]})
        if not main_season:
            continue
        
        # Filter by sport type if specified
        if sport_type and main_season["sport_type"] != sport_type.value:
            continue
        
        tier_info = {
            "seat_id": seat["id"],
            "status": seat["status"],
            "joined_at": seat["joined_at"],
            "skill_tier": SkillTier(**parse_from_mongo(skill_tier)),
            "format_tier": FormatTier(**parse_from_mongo(format_tier)),
            "main_season": MainSeason(**parse_from_mongo(main_season))
        }
        result.append(tier_info)
    
    return result

@api_router.get("/users/{user_id}/standings")
async def get_user_standings(user_id: str, sport_type: Optional[SportType] = None):
    standings = await db.standings.find({"player_id": user_id}).to_list(100)
    
    result = []
    for standing in standings:
        # Get skill tier details
        skill_tier = await db.skill_tiers.find_one({"id": standing["skill_tier_id"]})
        if not skill_tier:
            continue
        
        # Get format and main season for sport filtering
        format_tier = await db.format_tiers.find_one({"id": skill_tier["format_tier_id"]})
        if not format_tier:
            continue
        
        main_season = await db.main_seasons.find_one({"id": format_tier["main_season_id"]})
        if not main_season:
            continue
        
        # Filter by sport type if specified
        if sport_type and main_season["sport_type"] != sport_type.value:
            continue
        
        standing_info = {
            "standing": StandingSnapshot(**parse_from_mongo(standing)),
            "skill_tier": SkillTier(**parse_from_mongo(skill_tier)),
            "sport_type": main_season["sport_type"]
        }
        result.append(standing_info)
    
    return result

# Skill Tier Players Route
@api_router.get("/skill-tiers/{skill_tier_id}/players")
async def get_skill_tier_players(skill_tier_id: str):
    # Get player seats
    seats = await db.player_seats.find({"skill_tier_id": skill_tier_id}).to_list(100)
    
    # Get user details for each seat
    players = []
    for seat in seats:
        user = await db.users.find_one({"id": seat["user_id"]})
        if user:
            player_info = {
                "seat_id": seat["id"],
                "user_id": seat["user_id"],
                "name": user["name"],
                "email": user["email"],
                "rating_level": user["rating_level"],
                "status": seat["status"],
                "joined_at": seat["joined_at"]
            }
            players.append(player_info)
    
    return players

# Rest of the endpoints remain the same but with enhanced notifications...
# (Availability, Match Generation, Score Submission, Standings routes continue as before)

# Availability Routes (Updated for skill tiers)
@api_router.post("/availability")
async def set_availability(availability_data: AvailabilityCreate, user_id: str):
    # Check if availability already exists for this user/skill_tier/week
    existing = await db.availability.find_one({
        "skill_tier_id": availability_data.skill_tier_id,
        "user_id": user_id,
        "week_number": availability_data.week_number
    })
    
    availability_dict = availability_data.dict()
    availability_dict["user_id"] = user_id
    
    if existing:
        # Update existing
        availability_dict["updated_at"] = datetime.now(timezone.utc)
        availability_mongo = prepare_for_mongo(availability_dict)
        await db.availability.update_one(
            {"id": existing["id"]}, 
            {"$set": availability_mongo}
        )
        return {"message": "Availability updated successfully"}
    else:
        # Create new
        availability_obj = Availability(**availability_dict)
        availability_mongo = prepare_for_mongo(availability_obj.dict())
        await db.availability.insert_one(availability_mongo)
        return {"message": "Availability set successfully"}

@api_router.get("/skill-tiers/{skill_tier_id}/availability/{week_number}")
async def get_week_availability(skill_tier_id: str, week_number: int):
    availability_records = await db.availability.find({
        "skill_tier_id": skill_tier_id,
        "week_number": week_number
    }).to_list(100)
    
    # Get user details
    result = []
    for record in availability_records:
        user = await db.users.find_one({"id": record["user_id"]})
        if user:
            result.append({
                "user_id": record["user_id"],
                "name": user["name"],
                "status": record["status"],
                "note": record.get("note"),
                "updated_at": record["updated_at"]
            })
    
    return result

# Match Generation (Updated for skill tiers)
@api_router.post("/skill-tiers/{skill_tier_id}/generate-matches/{week_number}")
async def generate_weekly_matches(skill_tier_id: str, week_number: int):
    # Get available players for this week
    available_players = await db.availability.find({
        "skill_tier_id": skill_tier_id,
        "week_number": week_number,
        "status": AvailabilityStatus.YES
    }).to_list(100)
    
    if len(available_players) < 4:
        raise HTTPException(status_code=400, detail="Not enough available players (minimum 4 needed)")
    
    # Simple pairing algorithm - group players into matches of 4
    player_ids = [p["user_id"] for p in available_players]
    random.shuffle(player_ids)  # Simple randomization
    
    matches = []
    for i in range(0, len(player_ids) - 3, 4):
        match_players = player_ids[i:i+4]
        if len(match_players) == 4:
            match_obj = Match(
                skill_tier_id=skill_tier_id,
                week_number=week_number,
                format=LeagueFormat.DOUBLES
            )
            match_mongo = prepare_for_mongo(match_obj.dict())
            await db.matches.insert_one(match_mongo)
            
            # Create sets with simple pairing: [0,1] vs [2,3] and [0,2] vs [1,3]
            set1 = DoublesSet(
                match_id=match_obj.id,
                set_index=0,
                team_a=[match_players[0], match_players[1]],
                team_b=[match_players[2], match_players[3]],
                score_a=0,
                score_b=0
            )
            set2 = DoublesSet(
                match_id=match_obj.id,
                set_index=1,
                team_a=[match_players[0], match_players[2]],
                team_b=[match_players[1], match_players[3]],
                score_a=0,
                score_b=0
            )
            
            await db.doubles_sets.insert_one(prepare_for_mongo(set1.dict()))
            await db.doubles_sets.insert_one(prepare_for_mongo(set2.dict()))
            
            # Create notifications for all players about match scheduling
            for player_id in match_players:
                match_notification = NotificationCreate(
                    user_id=player_id,
                    title="Match Scheduled",
                    message=f"You have been scheduled for a match in week {week_number}",
                    type=NotificationType.MATCH_SCHEDULED,
                    related_entity_id=match_obj.id
                )
                await create_notification(match_notification)
            
            matches.append(match_obj)
    
    return {"message": f"Generated {len(matches)} matches for week {week_number}", "matches": matches}

# Get Matches (Updated for skill tiers)
@api_router.get("/skill-tiers/{skill_tier_id}/matches")
async def get_skill_tier_matches(skill_tier_id: str, week_number: Optional[int] = None):
    query = {"skill_tier_id": skill_tier_id}
    if week_number:
        query["week_number"] = week_number
    
    matches = await db.matches.find(query).to_list(100)
    
    # Get sets for each match
    result = []
    for match in matches:
        # Parse match from mongo to handle ObjectId
        match = parse_from_mongo(match)
        
        sets = await db.doubles_sets.find({"match_id": match["id"]}).to_list(10)
        
        # Get player names for sets
        for set_data in sets:
            # Parse set data from mongo
            set_data = parse_from_mongo(set_data)
            
            team_a_names = []
            team_b_names = []
            
            for user_id in set_data["team_a"]:
                user = await db.users.find_one({"id": user_id})
                team_a_names.append(user["name"] if user else "Unknown")
            
            for user_id in set_data["team_b"]:
                user = await db.users.find_one({"id": user_id})
                team_b_names.append(user["name"] if user else "Unknown")
            
            set_data["team_a_names"] = team_a_names
            set_data["team_b_names"] = team_b_names
        
        match["sets"] = sets
        result.append(match)
    
    return result

# Submit Scores (Updated with notifications)
@api_router.post("/matches/{match_id}/submit-scores")
async def submit_match_scores(match_id: str, scores: List[dict], submitted_by: str):
    # Update sets with scores
    for score_data in scores:
        set_id = score_data["set_id"]
        score_a = score_data["score_a"]
        score_b = score_data["score_b"]
        
        await db.doubles_sets.update_one(
            {"id": set_id},
            {"$set": {"score_a": score_a, "score_b": score_b}}
        )
    
    # Update match status
    await db.matches.update_one(
        {"id": match_id},
        {"$set": {"status": MatchStatus.PLAYED}}
    )
    
    # Get match details for notifications
    match = await db.matches.find_one({"id": match_id})
    if match:
        # Get all players in the match
        sets = await db.doubles_sets.find({"match_id": match_id}).to_list(10)
        all_players = set()
        for set_data in sets:
            all_players.update(set_data["team_a"] + set_data["team_b"])
        
        # Notify all players about score submission
        for player_id in all_players:
            if player_id != submitted_by:  # Don't notify the submitter
                score_notification = NotificationCreate(
                    user_id=player_id,
                    title="Match Scores Submitted",
                    message=f"Scores have been submitted for your week {match['week_number']} match",
                    type=NotificationType.SCORE_SUBMITTED,
                    related_entity_id=match_id
                )
                await create_notification(score_notification)
    
    # Recalculate standings
    await recalculate_skill_tier_standings(match_id)
    
    return {"message": "Scores submitted successfully"}

async def recalculate_skill_tier_standings(match_id: str):
    """Recalculate standings for a skill tier based on submitted scores"""
    # Get match to find skill tier
    match = await db.matches.find_one({"id": match_id})
    if not match:
        return
    
    skill_tier_id = match["skill_tier_id"]
    
    # Get all players in skill tier
    players = await db.player_seats.find({"skill_tier_id": skill_tier_id, "status": PlayerSeatStatus.ACTIVE}).to_list(100)
    
    # Calculate standings for each player
    for player_seat in players:
        user_id = player_seat["user_id"]
        
        # Find all sets this player participated in
        sets_as_team_a = await db.doubles_sets.find({"team_a": {"$in": [user_id]}}).to_list(1000)
        sets_as_team_b = await db.doubles_sets.find({"team_b": {"$in": [user_id]}}).to_list(1000)
        
        total_set_wins = 0
        total_sets_played = 0
        
        # Count wins from team_a sets
        for set_data in sets_as_team_a:
            if set_data["score_a"] > 0 or set_data["score_b"] > 0:  # Only count played sets
                total_sets_played += 1
                if set_data["score_a"] > set_data["score_b"]:
                    total_set_wins += 1
        
        # Count wins from team_b sets
        for set_data in sets_as_team_b:
            if set_data["score_a"] > 0 or set_data["score_b"] > 0:  # Only count played sets
                total_sets_played += 1
                if set_data["score_b"] > set_data["score_a"]:
                    total_set_wins += 1
        
        win_pct = total_set_wins / total_sets_played if total_sets_played > 0 else 0.0
        
        # Update or create standing
        standing_data = {
            "skill_tier_id": skill_tier_id,
            "player_id": user_id,
            "total_set_wins": total_set_wins,
            "total_sets_played": total_sets_played,
            "win_pct": win_pct,
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.standings.update_one(
            {"skill_tier_id": skill_tier_id, "player_id": user_id},
            {"$set": prepare_for_mongo(standing_data)},
            upsert=True
        )

# Standings (Updated for skill tiers)
@api_router.get("/skill-tiers/{skill_tier_id}/standings")
async def get_skill_tier_standings(skill_tier_id: str):
    standings = await db.standings.find({"skill_tier_id": skill_tier_id}).sort("total_set_wins", -1).to_list(100)
    
    # Add player names
    result = []
    rank = 1
    for standing in standings:
        user = await db.users.find_one({"id": standing["player_id"]})
        if user:
            standing_info = {
                "rank": rank,
                "player_name": user["name"],
                "rating_level": user["rating_level"],
                "total_set_wins": standing["total_set_wins"],
                "total_sets_played": standing["total_sets_played"],
                "win_pct": round(standing["win_pct"], 3)
            }
            result.append(standing_info)
            rank += 1
    
    return result

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()