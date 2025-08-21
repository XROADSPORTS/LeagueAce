from fastapi import FastAPI, APIRouter, HTTPException, Depends, File, UploadFile
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import time
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal, Dict, Any
import uuid
from datetime import datetime, timezone, date, timedelta

def generate_uuid() -> str:
    return str(uuid.uuid4())
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

class PlayerConfirmationStatus(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    DECLINED = "Declined"
    SUBSTITUTE_REQUESTED = "Substitute Requested"

class SubstituteRequestStatus(str, Enum):
    OPEN = "Open"
    FILLED = "Filled"
    CANCELLED = "Cancelled"

class TossResult(str, Enum):
    SERVE = "Serve"
    RETURN = "Return"
    COURT_SIDE_A = "Court Side A"
    COURT_SIDE_B = "Court Side B"

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
    EMOJI = "emoji"
    REPLY = "reply"

class ReactionType(str, Enum):
    LIKE = "👍"
    HEART = "❤️"
    LAUGH = "😂"
    SURPRISE = "😮"
    ANGRY = "😠"
    SAD = "😢"
    TENNIS = "🎾"
    FIRE = "🔥"

class SlashCommand(str, Enum):
    WHEN = "/when"
    WHERE = "/where"
    LINEUP = "/lineup"
    SUBS = "/subs"
    SCORE = "/score"
    TOSS = "/toss"

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

def calculate_player_rankings(player_stats: List["PlayerSetStats"]) -> List["PlayerSetStats"]:
    """
    Calculate player rankings based on:
    1. Total sets won (primary)
    2. Set win percentage (tie-breaker 1) 
    3. Head-to-head record (tie-breaker 2)
    4. Matches won (tie-breaker 3)
    """
    # Sort players by ranking criteria
    sorted_players = sorted(player_stats, key=lambda p: (
        -p.total_sets_won,           # More sets won = higher rank
        -p.set_win_percentage,       # Better set win % = higher rank
        -p.matches_won,              # More matches won = higher rank
        -p.tie_breaker_points        # Tie breaker points
    ))
    
    # Assign ranks
    for i, player in enumerate(sorted_players):
        player.rank = i + 1
        player.last_updated = datetime.now(timezone.utc)
    
    return sorted_players

def update_player_stats_from_match(match: Dict, match_result: "MatchResult") -> List["PlayerSetStats"]:
    """Update player statistics based on a completed match"""
    updated_stats = []
    
    for participant_id in match["participants"]:
        # Calculate sets won and played for this participant
        sets_won = 0
        sets_played = len(match_result.sets)
        
        for set_result in match_result.sets:
            if participant_id in set_result.set_winner_ids:
                sets_won += 1
        
        # Check if player won the match
        match_won = 1 if participant_id in match_result.winner_ids else 0
        
        # Create or update player stats
        stats = PlayerSetStats(
            player_id=participant_id,
            rating_tier_id=match["rating_tier_id"],
            player_group_id=match.get("player_group_id"),
            total_sets_won=sets_won,
            total_sets_played=sets_played,
            matches_played=1,
            matches_won=match_won,
            set_win_percentage=sets_won / sets_played if sets_played > 0 else 0.0,
            win_percentage=match_won
        )
        
        updated_stats.append(stats)
    
    return updated_stats

def determine_playoff_qualifiers(player_stats: List["PlayerSetStats"], playoff_spots: int = 8) -> List[str]:
    """Determine which players qualify for playoffs (default top 8)"""
    ranked_players = calculate_player_rankings(player_stats)
    qualifiers = [player.player_id for player in ranked_players[:playoff_spots]]
    return qualifiers

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

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None

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
    league_id: str  # Changed from season_id to league_id 
    name: str  # Tier 2: Singles, Doubles, Round Robin
    format_type: LeagueFormat
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FormatTierCreate(BaseModel):
    league_id: str  # Changed from season_id to league_id
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
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    status: MatchStatus = MatchStatus.PENDING
    result_confirmed_by: List[str] = Field(default_factory=list)
    chat_thread_id: Optional[str] = None
    confirmation_deadline: Optional[datetime] = None
    toss_completed: bool = False
    toss_winner_id: Optional[str] = None
    toss_choice: Optional[TossResult] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlayerConfirmation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    player_id: str
    status: PlayerConfirmationStatus = PlayerConfirmationStatus.PENDING
    response_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MatchTimeProposal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    proposed_by: str
    proposed_datetime: datetime
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    notes: Optional[str] = None
    votes: List[str] = Field(default_factory=list)  # Player IDs who voted for this time
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SubstituteRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    original_player_id: str
    requested_by: str
    reason: str
    status: SubstituteRequestStatus = SubstituteRequestStatus.OPEN
    substitute_player_id: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PreMatchToss(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    initiated_by: str
    winner_id: str
    choice: TossResult
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SetResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    set_number: int
    # For singles
    player1_score: int = Field(ge=0, le=7)  # Tennis scores typically max at 7
    player2_score: int = Field(ge=0, le=7)
    player1_id: Optional[str] = None
    player2_id: Optional[str] = None
    # For doubles  
    team_a_score: int = Field(ge=0, le=7)
    team_b_score: int = Field(ge=0, le=7)
    team_a_players: Optional[List[str]] = None
    team_b_players: Optional[List[str]] = None
    # Set winner tracking
    set_winner_ids: List[str] = Field(default_factory=list)
    is_completed: bool = False
    completed_at: Optional[datetime] = None

class MatchResult(BaseModel):
    match_id: str
    sets: List[SetResult]
    winner_ids: List[str]
    submitted_by: str
    total_sets_played: int
    match_completed: bool = False
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlayerSetStats(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    player_id: str
    rating_tier_id: str
    player_group_id: Optional[str] = None
    total_sets_won: int = 0
    total_sets_played: int = 0
    matches_played: int = 0
    matches_won: int = 0
    win_percentage: float = 0.0
    set_win_percentage: float = 0.0
    rank: int = 0
    tie_breaker_points: int = 0  # For tie-breaking logic
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueStandings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    player_group_id: Optional[str] = None
    season_week: int
    player_stats: List[PlayerSetStats]
    playoff_qualification: List[str] = Field(default_factory=list)  # Top 8 player IDs
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PlayoffBracket(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    bracket_type: Literal["single_elimination", "double_elimination"] = "single_elimination"
    qualified_players: List[str]  # Top 8 players from regular season
    bracket_matches: List[str] = Field(default_factory=list)  # Match IDs in bracket order
    current_round: str = "quarterfinals"  # quarterfinals, semifinals, finals
    champion_id: Optional[str] = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

class TimeProposalRequest(BaseModel):
    match_id: str
    proposed_datetime: datetime
    venue_name: Optional[str] = None
    venue_address: Optional[str] = None
    notes: Optional[str] = None

class PlayerConfirmationRequest(BaseModel):
    match_id: str
    status: PlayerConfirmationStatus
    notes: Optional[str] = None

class SubstituteRequestCreate(BaseModel):
    match_id: str
    original_player_id: str
    reason: str

class SubstituteApproval(BaseModel):
    substitute_request_id: str
    substitute_player_id: str

class TossRequest(BaseModel):
    match_id: str

class SetScoreUpdate(BaseModel):
    match_id: str
    set_number: int
    # For singles
    player1_score: Optional[int] = None
    player2_score: Optional[int] = None
    # For doubles
    team_a_score: Optional[int] = None
    team_b_score: Optional[int] = None
    is_set_complete: bool = False

class MatchScoreSubmission(BaseModel):
    match_id: str
    sets: List[SetScoreUpdate]
    match_winner_ids: List[str]

class StandingsRequest(BaseModel):
    rating_tier_id: str
    player_group_id: Optional[str] = None
    week_number: Optional[int] = None

# Advanced Chat Request Models
class MessageReactionRequest(BaseModel):
    message_id: str
    reaction_type: ReactionType

class EditMessageRequest(BaseModel):
    message_id: str
    new_text: str

class PinMessageRequest(BaseModel):
    message_id: str
    pin: bool = True

class SlashCommandRequest(BaseModel):
    thread_id: str
    command: SlashCommand
    parameters: Optional[Dict[str, str]] = None

class MentionNotification(BaseModel):
    mentioned_user_id: str
    message_id: str
    thread_id: str
    sender_name: str
    message_preview: str

class ThreadModerationRequest(BaseModel):
    thread_id: str
    action: Literal["mute_user", "unmute_user", "kick_user", "archive_thread", "unarchive_thread"]
    target_user_id: Optional[str] = None
    reason: Optional[str] = None

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
    unread_count: int = 0
    is_archived: bool = False
    moderation_settings: Dict[str, Any] = Field(default_factory=dict)
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
    reactions: Dict[str, List[str]] = Field(default_factory=dict)  # reaction_type -> list of user_ids
    mentions: List[str] = Field(default_factory=list)  # user_ids mentioned in message
    is_pinned: bool = False
    is_edited: bool = False
    edited_at: Optional[datetime] = None
    action_payload: Optional[Dict] = None
    slash_command: Optional[SlashCommand] = None
    read_by: List[str] = Field(default_factory=list)  # user_ids who have read this message
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
    role: str = "member"  # "admin" | "moderator" | "member"
    muted: bool = False
    notifications_enabled: bool = True
    last_read_at: Optional[datetime] = None
    last_typing_at: Optional[datetime] = None
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MessageReaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str
    user_id: str
    reaction_type: ReactionType
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TypingIndicator(BaseModel):
    thread_id: str
    user_id: str
    user_name: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

@api_router.patch("/users/{user_id}", response_model=UserProfile)
async def update_user_profile(user_id: str, updates: UserProfileUpdate):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    if data:
        await db.users.update_one({"id": user_id}, {"$set": data})
    updated_user = await db.users.find_one({"id": user_id})
    return UserProfile(**parse_from_mongo(updated_user))

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
    league = await db.leagues.find_one({"id": tier_data.league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    tier_dict = tier_data.dict()
    tier_obj = FormatTier(**tier_dict)
    tier_mongo = prepare_for_mongo(tier_obj.dict())
    await db.format_tiers.insert_one(tier_mongo)
    
    return tier_obj

@api_router.get("/leagues/{league_id}/format-tiers", response_model=List[FormatTier])
async def get_league_format_tiers(league_id: str):
    tiers = await db.format_tiers.find({"league_id": league_id}).to_list(100)
    return [FormatTier(**parse_from_mongo(tier)) for tier in tiers]

# Keep the old season endpoint for backward compatibility
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

# Validate/Resolve Join Code
@api_router.get("/rating-tiers/by-code/{code}")
async def get_rating_tier_by_code(code: str):
    normalized = (code or "").strip().upper()
    rt = await db.rating_tiers.find_one({"join_code": normalized})
    if not rt:
        raise HTTPException(status_code=404, detail="Invalid join code")
    # Fetch related format tier and league for context
    fmt = await db.format_tiers.find_one({"id": rt.get("format_tier_id")}) if rt.get("format_tier_id") else None
    league = await db.leagues.find_one({"id": fmt.get("league_id")}) if fmt and fmt.get("league_id") else None
    summary = {
        "id": rt.get("id"),
        "name": rt.get("name"),
        "join_code": rt.get("join_code"),
        "min_rating": rt.get("min_rating"),
        "max_rating": rt.get("max_rating"),
        "max_players": rt.get("max_players"),
        "competition_system": rt.get("competition_system"),
        "league_id": league.get("id") if league else None,
        "league_name": league.get("name") if league else None,
        "sport_type": league.get("sport_type") if league else None,
    }
    return summary

async def get_rating_tier_groups(rating_tier_id: str):
    groups = await db.player_groups.find({"rating_tier_id": rating_tier_id}).to_list(100)
    return [PlayerGroup(**parse_from_mongo(group)) for group in groups]

# Enhanced Join by Code Route
@api_router.post("/join-by-code/{user_id}")
async def join_by_code(user_id: str, request: JoinByCodeRequest):
    # Normalize incoming code: trim + uppercase for case-insensitive matching
    import re
    raw = (request.join_code or "")
    code = re.sub(r"[^A-Z0-9]", "", raw.strip().upper())
    rating_tier = await db.rating_tiers.find_one({"join_code": code})
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

# Match Scheduling and Confirmation Routes
@api_router.post("/matches/{match_id}/propose-time")
async def propose_match_time(match_id: str, proposal: TimeProposalRequest, proposed_by: str):
    """Propose a time and venue for a match"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if proposed_by not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can propose times")
    
    proposal_obj = MatchTimeProposal(
        match_id=match_id,
        proposed_by=proposed_by,
        proposed_datetime=proposal.proposed_datetime,
        venue_name=proposal.venue_name,
        venue_address=proposal.venue_address,
        notes=proposal.notes
    )
    
    proposal_mongo = prepare_for_mongo(proposal_obj.dict())
    await db.match_time_proposals.insert_one(proposal_mongo)
    
    # Add system message to match chat
    if match["chat_thread_id"]:
        user = await db.users.find_one({"id": proposed_by})
        user_name = user["name"] if user else "Unknown"
        
        venue_text = f" at {proposal.venue_name}" if proposal.venue_name else ""
        notes_text = f"\n📝 Notes: {proposal.notes}" if proposal.notes else ""
        
        await create_system_message(
            match["chat_thread_id"],
            f"⏰ {user_name} proposed match time:\n" +
            f"🗓️ {proposal.proposed_datetime.strftime('%A, %B %d at %I:%M %p')}" +
            venue_text + notes_text +
            "\n\nReact with 👍 to vote for this time!"
        )
    
    # Notify other participants
    for participant_id in match["participants"]:
        if participant_id != proposed_by:
            notification = NotificationCreate(
                user_id=participant_id,
                title="Match Time Proposed",
                message=f"New time proposed for your Week {match['week_number']} match",
                type=NotificationType.MATCH_SCHEDULED,
                related_entity_id=match_id
            )
            await create_notification(notification)
    
    return proposal_obj

@api_router.get("/matches/{match_id}/time-proposals")
async def get_match_time_proposals(match_id: str):
    """Get all time proposals for a match"""
    proposals = await db.match_time_proposals.find({"match_id": match_id}).to_list(100)
    return [MatchTimeProposal(**parse_from_mongo(proposal)) for proposal in proposals]

@api_router.post("/matches/{match_id}/vote-time/{proposal_id}")
async def vote_for_time_proposal(match_id: str, proposal_id: str, voter_id: str):
    """Vote for a time proposal"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if voter_id not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can vote")
    
    proposal = await db.match_time_proposals.find_one({"id": proposal_id})
    if not proposal:
        raise HTTPException(status_code=404, detail="Time proposal not found")
    
    # Add voter to the proposal if not already voted
    if voter_id not in proposal.get("votes", []):
        await db.match_time_proposals.update_one(
            {"id": proposal_id},
            {"$push": {"votes": voter_id}}
        )
        
        # Check if we have majority vote (more than half of participants)
        updated_proposal = await db.match_time_proposals.find_one({"id": proposal_id})
        votes_needed = len(match["participants"]) // 2 + 1
        
        if len(updated_proposal["votes"]) >= votes_needed:
            # Confirm the match with this time
            await db.matches.update_one(
                {"id": match_id},
                {
                    "$set": {
                        "scheduled_at": proposal["proposed_datetime"],
                        "venue_name": proposal["venue_name"],
                        "venue_address": proposal["venue_address"],
                        "status": MatchStatus.CONFIRMED
                    }
                }
            )
            
            # Create player confirmations for all participants
            for participant_id in match["participants"]:
                confirmation_obj = PlayerConfirmation(
                    match_id=match_id,
                    player_id=participant_id,
                    status=PlayerConfirmationStatus.PENDING
                )
                confirmation_mongo = prepare_for_mongo(confirmation_obj.dict())
                await db.player_confirmations.insert_one(confirmation_mongo)
            
            # Add system message
            if match["chat_thread_id"]:
                await create_system_message(
                    match["chat_thread_id"],
                    f"🎉 Match confirmed!\n" +
                    f"📅 {proposal['proposed_datetime'].strftime('%A, %B %d at %I:%M %p')}\n" +
                    f"📍 {proposal['venue_name'] or 'Venue TBD'}\n\n" +
                    f"Please confirm your attendance!"
                )
    
    return {"message": "Vote recorded successfully"}

@api_router.post("/matches/{match_id}/confirm")
async def confirm_match_participation(match_id: str, confirmation: PlayerConfirmationRequest, player_id: str):
    """Confirm or decline match participation"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if player_id not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can confirm")
    
    # Update or create confirmation
    existing_confirmation = await db.player_confirmations.find_one({
        "match_id": match_id,
        "player_id": player_id
    })
    
    if existing_confirmation:
        await db.player_confirmations.update_one(
            {"match_id": match_id, "player_id": player_id},
            {
                "$set": {
                    "status": confirmation.status,
                    "notes": confirmation.notes,
                    "response_at": datetime.now(timezone.utc)
                }
            }
        )
    else:
        confirmation_obj = PlayerConfirmation(
            match_id=match_id,
            player_id=player_id,
            status=confirmation.status,
            notes=confirmation.notes,
            response_at=datetime.now(timezone.utc)
        )
        confirmation_mongo = prepare_for_mongo(confirmation_obj.dict())
        await db.player_confirmations.insert_one(confirmation_mongo)
    
    # Add system message to chat
    if match["chat_thread_id"]:
        user = await db.users.find_one({"id": player_id})
        user_name = user["name"] if user else "Unknown"
        status_emoji = "✅" if confirmation.status == PlayerConfirmationStatus.ACCEPTED else "❌"
        
        await create_system_message(
            match["chat_thread_id"],
            f"{status_emoji} {user_name} {confirmation.status.lower()} the match" +
            (f"\n💬 {confirmation.notes}" if confirmation.notes else "")
        )
    
    return {"message": f"Match participation {confirmation.status.lower()}"}

@api_router.get("/matches/{match_id}/confirmations")
async def get_match_confirmations(match_id: str):
    """Get all player confirmations for a match"""
    confirmations = await db.player_confirmations.find({"match_id": match_id}).to_list(100)
    return [PlayerConfirmation(**parse_from_mongo(confirmation)) for confirmation in confirmations]

# Substitute Management Routes
@api_router.post("/matches/{match_id}/request-substitute")
async def request_substitute(match_id: str, request: SubstituteRequestCreate, requested_by: str):
    """Request a substitute for a match"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if request.original_player_id not in match["participants"]:
        raise HTTPException(status_code=400, detail="Original player is not in this match")
    
    # Check if requesting player has permission (original player or league manager)
    if requested_by != request.original_player_id:
        user = await db.users.find_one({"id": requested_by})
        if not user or user["role"] != UserRole.LEAGUE_MANAGER:
            raise HTTPException(status_code=403, detail="Only the player or league manager can request substitute")
    
    substitute_request_obj = SubstituteRequest(
        match_id=match_id,
        original_player_id=request.original_player_id,
        requested_by=requested_by,
        reason=request.reason
    )
    
    substitute_mongo = prepare_for_mongo(substitute_request_obj.dict())
    await db.substitute_requests.insert_one(substitute_mongo)
    
    # Add system message to chat
    if match["chat_thread_id"]:
        original_user = await db.users.find_one({"id": request.original_player_id})
        original_name = original_user["name"] if original_user else "Unknown"
        
        await create_system_message(
            match["chat_thread_id"],
            f"🔄 Substitute needed for {original_name}\n" +
            f"📋 Reason: {request.reason}\n\n" +
            f"Any available players can volunteer!"
        )
    
    return substitute_request_obj

@api_router.get("/matches/{match_id}/substitute-requests")
async def get_substitute_requests(match_id: str):
    """Get all substitute requests for a match"""
    requests = await db.substitute_requests.find({"match_id": match_id}).to_list(100)
    return [SubstituteRequest(**parse_from_mongo(request)) for request in requests]

@api_router.post("/substitute-requests/{request_id}/approve")
async def approve_substitute(request_id: str, approval: SubstituteApproval, approved_by: str):
    """Approve a substitute player"""
    substitute_request = await db.substitute_requests.find_one({"id": request_id})
    if not substitute_request:
        raise HTTPException(status_code=404, detail="Substitute request not found")
    
    match = await db.matches.find_one({"id": substitute_request["match_id"]})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    # Check if approver has permission (league manager or match participants)
    approver = await db.users.find_one({"id": approved_by})
    if (not approver or 
        (approver["role"] != UserRole.LEAGUE_MANAGER and approved_by not in match["participants"])):
        raise HTTPException(status_code=403, detail="Insufficient permissions to approve substitute")
    
    # Update substitute request
    await db.substitute_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "substitute_player_id": approval.substitute_player_id,
                "approved_by": approved_by,
                "status": SubstituteRequestStatus.FILLED
            }
        }
    )
    
    # Update match participants
    new_participants = [
        approval.substitute_player_id if p == substitute_request["original_player_id"] else p
        for p in match["participants"]
    ]
    
    await db.matches.update_one(
        {"id": substitute_request["match_id"]},
        {"$set": {"participants": new_participants}}
    )
    
    # Add substitute to match chat
    if match["chat_thread_id"]:
        # Add substitute to chat thread
        substitute_member = ChatThreadMember(
            thread_id=match["chat_thread_id"],
            user_id=approval.substitute_player_id
        )
        substitute_mongo = prepare_for_mongo(substitute_member.dict())
        await db.chat_thread_members.insert_one(substitute_mongo)
        
        # Update member count
        await db.chat_threads.update_one(
            {"id": match["chat_thread_id"]},
            {"$inc": {"member_count": 1}}
        )
        
        # Add system message
        substitute_user = await db.users.find_one({"id": approval.substitute_player_id})
        original_user = await db.users.find_one({"id": substitute_request["original_player_id"]})
        
        substitute_name = substitute_user["name"] if substitute_user else "Unknown"
        original_name = original_user["name"] if original_user else "Unknown"
        
        await create_system_message(
            match["chat_thread_id"],
            f"✅ {substitute_name} will substitute for {original_name}\n" +
            f"Welcome to the match chat!"
        )
    
    return {"message": "Substitute approved successfully"}

# Pre-Match Toss Routes
@api_router.post("/matches/{match_id}/toss")
async def conduct_pre_match_toss(match_id: str, toss_request: TossRequest, initiated_by: str):
    """Conduct a digital coin toss for serve/court selection"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if initiated_by not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can initiate toss")
    
    if match.get("toss_completed"):
        raise HTTPException(status_code=400, detail="Toss already completed for this match")
    
    # Randomly select winner
    import random
    winner_id = random.choice(match["participants"])
    
    # Randomly select what they get to choose (serve/return or court side)
    toss_choice = random.choice([TossResult.SERVE, TossResult.COURT_SIDE_A])
    
    # Create toss record
    toss_obj = PreMatchToss(
        match_id=match_id,
        initiated_by=initiated_by,
        winner_id=winner_id,
        choice=toss_choice
    )
    
    toss_mongo = prepare_for_mongo(toss_obj.dict())
    await db.pre_match_tosses.insert_one(toss_mongo)
    
    # Update match
    await db.matches.update_one(
        {"id": match_id},
        {
            "$set": {
                "toss_completed": True,
                "toss_winner_id": winner_id,
                "toss_choice": toss_choice
            }
        }
    )
    
    # Add system message to chat
    if match["chat_thread_id"]:
        winner_user = await db.users.find_one({"id": winner_id})
        winner_name = winner_user["name"] if winner_user else "Unknown"
        
        choice_text = "serve first" if toss_choice == TossResult.SERVE else "choose court side"
        
        await create_system_message(
            match["chat_thread_id"],
            f"🪙 **Toss Result**\n" +
            f"🎯 {winner_name} wins the toss!\n" +
            f"🎾 Choice: {choice_text}\n\n" +
            f"Good luck to all players!"
        )
    
    return {
        "winner_id": winner_id,
        "choice": toss_choice,
        "message": f"Toss completed! {winner_name} gets to {choice_text}"
    }

@api_router.get("/matches/{match_id}/toss")
async def get_match_toss(match_id: str):
    """Get toss result for a match"""
    toss = await db.pre_match_tosses.find_one({"match_id": match_id})
    if not toss:
        raise HTTPException(status_code=404, detail="No toss found for this match")
    
    return PreMatchToss(**parse_from_mongo(toss))

# Player Dashboard Data Routes
@api_router.get("/users/{user_id}/joined-tiers")
async def get_user_joined_tiers(user_id: str, sport_type: Optional[str] = None):
    """Get all rating tiers the user has joined"""
    # Find all player seats for this user
    player_seats = await db.player_seats.find({"user_id": user_id}).to_list(100)
    
    if not player_seats:
        return []
    
    joined_tiers = []
    for seat in player_seats:
        # Get the rating tier information
        rating_tier = await db.rating_tiers.find_one({"id": seat["rating_tier_id"]})
        if rating_tier:
            # Get format tier to check sport type
            format_tier = await db.format_tiers.find_one({"id": rating_tier["format_tier_id"]})
            if format_tier:
                # Get league information
                league = await db.leagues.find_one({"id": format_tier["league_id"]})
                if league and (not sport_type or league["sport_type"] == sport_type):
                    # Add seat status and group info
                    tier_data = parse_from_mongo(rating_tier.copy())
                    tier_data["seat_status"] = seat["status"]
                    tier_data["player_group_id"] = seat.get("player_group_id")
                    tier_data["joined_at"] = seat["joined_at"]
                    tier_data["league_name"] = league["name"]
                    tier_data["format_name"] = format_tier["name"]
                    tier_data["sport_type"] = league["sport_type"]
                    
                    # Get current player count
                    current_players = await db.player_seats.count_documents({
                        "rating_tier_id": rating_tier["id"],
                        "status": PlayerSeatStatus.ACTIVE
                    })
                    tier_data["current_players"] = current_players
                    
                    joined_tiers.append(tier_data)
    
    return joined_tiers

@api_router.get("/users/{user_id}/standings")
async def get_user_standings(user_id: str, sport_type: Optional[str] = None):
    """Get user's standings across all joined leagues"""
    # Get user's player stats
    player_stats = await db.player_set_stats.find({"player_id": user_id}).to_list(100)
    
    standings = []
    for stats in player_stats:
        # Get rating tier info
        rating_tier = await db.rating_tiers.find_one({"id": stats["rating_tier_id"]})
        if rating_tier:
            # Get format and league info
            format_tier = await db.format_tiers.find_one({"id": rating_tier["format_tier_id"]})
            if format_tier:
                league = await db.leagues.find_one({"id": format_tier["league_id"]})
                if league and (not sport_type or league["sport_type"] == sport_type):
                    standing_data = {
                        "league_name": league["name"],
                        "format_name": format_tier["name"],
                        "tier_name": rating_tier["name"],
                        "rank": stats["rank"],
                        "total_sets_won": stats["total_sets_won"],
                        "total_sets_played": stats["total_sets_played"],
                        "set_win_percentage": stats["set_win_percentage"],
                        "matches_played": stats["matches_played"],
                        "matches_won": stats["matches_won"],
                        "win_percentage": stats["win_percentage"]
                    }
                    standings.append(standing_data)
    
    return standings

@api_router.get("/users/{user_id}/matches")
async def get_user_matches(user_id: str, sport_type: Optional[str] = None):
    """Get user's upcoming matches"""
    # Find matches where user is a participant
    matches = await db.matches.find({"participants": user_id}).to_list(100)
    
    user_matches = []
    for match in matches:
        # Get rating tier and league info
        rating_tier = await db.rating_tiers.find_one({"id": match["rating_tier_id"]})
        if rating_tier:
            format_tier = await db.format_tiers.find_one({"id": rating_tier["format_tier_id"]})
            if format_tier:
                league = await db.leagues.find_one({"id": format_tier["league_id"]})
                if league and (not sport_type or league["sport_type"] == sport_type):
                    match_data = match.copy()
                    match_data["league_name"] = league["name"]
                    match_data["format_name"] = format_tier["name"]
                    match_data["tier_name"] = rating_tier["name"]
                    user_matches.append(match_data)
    
    return user_matches

# Profile Picture Management Routes
@api_router.post("/users/{user_id}/upload-picture")
async def upload_profile_picture(user_id: str, file: UploadFile = File(...)):
    """Upload and update user profile picture"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Check file size (limit to 5MB)
    if file.size > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 5MB")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Generate unique filename
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        unique_filename = f"profile_{user_id}_{int(time.time())}.{file_extension}"
        
        # In a real implementation, you would upload to cloud storage (S3, etc.)
        # For now, we'll create a data URL (base64 encoded)
        import base64
        file_base64 = base64.b64encode(file_content).decode()
        profile_picture_url = f"data:{file.content_type};base64,{file_base64}"
        
        # Update user profile
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"profile_picture": profile_picture_url}}
        )
        
        # Get updated user
        updated_user = await db.users.find_one({"id": user_id})
        
        return {
            "message": "Profile picture uploaded successfully",
            "profile_picture": profile_picture_url,
            "user": UserProfile(**parse_from_mongo(updated_user))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload profile picture: {str(e)}")

@api_router.delete("/users/{user_id}/remove-picture")
async def remove_profile_picture(user_id: str):
    """Remove user profile picture"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Remove profile picture
    await db.users.update_one(
        {"id": user_id},
        {"$unset": {"profile_picture": "", "photo_url": ""}}
    )
    
    return {"message": "Profile picture removed successfully"}

# Set-by-Set Scoring Routes  
@api_router.post("/matches/{match_id}/score-set")
async def update_set_score(match_id: str, set_score: SetScoreUpdate, updated_by: str):
    """Update score for a specific set"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if updated_by not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can update scores")
    
    # Create or update the set result
    existing_set = await db.set_results.find_one({
        "match_id": match_id,
        "set_number": set_score.set_number
    })
    
    set_data = set_score.dict()
    set_data["match_id"] = match_id
    
    # Determine set winner if set is complete
    if set_score.is_set_complete:
        set_winner_ids = []
        
        if match["format"] == LeagueFormat.SINGLES:
            if set_score.player1_score and set_score.player2_score:
                if set_score.player1_score > set_score.player2_score:
                    # Need to map to actual player IDs
                    set_winner_ids = [match["participants"][0]]  # Assuming first participant is player1
                else:
                    set_winner_ids = [match["participants"][1]]
        
        elif match["format"] == LeagueFormat.DOUBLES:
            if set_score.team_a_score and set_score.team_b_score:
                if set_score.team_a_score > set_score.team_b_score:
                    set_winner_ids = match["participants"][:2]  # First two are team A
                else:
                    set_winner_ids = match["participants"][2:]  # Last two are team B
        
        set_data["set_winner_ids"] = set_winner_ids
        set_data["completed_at"] = datetime.now(timezone.utc)
    
    if existing_set:
        await db.set_results.update_one(
            {"match_id": match_id, "set_number": set_score.set_number},
            {"$set": set_data}
        )
    else:
        set_obj = SetResult(**set_data)
        set_mongo = prepare_for_mongo(set_obj.dict())
        await db.set_results.insert_one(set_mongo)
    
    # Add system message to match chat
    if match["chat_thread_id"]:
        score_text = ""
        if match["format"] == LeagueFormat.SINGLES:
            score_text = f"Set {set_score.set_number}: {set_score.player1_score}-{set_score.player2_score}"
        else:
            score_text = f"Set {set_score.set_number}: Team A {set_score.team_a_score}-{set_score.team_b_score} Team B"
        
        status_text = " ✅ SET COMPLETE" if set_score.is_set_complete else " (in progress)"
        
        await create_system_message(
            match["chat_thread_id"],
            f"🎾 Score Update\n{score_text}{status_text}"
        )
    
    return {"message": "Set score updated successfully"}

@api_router.post("/matches/{match_id}/submit-final-score")
async def submit_match_result(match_id: str, result: MatchScoreSubmission, submitted_by: str):
    """Submit final match result with all set scores"""
    match = await db.matches.find_one({"id": match_id})
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    
    if submitted_by not in match["participants"]:
        raise HTTPException(status_code=403, detail="Only match participants can submit results")
    
    # Process each set result
    processed_sets = []
    for set_update in result.sets:
        set_data = set_update.dict()
        set_data["match_id"] = match_id
        
        # Determine set winner
        if set_update.is_set_complete:
            set_winner_ids = []
            
            if match["format"] == LeagueFormat.SINGLES:
                if set_update.player1_score > set_update.player2_score:
                    set_winner_ids = [match["participants"][0]]
                else:
                    set_winner_ids = [match["participants"][1]]
            
            elif match["format"] == LeagueFormat.DOUBLES:
                if set_update.team_a_score > set_update.team_b_score:
                    set_winner_ids = match["participants"][:2]
                else:
                    set_winner_ids = match["participants"][2:]
            
            set_data["set_winner_ids"] = set_winner_ids
            set_data["completed_at"] = datetime.now(timezone.utc)
        
        set_obj = SetResult(**set_data)
        processed_sets.append(set_obj)
        
        # Save set result
        set_mongo = prepare_for_mongo(set_obj.dict())
        await db.set_results.update_one(
            {"match_id": match_id, "set_number": set_update.set_number},
            {"$set": set_mongo},
            upsert=True
        )
    
    # Create match result record
    match_result = MatchResult(
        match_id=match_id,
        sets=processed_sets,
        winner_ids=result.match_winner_ids,
        submitted_by=submitted_by,
        total_sets_played=len(processed_sets),
        match_completed=True
    )
    
    match_result_mongo = prepare_for_mongo(match_result.dict())
    await db.match_results.insert_one(match_result_mongo)
    
    # Update match status to PLAYED
    await db.matches.update_one(
        {"id": match_id},
        {"$set": {"status": MatchStatus.PLAYED}}
    )
    
    # Update player statistics
    updated_stats = update_player_stats_from_match(match, match_result)
    
    for stats in updated_stats:
        # Get existing stats for this player
        existing_stats = await db.player_set_stats.find_one({
            "player_id": stats.player_id,
            "rating_tier_id": stats.rating_tier_id
        })
        
        if existing_stats:
            # Update cumulative stats
            await db.player_set_stats.update_one(
                {"player_id": stats.player_id, "rating_tier_id": stats.rating_tier_id},
                {
                    "$inc": {
                        "total_sets_won": stats.total_sets_won,
                        "total_sets_played": stats.total_sets_played,
                        "matches_played": stats.matches_played,
                        "matches_won": stats.matches_won
                    },
                    "$set": {"last_updated": stats.last_updated}
                }
            )
            
            # Recalculate percentages
            updated_record = await db.player_set_stats.find_one({
                "player_id": stats.player_id,
                "rating_tier_id": stats.rating_tier_id
            })
            
            new_set_win_pct = updated_record["total_sets_won"] / updated_record["total_sets_played"] if updated_record["total_sets_played"] > 0 else 0.0
            new_match_win_pct = updated_record["matches_won"] / updated_record["matches_played"] if updated_record["matches_played"] > 0 else 0.0
            
            await db.player_set_stats.update_one(
                {"player_id": stats.player_id, "rating_tier_id": stats.rating_tier_id},
                {
                    "$set": {
                        "set_win_percentage": new_set_win_pct,
                        "win_percentage": new_match_win_pct
                    }
                }
            )
        else:
            # Create new stats record
            stats.set_win_percentage = stats.total_sets_won / stats.total_sets_played if stats.total_sets_played > 0 else 0.0
            stats_mongo = prepare_for_mongo(stats.dict())
            await db.player_set_stats.insert_one(stats_mongo)
    
    # Add final score to match chat
    if match["chat_thread_id"]:
        winner_names = []
        for winner_id in result.match_winner_ids:
            user = await db.users.find_one({"id": winner_id})
            if user:
                winner_names.append(user["name"])
        
        await create_system_message(
            match["chat_thread_id"],
            f"🏆 **Match Complete!**\n" +
            f"🎉 Winner(s): {', '.join(winner_names)}\n" +
            f"📊 Total sets played: {len(processed_sets)}\n\n" +
            f"Great match everyone! 🎾"
        )
    
    return {
        "message": "Match result submitted successfully",
        "match_result": match_result
    }

@api_router.get("/matches/{match_id}/score")
async def get_match_score(match_id: str):
    """Get current score for a match"""
    sets = await db.set_results.find({"match_id": match_id}).sort("set_number", 1).to_list(100)
    
    if not sets:
        return {"message": "No scores recorded yet", "sets": []}
    
    return {
        "sets": [SetResult(**parse_from_mongo(set_result)) for set_result in sets],
        "total_sets": len(sets)
    }

# Rankings and Standings Routes
@api_router.get("/rating-tiers/{tier_id}/standings")
async def get_tier_standings(tier_id: str, group_id: Optional[str] = None):
    """Get current standings for a rating tier"""
    query = {"rating_tier_id": tier_id}
    if group_id:
        query["player_group_id"] = group_id
    
    stats = await db.player_set_stats.find(query).to_list(100)
    
    if not stats:
        return {"message": "No standings available yet", "standings": []}
    
    # Convert to PlayerSetStats objects and calculate rankings
    player_stats = [PlayerSetStats(**parse_from_mongo(stat)) for stat in stats]
    ranked_players = calculate_player_rankings(player_stats)
    
    return {
        "standings": ranked_players,
        "total_players": len(ranked_players),
        "last_updated": datetime.now(timezone.utc)
    }

@api_router.get("/rating-tiers/{tier_id}/playoff-qualifiers")
async def get_playoff_qualifiers(tier_id: str, playoff_spots: int = 8):
    """Get players qualified for playoffs"""
    stats = await db.player_set_stats.find({"rating_tier_id": tier_id}).to_list(100)
    
    if len(stats) < playoff_spots:
        raise HTTPException(status_code=400, detail=f"Not enough players for playoffs. Need {playoff_spots}, have {len(stats)}")
    
    player_stats = [PlayerSetStats(**parse_from_mongo(stat)) for stat in stats]
    qualifiers = determine_playoff_qualifiers(player_stats, playoff_spots)
    
    # Get qualifier details
    qualifier_details = []
    for player_id in qualifiers:
        user = await db.users.find_one({"id": player_id})
        stats = next((s for s in player_stats if s.player_id == player_id), None)
        
        if user and stats:
            qualifier_details.append({
                "player_id": player_id,
                "player_name": user["name"],
                "rank": stats.rank,
                "total_sets_won": stats.total_sets_won,
                "set_win_percentage": stats.set_win_percentage,
                "matches_played": stats.matches_played
            })
    
    return {
        "qualifiers": qualifier_details,
        "playoff_spots": playoff_spots,
        "total_eligible_players": len(stats)
    }

@api_router.post("/rating-tiers/{tier_id}/create-playoff-bracket")
async def create_playoff_bracket(tier_id: str, playoff_spots: int = 8, created_by: str = None):
    """Create playoff bracket for top players"""
    # Get tier info to verify it uses Team League Format
    tier = await db.rating_tiers.find_one({"id": tier_id})
    if not tier:
        raise HTTPException(status_code=404, detail="Rating tier not found")
    
    if tier["competition_system"] != CompetitionSystem.TEAM_LEAGUE:
        raise HTTPException(status_code=400, detail="Playoffs only available for Team League Format")
    
    # Check if bracket already exists
    existing_bracket = await db.playoff_brackets.find_one({"rating_tier_id": tier_id})
    if existing_bracket:
        return PlayoffBracket(**parse_from_mongo(existing_bracket))
    
    # Get qualifiers
    stats = await db.player_set_stats.find({"rating_tier_id": tier_id}).to_list(100)
    if len(stats) < playoff_spots:
        raise HTTPException(status_code=400, detail=f"Not enough players for playoffs. Need {playoff_spots}, have {len(stats)}")
    
    player_stats = [PlayerSetStats(**parse_from_mongo(stat)) for stat in stats]
    qualifiers = determine_playoff_qualifiers(player_stats, playoff_spots)
    
    # Create bracket
    bracket = PlayoffBracket(
        rating_tier_id=tier_id,
        qualified_players=qualifiers
    )
    
    bracket_mongo = prepare_for_mongo(bracket.dict())
    await db.playoff_brackets.insert_one(bracket_mongo)
    
    return {
        "message": "Playoff bracket created successfully",
        "bracket": bracket,
        "qualifiers_count": len(qualifiers)
    }

# Comprehensive Chat System Routes (Phase 5)
@api_router.post("/chat/messages")
async def send_message(message_data: ChatMessageCreate, sender_id: str):
    """Send a message to a chat thread"""
    # Verify sender is member of thread
    member = await db.chat_thread_members.find_one({
        "thread_id": message_data.thread_id,
        "user_id": sender_id
    })
    
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Get sender info
    sender = await db.users.find_one({"id": sender_id})
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    # Process mentions (@username)
    mentions = []
    if "@" in message_data.text:
        # Simple mention detection (in production, use more sophisticated parsing)
        thread_members = await db.chat_thread_members.find({"thread_id": message_data.thread_id}).to_list(100)
        for member_data in thread_members:
            user = await db.users.find_one({"id": member_data["user_id"]})
            if user and f"@{user['name']}" in message_data.text:
                mentions.append(user["id"])
    
    # Detect slash commands
    slash_command = None
    if message_data.text.startswith("/"):
        command_text = message_data.text.split()[0]
        try:
            slash_command = SlashCommand(command_text)
        except ValueError:
            pass  # Not a recognized slash command
    
    # Create message
    message_obj = ChatMessage(
        thread_id=message_data.thread_id,
        sender_id=sender_id,
        sender_name=sender["name"],
        text=message_data.text,
        type=message_data.type,
        reply_to_message_id=message_data.reply_to_message_id,
        attachments=message_data.attachments,
        mentions=mentions,
        slash_command=slash_command,
        action_payload=message_data.action_payload
    )
    
    message_mongo = prepare_for_mongo(message_obj.dict())
    await db.chat_messages.insert_one(message_mongo)
    
    # Update thread last message time
    await db.chat_threads.update_one(
        {"id": message_data.thread_id},
        {
            "$set": {"last_message_at": datetime.now(timezone.utc)},
            "$inc": {"unread_count": 1}
        }
    )
    
    # Send mention notifications
    for mentioned_user_id in mentions:
        if mentioned_user_id != sender_id:  # Don't notify self
            notification = NotificationCreate(
                user_id=mentioned_user_id,
                title="You were mentioned",
                message=f"{sender['name']} mentioned you in chat",
                type=NotificationType.CHAT_MESSAGE,
                related_entity_id=message_obj.id
            )
            await create_notification(notification)
    
    # Handle slash commands
    if slash_command:
        await handle_slash_command(slash_command, message_obj, message_data)
    
    return message_obj

@api_router.get("/chat/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str, limit: int = 50, before: Optional[str] = None, user_id: str = None):
    """Get messages for a chat thread"""
    # Verify user is member of thread
    if user_id:
        member = await db.chat_thread_members.find_one({
            "thread_id": thread_id,
            "user_id": user_id
        })
        if not member:
            raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Build query
    query = {"thread_id": thread_id}
    if before:
        # Get messages before a specific message ID (for pagination)
        before_message = await db.chat_messages.find_one({"id": before})
        if before_message:
            query["created_at"] = {"$lt": before_message["created_at"]}
    
    # Get messages
    messages = await db.chat_messages.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    messages.reverse()  # Return in chronological order
    
    return [ChatMessage(**parse_from_mongo(message)) for message in messages]

@api_router.post("/chat/messages/{message_id}/react")
async def react_to_message(message_id: str, reaction: MessageReactionRequest, user_id: str):
    """Add or remove a reaction to a message"""
    message = await db.chat_messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is member of thread
    member = await db.chat_thread_members.find_one({
        "thread_id": message["thread_id"],
        "user_id": user_id
    })
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Get current reactions
    reactions = message.get("reactions", {})
    reaction_type = reaction.reaction_type.value
    
    # Toggle reaction
    if reaction_type not in reactions:
        reactions[reaction_type] = []
    
    if user_id in reactions[reaction_type]:
        # Remove reaction
        reactions[reaction_type].remove(user_id)
        if not reactions[reaction_type]:  # Remove empty reaction list
            del reactions[reaction_type]
    else:
        # Add reaction
        reactions[reaction_type].append(user_id)
    
    # Update message
    await db.chat_messages.update_one(
        {"id": message_id},
        {"$set": {"reactions": reactions}}
    )
    
    # Create reaction record for analytics
    reaction_obj = MessageReaction(
        message_id=message_id,
        user_id=user_id,
        reaction_type=reaction.reaction_type
    )
    reaction_mongo = prepare_for_mongo(reaction_obj.dict())
    await db.message_reactions.insert_one(reaction_mongo)
    
    return {"message": "Reaction updated successfully", "reactions": reactions}

@api_router.patch("/chat/messages/{message_id}")
async def edit_message(message_id: str, edit_data: EditMessageRequest, user_id: str):
    """Edit a message"""
    message = await db.chat_messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    if message["sender_id"] != user_id:
        raise HTTPException(status_code=403, detail="Can only edit your own messages")
    
    # Check if message is recent (allow editing within 15 minutes)
    message_time = datetime.fromisoformat(message["created_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) - message_time > timedelta(minutes=15):
        raise HTTPException(status_code=400, detail="Message is too old to edit")
    
    # Update message
    await db.chat_messages.update_one(
        {"id": message_id},
        {
            "$set": {
                "text": edit_data.new_text,
                "is_edited": True,
                "edited_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Message edited successfully"}

@api_router.post("/chat/messages/{message_id}/pin")
async def pin_message(message_id: str, pin_data: PinMessageRequest, user_id: str):
    """Pin or unpin a message"""
    message = await db.chat_messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Check if user is admin/moderator of thread
    member = await db.chat_thread_members.find_one({
        "thread_id": message["thread_id"],
        "user_id": user_id
    })
    
    if not member or member["role"] not in ["admin", "moderator"]:
        raise HTTPException(status_code=403, detail="Only admins and moderators can pin messages")
    
    # Update message
    await db.chat_messages.update_one(
        {"id": message_id},
        {"$set": {"is_pinned": pin_data.pin}}
    )
    
    # Update thread pinned messages
    if pin_data.pin:
        await db.chat_threads.update_one(
            {"id": message["thread_id"]},
            {"$addToSet": {"pinned_message_ids": message_id}}
        )
    else:
        await db.chat_threads.update_one(
            {"id": message["thread_id"]},
            {"$pull": {"pinned_message_ids": message_id}}
        )
    
    action_text = "pinned" if pin_data.pin else "unpinned"
    return {"message": f"Message {action_text} successfully"}

@api_router.post("/chat/threads/{thread_id}/typing")
async def update_typing_indicator(thread_id: str, user_id: str):
    """Update typing indicator for user in thread"""
    # Verify user is member of thread
    member = await db.chat_thread_members.find_one({
        "thread_id": thread_id,
        "user_id": user_id
    })
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Update typing timestamp
    await db.chat_thread_members.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {"$set": {"last_typing_at": datetime.now(timezone.utc)}}
    )
    
    return {"message": "Typing indicator updated"}

@api_router.get("/chat/threads/{thread_id}/typing")
async def get_typing_indicators(thread_id: str, user_id: str = None):
    """Get currently typing users in thread"""
    # Verify user is member of thread if user_id provided
    if user_id:
        member = await db.chat_thread_members.find_one({
            "thread_id": thread_id,
            "user_id": user_id
        })
        if not member:
            raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Get members who were typing in last 5 seconds
    cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=5)
    
    typing_members = await db.chat_thread_members.find({
        "thread_id": thread_id,
        "last_typing_at": {"$gt": cutoff_time}
    }).to_list(10)
    
    # Get user details for typing indicators
    typing_users = []
    for member in typing_members:
        if member["user_id"] != user_id:  # Don't include requester
            user = await db.users.find_one({"id": member["user_id"]})
            if user:
                typing_users.append({
                    "user_id": user["id"],
                    "user_name": user["name"],
                    "started_at": member["last_typing_at"]
                })
    
    return {"typing_users": typing_users}

@api_router.post("/chat/threads/{thread_id}/mark-read")
async def mark_messages_read(thread_id: str, message_id: Optional[str] = None, user_id: str = None):
    """Mark messages as read up to a specific message"""
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID required")
    
    # Verify user is member of thread
    member = await db.chat_thread_members.find_one({
        "thread_id": thread_id,
        "user_id": user_id
    })
    if not member:
        raise HTTPException(status_code=403, detail="User is not a member of this thread")
    
    # Update last read timestamp
    read_time = datetime.now(timezone.utc)
    await db.chat_thread_members.update_one(
        {"thread_id": thread_id, "user_id": user_id},
        {"$set": {"last_read_at": read_time}}
    )
    
    # Mark specific messages as read
    if message_id:
        # Mark all messages up to this message as read
        message = await db.chat_messages.find_one({"id": message_id})
        if message:
            await db.chat_messages.update_many(
                {
                    "thread_id": thread_id,
                    "created_at": {"$lte": message["created_at"]}
                },
                {"$addToSet": {"read_by": user_id}}
            )
    else:
        # Mark all messages as read
        await db.chat_messages.update_many(
            {"thread_id": thread_id},
            {"$addToSet": {"read_by": user_id}}
        )
    
    return {"message": "Messages marked as read"}

async def handle_slash_command(command: SlashCommand, message: ChatMessage, message_data: ChatMessageCreate):
    """Handle slash commands in chat"""
    thread_id = message.thread_id
    sender_id = message.sender_id
    
    try:
        if command == SlashCommand.WHEN:
            # Extract proposed time from message
            response_text = "⏰ Use the 'Propose Time' button to suggest match times!"
            
        elif command == SlashCommand.WHERE:
            # Extract venue suggestion
            venue_text = message.text.replace("/where", "").strip()
            response_text = f"📍 Venue suggestion: {venue_text}" if venue_text else "📍 Please specify a venue location"
            
        elif command == SlashCommand.LINEUP:
            # Show current match lineup
            response_text = "📋 Use the match card to see current participants and confirmations"
            
        elif command == SlashCommand.SUBS:
            # Handle substitute requests
            response_text = "🔄 Use the 'Request Substitute' feature in the match card"
            
        elif command == SlashCommand.SCORE:
            # Quick score update
            response_text = "🎾 Use the scoring interface to update match scores"
            
        elif command == SlashCommand.TOSS:
            # Conduct toss
            response_text = "🪙 Use the 'Coin Toss' button to conduct pre-match toss"
            
        else:
            response_text = f"❓ Unknown command: {command.value}"
        
        # Send system response
        await create_system_message(thread_id, response_text)
        
    except Exception as e:
        await create_system_message(thread_id, f"❌ Error processing command: {str(e)}")

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