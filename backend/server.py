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
    CAPTAIN = "Captain"
    ADMIN = "Admin"

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

# Utility functions
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

# Pydantic Models
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = Field(ge=3.0, le=5.5)
    photo_url: Optional[str] = None
    roles: List[UserRole] = Field(default_factory=lambda: [UserRole.PLAYER])
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserProfileCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = Field(ge=3.0, le=5.5)
    photo_url: Optional[str] = None

class League(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    surface: str = "Hard Court"
    region: str
    level: str
    format: LeagueFormat
    rules_md: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LeagueCreate(BaseModel):
    name: str
    surface: str = "Hard Court"
    region: str
    level: str
    format: LeagueFormat
    rules_md: Optional[str] = None

class Season(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    name: str
    start_date: date
    end_date: date
    status: SeasonStatus = SeasonStatus.DRAFT
    weeks: int = 9
    max_players: int = 36
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SeasonCreate(BaseModel):
    league_id: str
    name: str
    start_date: date
    end_date: date
    weeks: int = 9
    max_players: int = 36

class PlayerSeat(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    season_id: str
    user_id: str
    status: PlayerSeatStatus = PlayerSeatStatus.ACTIVE
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Match(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    season_id: str
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
    season_id: str
    user_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AvailabilityCreate(BaseModel):
    season_id: str
    week_number: int
    status: AvailabilityStatus
    note: Optional[str] = None

class StandingSnapshot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    season_id: str
    player_id: str
    total_set_wins: int = 0
    total_sets_played: int = 0
    win_pct: float = 0.0
    rank: int = 0
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

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

# League Routes
@api_router.post("/leagues", response_model=League)
async def create_league(league_data: LeagueCreate, created_by: str = "system"):
    league_dict = league_data.dict()
    league_dict["created_by"] = created_by
    league_obj = League(**league_dict)
    league_mongo = prepare_for_mongo(league_obj.dict())
    await db.leagues.insert_one(league_mongo)
    return league_obj

@api_router.get("/leagues", response_model=List[League])
async def get_leagues():
    leagues = await db.leagues.find().to_list(100)
    return [League(**parse_from_mongo(league)) for league in leagues]

@api_router.get("/leagues/{league_id}", response_model=League)
async def get_league(league_id: str):
    league = await db.leagues.find_one({"id": league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return League(**parse_from_mongo(league))

# Season Routes
@api_router.post("/seasons", response_model=Season)  
async def create_season(season_data: SeasonCreate):
    # Verify league exists
    league = await db.leagues.find_one({"id": season_data.league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    season_dict = season_data.dict()
    season_obj = Season(**season_dict)
    season_mongo = prepare_for_mongo(season_obj.dict())
    await db.seasons.insert_one(season_mongo)
    return season_obj

@api_router.get("/seasons", response_model=List[Season])
async def get_seasons():
    seasons = await db.seasons.find().to_list(100)
    return [Season(**parse_from_mongo(season)) for season in seasons]

@api_router.get("/leagues/{league_id}/seasons", response_model=List[Season])
async def get_league_seasons(league_id: str):
    seasons = await db.seasons.find({"league_id": league_id}).to_list(100)
    return [Season(**parse_from_mongo(season)) for season in seasons]

# Player Seat Routes (Join League)
@api_router.post("/seasons/{season_id}/join")
async def join_season(season_id: str, user_id: str):
    # Check if season exists
    season = await db.seasons.find_one({"id": season_id})
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # Check if user already joined
    existing_seat = await db.player_seats.find_one({"season_id": season_id, "user_id": user_id})
    if existing_seat:
        raise HTTPException(status_code=400, detail="User already joined this season")
    
    # Count current players
    player_count = await db.player_seats.count_documents({"season_id": season_id, "status": PlayerSeatStatus.ACTIVE})
    
    # Determine status based on capacity
    status = PlayerSeatStatus.ACTIVE if player_count < season["max_players"] else PlayerSeatStatus.RESERVE
    
    seat_obj = PlayerSeat(season_id=season_id, user_id=user_id, status=status)
    seat_mongo = prepare_for_mongo(seat_obj.dict())
    await db.player_seats.insert_one(seat_mongo)
    
    return {"message": f"Successfully joined season with status: {status}", "status": status}

@api_router.get("/seasons/{season_id}/players", response_model=List[dict])
async def get_season_players(season_id: str):
    # Get player seats
    seats = await db.player_seats.find({"season_id": season_id}).to_list(100)
    
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

# Availability Routes
@api_router.post("/availability")
async def set_availability(availability_data: AvailabilityCreate, user_id: str):
    # Check if availability already exists for this user/season/week
    existing = await db.availability.find_one({
        "season_id": availability_data.season_id,
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

@api_router.get("/seasons/{season_id}/availability/{week_number}")
async def get_week_availability(season_id: str, week_number: int):
    availability_records = await db.availability.find({
        "season_id": season_id,
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

# Simple Match Generation (MVP version)
@api_router.post("/seasons/{season_id}/generate-matches/{week_number}")
async def generate_weekly_matches(season_id: str, week_number: int):
    # Get available players for this week
    available_players = await db.availability.find({
        "season_id": season_id,
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
                season_id=season_id,
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
            
            matches.append(match_obj)
    
    return {"message": f"Generated {len(matches)} matches for week {week_number}", "matches": matches}

# Get Matches
@api_router.get("/seasons/{season_id}/matches")
async def get_season_matches(season_id: str, week_number: Optional[int] = None):
    query = {"season_id": season_id}
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

# Submit Scores
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
    
    # Recalculate standings
    await recalculate_season_standings(match_id)
    
    return {"message": "Scores submitted successfully"}

async def recalculate_season_standings(match_id: str):
    """Recalculate standings for a season based on submitted scores"""
    # Get match to find season
    match = await db.matches.find_one({"id": match_id})
    if not match:
        return
    
    season_id = match["season_id"]
    
    # Get all players in season
    players = await db.player_seats.find({"season_id": season_id, "status": PlayerSeatStatus.ACTIVE}).to_list(100)
    
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
            "season_id": season_id,
            "player_id": user_id,
            "total_set_wins": total_set_wins,
            "total_sets_played": total_sets_played,
            "win_pct": win_pct,
            "updated_at": datetime.now(timezone.utc)
        }
        
        await db.standings.update_one(
            {"season_id": season_id, "player_id": user_id},
            {"$set": prepare_for_mongo(standing_data)},
            upsert=True
        )

# Standings
@api_router.get("/seasons/{season_id}/standings")
async def get_season_standings(season_id: str):
    standings = await db.standings.find({"season_id": season_id}).sort("total_set_wins", -1).to_list(100)
    
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