from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal, Dict, Any
import uuid
from datetime import datetime, timezone, date
from enum import Enum
import random
import string
import base64
import math

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="LeagueAce API", description="Tennis & Pickleball League Management API - Tennis. Organized.")
api_router = APIRouter(prefix="/api")

# Enhanced Enums
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

class CompetitionSystem(str, Enum):
    TEAM_LEAGUE = "Team League Format"
    KNOCKOUT = "Knockout System"

class NotificationType(str, Enum):
    LEAGUE_INVITE = "League Invite"
    MATCH_SCHEDULED = "Match Scheduled"
    SCORE_SUBMITTED = "Score Submitted"
    SEASON_CREATED = "Season Created"
    TIER_ADDED = "Tier Added"
    CHAT_MESSAGE = "Chat Message"
    GROUP_CREATED = "Group Created"

class AuthProvider(str, Enum):
    EMAIL = "Email"
    GOOGLE = "Google"
    APPLE = "Apple"

class ChatThreadType(str, Enum):
    LEAGUE = "league"
    GROUP = "group"
    MATCH = "match"
    DM = "dm"
    ANNOUNCEMENTS = "announcements"

class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"
    ACTION = "action"

# Utility functions
def generate_join_code():
    """Generate a unique 6-character join code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def generate_group_name(index: int, custom_names: List[str] = None) -> str:
    """Generate group names like Group A, B, C or use custom names"""
    if custom_names and index < len(custom_names):
        return custom_names[index]
    return f"Group {chr(65 + index)}"  # A, B, C, etc.

def generate_round_robin_doubles_schedule(players: List[str], total_weeks: int = 12) -> Dict[str, Any]:
    """
    Generate a round robin doubles schedule where every player plays with every other player exactly once as partners,
    and against every possible combination of opponents.
    """
    if len(players) < 4:
        raise ValueError("Need at least 4 players for doubles")
    
    if len(players) % 2 != 0:
        raise ValueError("Need even number of players for doubles")
    
    n = len(players)
    schedule = []
    partner_combinations = []
    all_partnerships = []
    
    # Generate all possible partnerships
    for i in range(n):
        for j in range(i + 1, n):
            all_partnerships.append((players[i], players[j]))
    
    # Generate matches ensuring each player partners with everyone exactly once
    week = 1
    used_partnerships = set()
    
    while len(used_partnerships) < len(all_partnerships) and week <= total_weeks:
        week_matches = []
        week_partnerships = set()
        
        # Try to create matches for this week
        available_players = set(players)
        
        while len(available_players) >= 4:
            # Find the best partnership that hasn't been used
            best_partnership = None
            for partnership in all_partnerships:
                if (partnership not in used_partnerships and 
                    partnership[0] in available_players and 
                    partnership[1] in available_players and
                    partnership not in week_partnerships):
                    best_partnership = partnership
                    break
            
            if not best_partnership:
                # If no unused partnership available, use any available
                for partnership in all_partnerships:
                    if (partnership[0] in available_players and 
                        partnership[1] in available_players and
                        partnership not in week_partnerships):
                        best_partnership = partnership
                        break
            
            if not best_partnership:
                break
                
            # Remove these players from available pool
            team_a = list(best_partnership)
            available_players.remove(team_a[0])
            available_players.remove(team_a[1])
            
            # Find opponents
            if len(available_players) >= 2:
                team_b = list(available_players)[:2]
                available_players.remove(team_b[0])
                available_players.remove(team_b[1])
                
                match = {
                    "week": week,
                    "team_a": team_a,
                    "team_b": team_b,
                    "partnership_a": best_partnership,
                    "partnership_b": tuple(team_b)
                }
                
                week_matches.append(match)
                week_partnerships.add(best_partnership)
                week_partnerships.add(tuple(team_b))
                
                if best_partnership not in used_partnerships:
                    used_partnerships.add(best_partnership)
                if tuple(team_b) not in used_partnerships:
                    used_partnerships.add(tuple(team_b))
        
        if week_matches:
            schedule.extend(week_matches)
        
        week += 1
    
    return {
        "total_weeks": week - 1,
        "total_matches": len(schedule),
        "schedule": schedule,
        "partnerships_coverage": len(used_partnerships),
        "total_possible_partnerships": len(all_partnerships)
    }

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
    profile_picture: Optional[str] = None
    role: UserRole = UserRole.PLAYER
    sports_preferences: List[SportType] = Field(default_factory=list)
    auth_provider: AuthProvider = AuthProvider.EMAIL
    google_id: Optional[str] = None
    apple_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfileCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = Field(ge=3.0, le=5.5)
    photo_url: Optional[str] = None
    role: UserRole = UserRole.PLAYER
    auth_provider: AuthProvider = AuthProvider.EMAIL
    google_id: Optional[str] = None
    apple_id: Optional[str] = None

class SportPreferenceUpdate(BaseModel):
    sports_preferences: List[SportType]

class ProfilePictureUpdate(BaseModel):
    profile_picture: str

class SocialLoginRequest(BaseModel):
    provider: AuthProvider
    token: str
    email: EmailStr
    name: str
    provider_id: str

# Enhanced League Structure Models (4-Tier System)
class League(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Tier 1: League Name
    sport_type: SportType
    description: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueCreate(BaseModel):
    name: str
    sport_type: SportType
    description: Optional[str] = None

class Season(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    name: str
    start_date: date
    end_date: date
    status: SeasonStatus = SeasonStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SeasonCreate(BaseModel):
    league_id: str
    name: str
    start_date: date
    end_date: date

class FormatTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    season_id: str
    name: str  # Tier 2: Singles, Doubles, Round Robin
    format_type: LeagueFormat
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FormatTierCreate(BaseModel):
    season_id: str
    name: str
    format_type: LeagueFormat
    description: Optional[str] = None

class RatingTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    format_tier_id: str
    name: str  # Tier 3: 4.0, 4.5, 5.0
    min_rating: float
    max_rating: float
    max_players: int = 36
    competition_system: CompetitionSystem = CompetitionSystem.TEAM_LEAGUE
    playoff_spots: Optional[int] = 8  # Top players for playoffs
    join_code: str = Field(default_factory=generate_join_code)
    region: str = "General"
    surface: str = "Hard Court"
    rules_md: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RatingTierCreate(BaseModel):
    format_tier_id: str
    name: str
    min_rating: float
    max_rating: float
    max_players: int = 36
    competition_system: CompetitionSystem = CompetitionSystem.TEAM_LEAGUE
    playoff_spots: Optional[int] = 8
    region: str = "General"
    surface: str = "Hard Court"
    rules_md: Optional[str] = None

class PlayerGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    name: str  # Tier 4: Group A, Group B, Group C
    group_size: int = 12
    custom_name: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlayerGroupCreate(BaseModel):
    group_size: int = 12
    custom_names: Optional[List[str]] = None

class PlayerSeat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    player_group_id: Optional[str] = None
    user_id: str
    status: PlayerSeatStatus = PlayerSeatStatus.ACTIVE
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class JoinByCodeRequest(BaseModel):
    join_code: str

# Enhanced Match Models
class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    player_group_id: Optional[str] = None
    week_number: int
    format: LeagueFormat
    participants: List[str]  # List of user IDs
    scheduled_at: Optional[datetime] = None
    venue_id: Optional[str] = None
    status: MatchStatus = MatchStatus.PENDING
    result_confirmed_by: List[str] = Field(default_factory=list)
    chat_thread_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SetResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    set_number: int
    player1_score: int = Field(ge=0)
    player2_score: int = Field(ge=0)
    # For doubles
    team_a_score: int = Field(ge=0)
    team_b_score: int = Field(ge=0)
    team_a_players: Optional[List[str]] = None
    team_b_players: Optional[List[str]] = None

class MatchResult(BaseModel):
    match_id: str
    sets: List[SetResult]
    winner_ids: List[str]
    submitted_by: str

class RoundRobinSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_group_id: str
    total_weeks: int
    matches_per_week: int
    partner_rotation: List[Dict[str, Any]]  # Stores partner combinations for each week
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MatchGenerationRequest(BaseModel):
    player_group_id: str
    week_number: int
    matches_per_week: Optional[int] = 4

# Chat System Models
class ChatThread(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ChatThreadType
    name: str
    scope: Dict[str, str]  # leagueId, seasonId, groupId, matchId, etc.
    created_by: str
    member_count: int = 0
    pinned_message_ids: List[str] = Field(default_factory=list)
    last_message_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatThreadCreate(BaseModel):
    type: ChatThreadType
    name: str
    scope: Dict[str, str]
    member_ids: List[str]

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str
    sender_id: str
    sender_name: str
    text: str
    type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    reactions: Dict[str, bool] = Field(default_factory=dict)
    action_payload: Optional[Dict] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ChatMessageCreate(BaseModel):
    thread_id: str
    text: str
    type: MessageType = MessageType.TEXT
    reply_to_message_id: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    action_payload: Optional[Dict] = None

class ChatThreadMember(BaseModel):
    thread_id: str
    user_id: str
    role: str = "member"  # "admin" | "member"
    muted: bool = False
    last_read_at: Optional[datetime] = None
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Other existing models...
class Availability(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    user_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AvailabilityCreate(BaseModel):
    rating_tier_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None

class StandingSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    player_group_id: Optional[str] = None
    player_id: str
    total_set_wins: int = 0
    total_sets_played: int = 0
    win_pct: float = 0.0
    rank: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: NotificationType
    sport_type: Optional[SportType] = None
    related_entity_id: Optional[str] = None
    read: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    type: NotificationType
    sport_type: Optional[SportType] = None
    related_entity_id: Optional[str] = None

# Notification Helper Function
async def create_notification(notification_data: NotificationCreate):
    """Helper function to create notifications"""
    notification_obj = Notification(**notification_data.dict())
    notification_mongo = prepare_for_mongo(notification_obj.dict())
    await db.notifications.insert_one(notification_mongo)
    return notification_obj

# Chat Helper Functions
async def create_chat_thread(thread_data: ChatThreadCreate, created_by: str):
    """Create a chat thread and add initial members"""
    thread_dict = thread_data.dict()
    thread_dict["created_by"] = created_by
    thread_dict["member_count"] = len(thread_data.member_ids)
    
    thread_obj = ChatThread(**thread_dict)
    thread_mongo = prepare_for_mongo(thread_obj.dict())
    await db.chat_threads.insert_one(thread_mongo)
    
    # Add members
    for member_id in thread_data.member_ids:
        member_obj = ChatThreadMember(
            thread_id=thread_obj.id,
            user_id=member_id,
            role="admin" if member_id == created_by else "member"
        )
        member_mongo = prepare_for_mongo(member_obj.dict())
        await db.chat_thread_members.insert_one(member_mongo)
    
    return thread_obj

async def create_system_message(thread_id: str, message: str, action_payload: Optional[Dict] = None):
    """Create a system message in a chat thread"""
    message_obj = ChatMessage(
        thread_id=thread_id,
        sender_id="system",
        sender_name="System",
        text=message,
        type=MessageType.SYSTEM,
        action_payload=action_payload
    )
    message_mongo = prepare_for_mongo(message_obj.dict())
    await db.chat_messages.insert_one(message_mongo)
    
    # Update thread last message time
    await db.chat_threads.update_one(
        {"id": thread_id},
        {"$set": {"last_message_at": datetime.now(timezone.utc)}}
    )
    
    return message_obj

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to LeagueAce - Tennis & Pickleball League Management API", "tagline": "Tennis. Organized."}

# Authentication Routes
@api_router.post("/auth/social-login", response_model=UserProfile)
async def social_login(login_data: SocialLoginRequest):
    """Handle Google/Apple social login"""
    existing_user = None
    if login_data.provider == AuthProvider.GOOGLE:
        existing_user = await db.users.find_one({"google_id": login_data.provider_id})
    elif login_data.provider == AuthProvider.APPLE:
        existing_user = await db.users.find_one({"apple_id": login_data.provider_id})
    
    if existing_user:
        return UserProfile(**parse_from_mongo(existing_user))
    
    email_user = await db.users.find_one({"email": login_data.email})
    if email_user:
        update_data = {}
        if login_data.provider == AuthProvider.GOOGLE:
            update_data["google_id"] = login_data.provider_id
        elif login_data.provider == AuthProvider.APPLE:
            update_data["apple_id"] = login_data.provider_id
        
        await db.users.update_one({"id": email_user["id"]}, {"$set": update_data})
        updated_user = await db.users.find_one({"id": email_user["id"]})
        return UserProfile(**parse_from_mongo(updated_user))
    
    user_data = UserProfileCreate(
        email=login_data.email,
        name=login_data.name,
        rating_level=4.0,
        auth_provider=login_data.provider,
        google_id=login_data.provider_id if login_data.provider == AuthProvider.GOOGLE else None,
        apple_id=login_data.provider_id if login_data.provider == AuthProvider.APPLE else None
    )
    
    user_dict = user_data.dict()
    user_obj = UserProfile(**user_dict)
    user_mongo = prepare_for_mongo(user_obj.dict())
    await db.users.insert_one(user_mongo)
    
    welcome_notification = NotificationCreate(
        user_id=user_obj.id,
        title="Welcome to LeagueAce!",
        message=f"Welcome {user_obj.name}! Tennis. Organized. Ready to join leagues?",
        type=NotificationType.LEAGUE_INVITE
    )
    await create_notification(welcome_notification)
    
    return user_obj

# User Profile Routes
@api_router.post("/users", response_model=UserProfile)
async def create_user(user_data: UserProfileCreate):
    user_dict = user_data.dict()
    user_obj = UserProfile(**user_dict)
    user_mongo = prepare_for_mongo(user_obj.dict())
    await db.users.insert_one(user_mongo)
    
    welcome_notification = NotificationCreate(
        user_id=user_obj.id,
        title="Welcome to LeagueAce!",
        message=f"Welcome {user_obj.name}! Tennis. Organized. Ready to join leagues?",
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
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"sports_preferences": [sport.value for sport in preferences.sports_preferences]}}
    )
    
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**parse_from_mongo(updated_user))

@api_router.patch("/users/{user_id}/profile-picture", response_model=UserProfile)
async def update_profile_picture(user_id: str, picture_data: ProfilePictureUpdate):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"profile_picture": picture_data.profile_picture}}
    )
    
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**parse_from_mongo(updated_user))

@api_router.post("/users/{user_id}/upload-picture")
async def upload_profile_picture(user_id: str, file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_content = await file.read()
    base64_image = base64.b64encode(file_content).decode('utf-8')
    data_url = f"data:{file.content_type};base64,{base64_image}"
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"profile_picture": data_url}}
    )
    
    return {"message": "Profile picture uploaded successfully"}

# Enhanced League Creation Routes (4-Tier System)
@api_router.post("/leagues", response_model=League)
async def create_league(league_data: LeagueCreate, created_by: str):
    user = await db.users.find_one({"id": created_by})
    if not user or user["role"] != UserRole.LEAGUE_MANAGER:
        raise HTTPException(status_code=403, detail="Only League Managers can create leagues")
    
    league_dict = league_data.dict()
    league_dict["created_by"] = created_by
    league_obj = League(**league_dict)
    league_mongo = prepare_for_mongo(league_obj.dict())
    await db.leagues.insert_one(league_mongo)
    
    # Create league chat thread
    thread_data = ChatThreadCreate(
        type=ChatThreadType.LEAGUE,
        name=f"{league_obj.name} League Chat",
        scope={"league_id": league_obj.id},
        member_ids=[created_by]
    )
    await create_chat_thread(thread_data, created_by)
    
    league_notification = NotificationCreate(
        user_id=created_by,
        title=f"New {league_obj.sport_type} League Created",
        message=f"Successfully created {league_obj.name} league",
        type=NotificationType.SEASON_CREATED,
        sport_type=league_obj.sport_type,
        related_entity_id=league_obj.id
    )
    await create_notification(league_notification)
    
    return league_obj

@api_router.get("/leagues", response_model=List[League])
async def get_leagues(sport_type: Optional[SportType] = None):
    query = {}
    if sport_type:
        query["sport_type"] = sport_type.value
    
    leagues = await db.leagues.find(query).to_list(100)
    valid_leagues = []
    for league in leagues:
        try:
            # Only include leagues that match the current schema
            if 'sport_type' in league:
                valid_leagues.append(League(**parse_from_mongo(league)))
        except Exception as e:
            # Skip invalid league records
            continue
    return valid_leagues

@api_router.get("/users/{user_id}/leagues", response_model=List[League])
async def get_user_leagues(user_id: str, sport_type: Optional[SportType] = None):
    query = {"created_by": user_id}
    if sport_type:
        query["sport_type"] = sport_type.value
    
    leagues = await db.leagues.find(query).to_list(100)
    return [League(**parse_from_mongo(league)) for league in leagues]

# Season Routes (Tier 1)
@api_router.post("/seasons", response_model=Season)
async def create_season(season_data: SeasonCreate):
    league = await db.leagues.find_one({"id": season_data.league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    season_dict = season_data.dict()
    season_obj = Season(**season_dict)
    season_mongo = prepare_for_mongo(season_obj.dict())
    await db.seasons.insert_one(season_mongo)
    
    return season_obj

@api_router.get("/leagues/{league_id}/seasons", response_model=List[Season])
async def get_league_seasons(league_id: str):
    seasons = await db.seasons.find({"league_id": league_id}).to_list(100)
    return [Season(**parse_from_mongo(season)) for season in seasons]

# Format Tier Routes (Tier 2: Singles, Doubles, Round Robin)
@api_router.post("/format-tiers", response_model=FormatTier)
async def create_format_tier(tier_data: FormatTierCreate):
    season = await db.seasons.find_one({"id": tier_data.season_id})
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    tier_dict = tier_data.dict()
    tier_obj = FormatTier(**tier_dict)
    tier_mongo = prepare_for_mongo(tier_obj.dict())
    await db.format_tiers.insert_one(tier_mongo)
    
    return tier_obj

@api_router.get("/seasons/{season_id}/format-tiers", response_model=List[FormatTier])
async def get_season_format_tiers(season_id: str):
    tiers = await db.format_tiers.find({"season_id": season_id}).to_list(100)
    return [FormatTier(**parse_from_mongo(tier)) for tier in tiers]

# Rating Tier Routes (Tier 3: 4.0, 4.5, 5.0)
@api_router.post("/rating-tiers", response_model=RatingTier)
async def create_rating_tier(tier_data: RatingTierCreate):
    format_tier = await db.format_tiers.find_one({"id": tier_data.format_tier_id})
    if not format_tier:
        raise HTTPException(status_code=404, detail="Format tier not found")
    
    tier_dict = tier_data.dict()
    tier_obj = RatingTier(**tier_dict)
    tier_mongo = prepare_for_mongo(tier_obj.dict())
    await db.rating_tiers.insert_one(tier_mongo)
    
    return tier_obj

@api_router.get("/format-tiers/{format_tier_id}/rating-tiers", response_model=List[RatingTier])
async def get_format_rating_tiers(format_tier_id: str):
    tiers = await db.rating_tiers.find({"format_tier_id": format_tier_id}).to_list(100)
    return [RatingTier(**parse_from_mongo(tier)) for tier in tiers]

@api_router.get("/rating-tiers/{rating_tier_id}", response_model=RatingTier)
async def get_rating_tier(rating_tier_id: str):
    tier = await db.rating_tiers.find_one({"id": rating_tier_id})
    if not tier:
        raise HTTPException(status_code=404, detail="Rating tier not found")
    return RatingTier(**parse_from_mongo(tier))

# Player Group Routes (Tier 4: Groups A, B, C)
@api_router.post("/rating-tiers/{rating_tier_id}/create-groups")
async def create_player_groups(rating_tier_id: str, group_data: PlayerGroupCreate):
    rating_tier = await db.rating_tiers.find_one({"id": rating_tier_id})
    if not rating_tier:
        raise HTTPException(status_code=404, detail="Rating tier not found")
    
    # Get all players in this tier
    players = await db.player_seats.find({
        "rating_tier_id": rating_tier_id,
        "status": PlayerSeatStatus.ACTIVE
    }).to_list(1000)
    
    total_players = len(players)
    group_size = group_data.group_size
    num_groups = math.ceil(total_players / group_size)
    
    created_groups = []
    
    # Create groups
    for i in range(num_groups):
        group_name = generate_group_name(i, group_data.custom_names)
        group_obj = PlayerGroup(
            rating_tier_id=rating_tier_id,
            name=group_name,
            group_size=group_size,
            custom_name=group_data.custom_names[i] if group_data.custom_names and i < len(group_data.custom_names) else None
        )
        group_mongo = prepare_for_mongo(group_obj.dict())
        await db.player_groups.insert_one(group_mongo)
        created_groups.append(group_obj)
    
    # Randomly assign players to groups
    random.shuffle(players)
    for i, player in enumerate(players):
        group_index = i % num_groups
        group_id = created_groups[group_index].id
        
        await db.player_seats.update_one(
            {"id": player["id"]},
            {"$set": {"player_group_id": group_id}}
        )
        
        # Create group chat thread for first player in each group
        if i < num_groups:
            thread_data = ChatThreadCreate(
                type=ChatThreadType.GROUP,
                name=f"{created_groups[group_index].name} Chat",
                scope={
                    "rating_tier_id": rating_tier_id,
                    "group_id": group_id
                },
                member_ids=[player["user_id"]]
            )
            chat_thread = await create_chat_thread(thread_data, player["user_id"])
            
            # Add system message
            await create_system_message(
                chat_thread.id,
                f"Welcome to {created_groups[group_index].name}! Players will be added as they join."
            )
    
    return {
        "message": f"Created {num_groups} groups with {total_players} players",
        "groups": created_groups
    }

@api_router.get("/rating-tiers/{rating_tier_id}/groups", response_model=List[PlayerGroup])
async def get_rating_tier_groups(rating_tier_id: str):
    groups = await db.player_groups.find({"rating_tier_id": rating_tier_id}).to_list(100)
    return [PlayerGroup(**parse_from_mongo(group)) for group in groups]

# Enhanced Join by Code Route
@api_router.post("/join-by-code/{user_id}")
async def join_by_code(user_id: str, request: JoinByCodeRequest):
    rating_tier = await db.rating_tiers.find_one({"join_code": request.join_code})
    if not rating_tier:
        raise HTTPException(status_code=404, detail="Invalid join code")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_seat = await db.player_seats.find_one({"rating_tier_id": rating_tier["id"], "user_id": user_id})
    if existing_seat:
        raise HTTPException(status_code=400, detail="User already joined this tier")
    
    if not (rating_tier["min_rating"] <= user["rating_level"] <= rating_tier["max_rating"]):
        raise HTTPException(
            status_code=400, 
            detail=f"Rating {user['rating_level']} not suitable for tier {rating_tier['name']} ({rating_tier['min_rating']}-{rating_tier['max_rating']})"
        )
    
    player_count = await db.player_seats.count_documents({
        "rating_tier_id": rating_tier["id"], 
        "status": PlayerSeatStatus.ACTIVE
    })
    
    status = PlayerSeatStatus.ACTIVE if player_count < rating_tier["max_players"] else PlayerSeatStatus.RESERVE
    
    seat_obj = PlayerSeat(rating_tier_id=rating_tier["id"], user_id=user_id, status=status)
    seat_mongo = prepare_for_mongo(seat_obj.dict())
    await db.player_seats.insert_one(seat_mongo)
    
    # If groups exist, assign to a group
    groups = await db.player_groups.find({"rating_tier_id": rating_tier["id"]}).to_list(100)
    if groups:
        # Find group with least players
        group_player_counts = []
        for group in groups:
            count = await db.player_seats.count_documents({
                "player_group_id": group["id"],
                "status": PlayerSeatStatus.ACTIVE
            })
            group_player_counts.append((group["id"], count))
        
        # Assign to group with least players
        best_group_id = min(group_player_counts, key=lambda x: x[1])[0]
        await db.player_seats.update_one(
            {"id": seat_obj.id},
            {"$set": {"player_group_id": best_group_id}}
        )
        
        # Add to group chat
        group_chat = await db.chat_threads.find_one({
            "type": ChatThreadType.GROUP,
            "scope.group_id": best_group_id
        })
        if group_chat:
            member_obj = ChatThreadMember(
                thread_id=group_chat["id"],
                user_id=user_id
            )
            member_mongo = prepare_for_mongo(member_obj.dict())
            await db.chat_thread_members.insert_one(member_mongo)
            
            # Update member count
            await db.chat_threads.update_one(
                {"id": group_chat["id"]},
                {"$inc": {"member_count": 1}}
            )
            
            # System message
            await create_system_message(
                group_chat["id"],
                f"{user['name']} joined the group!"
            )
    
    join_notification = NotificationCreate(
        user_id=user_id,
        title=f"Joined {rating_tier['name']} Tier",
        message=f"Successfully joined {rating_tier['name']} with {status} status",
        type=NotificationType.LEAGUE_INVITE,
        related_entity_id=rating_tier["id"]
    )
    await create_notification(join_notification)
    
    return {
        "message": f"Successfully joined {rating_tier['name']} with status: {status}",
        "status": status,
        "rating_tier": RatingTier(**parse_from_mongo(rating_tier))
    }

# Continue with existing routes but updated for new structure...
# (Chat routes, match routes, etc. would continue here)

# Round Robin Doubles Match Generation Routes
@api_router.post("/player-groups/{group_id}/generate-schedule")
async def generate_group_schedule(group_id: str):
    """Generate a complete round robin doubles schedule for a player group"""
    group = await db.player_groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Player group not found")
    
    # Get all active players in the group
    players = await db.player_seats.find({
        "player_group_id": group_id,
        "status": PlayerSeatStatus.ACTIVE
    }).to_list(100)
    
    if len(players) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 players to generate doubles schedule")
    
    if len(players) % 2 != 0:
        raise HTTPException(status_code=400, detail="Need even number of players for doubles")
    
    player_ids = [player["user_id"] for player in players]
    
    # Generate the schedule
    try:
        schedule_data = generate_round_robin_doubles_schedule(player_ids)
        
        # Store the schedule
        schedule_obj = RoundRobinSchedule(
            player_group_id=group_id,
            total_weeks=schedule_data["total_weeks"],
            matches_per_week=len([m for m in schedule_data["schedule"] if m["week"] == 1]),
            partner_rotation=schedule_data["schedule"]
        )
        schedule_mongo = prepare_for_mongo(schedule_obj.dict())
        await db.round_robin_schedules.insert_one(schedule_mongo)
        
        return {
            "message": f"Generated {schedule_data['total_matches']} matches over {schedule_data['total_weeks']} weeks",
            "schedule": schedule_data,
            "schedule_id": schedule_obj.id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/player-groups/{group_id}/schedule")
async def get_group_schedule(group_id: str):
    """Get the round robin schedule for a player group"""
    schedule = await db.round_robin_schedules.find_one({"player_group_id": group_id})
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found for this group")
    
    return RoundRobinSchedule(**parse_from_mongo(schedule))

@api_router.post("/player-groups/{group_id}/create-matches")
async def create_week_matches(group_id: str, request: MatchGenerationRequest):
    """Create actual match records for a specific week based on the round robin schedule"""
    schedule = await db.round_robin_schedules.find_one({"player_group_id": group_id})
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found. Generate schedule first.")
    
    # Get player group info
    group = await db.player_groups.find_one({"id": group_id})
    rating_tier_id = group["rating_tier_id"]
    
    # Filter matches for the requested week
    week_matches = [m for m in schedule["partner_rotation"] if m["week"] == request.week_number]
    
    if not week_matches:
        raise HTTPException(status_code=404, detail=f"No matches scheduled for week {request.week_number}")
    
    created_matches = []
    
    for match_data in week_matches:
        # Create match record
        participants = match_data["team_a"] + match_data["team_b"]
        
        match_obj = Match(
            rating_tier_id=rating_tier_id,
            player_group_id=group_id,
            week_number=request.week_number,
            format=LeagueFormat.DOUBLES,
            participants=participants,
            status=MatchStatus.PENDING
        )
        match_mongo = prepare_for_mongo(match_obj.dict())
        await db.matches.insert_one(match_mongo)
        
        # Create match chat thread
        thread_data = ChatThreadCreate(
            type=ChatThreadType.MATCH,
            name=f"Week {request.week_number} Match Chat",
            scope={
                "match_id": match_obj.id,
                "group_id": group_id
            },
            member_ids=participants
        )
        chat_thread = await create_chat_thread(thread_data, participants[0])
        
        # Update match with chat thread ID
        await db.matches.update_one(
            {"id": match_obj.id},
            {"$set": {"chat_thread_id": chat_thread.id}}
        )
        
        # Add system message with match details
        team_a_names = []
        team_b_names = []
        
        for user_id in match_data["team_a"]:
            user = await db.users.find_one({"id": user_id})
            if user:
                team_a_names.append(user["name"])
                
        for user_id in match_data["team_b"]:
            user = await db.users.find_one({"id": user_id})
            if user:
                team_b_names.append(user["name"])
        
        await create_system_message(
            chat_thread.id,
            f"🎾 Week {request.week_number} Doubles Match\n" +
            f"Team A: {' & '.join(team_a_names)}\n" +
            f"Team B: {' & '.join(team_b_names)}\n\n" +
            f"Use /when to propose match times, /where for location, /lineup for confirmations!"
        )
        
        created_matches.append(match_obj)
        
        # Notify players
        for player_id in participants:
            notification = NotificationCreate(
                user_id=player_id,
                title=f"Week {request.week_number} Match Scheduled",
                message=f"Your doubles match has been created. Check the match chat for details!",
                type=NotificationType.MATCH_SCHEDULED,
                related_entity_id=match_obj.id
            )
            await create_notification(notification)
    
    return {
        "message": f"Created {len(created_matches)} matches for week {request.week_number}",
        "matches": created_matches
    }

@api_router.get("/player-groups/{group_id}/matches")
async def get_group_matches(group_id: str, week_number: Optional[int] = None):
    """Get all matches for a player group, optionally filtered by week"""
    query = {"player_group_id": group_id}
    if week_number:
        query["week_number"] = week_number
    
    matches = await db.matches.find(query).to_list(100)
    return [Match(**parse_from_mongo(match)) for match in matches]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()