import os
import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Literal
from collections import Counter
import asyncio
from fastapi.responses import StreamingResponse
from fastapi import UploadFile, File
from fastapi.staticfiles import StaticFiles


from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ========= FastAPI app =========
app = FastAPI(title="LeagueAce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ingress handles real origin; keep permissive for internal routing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploaded images
UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ========= DB =========
MONGO_URL = os.environ.get("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL not set in backend/.env")

# ========= RR Helpers =========
async def rr_notify(user_ids: List[str], message: str, meta: Optional[Dict[str, Any]] = None):
    if not user_ids:
        return
    doc = {
        "id": str(uuid.uuid4()),
        "user_ids": user_ids,
        "message": message,
        "meta": meta or {},
        "created_at": now_utc().isoformat(),
        "read_by": []
    }
    await db.rr_notifications.insert_one(doc)

async def rr_audit(action: str, match_id: Optional[str], actor_id: Optional[str], meta: Optional[Dict[str, Any]] = None):
    rec = {
        "id": str(uuid.uuid4()),
        "action": action,
        "match_id": match_id,
        "actor_id": actor_id,
        "meta": meta or {},
        "created_at": now_utc().isoformat(),
    }
    await db.rr_audits.insert_one(rec)

client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URL)
db = client.get_default_database()

# ========= Helpers =========

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def prepare_for_mongo(doc: Dict[str, Any]) -> Dict[str, Any]:
    out = {**doc}
    if "_id" in out:
        out.pop("_id", None)
    # Convert datetime to iso string for safety
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


def parse_from_mongo(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not doc:
        return doc
    out = {**doc}
    out.pop("_id", None)
    return out

# ========= Minimal Users (LAN) to support RR UX =========
class UserProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = 4.0
    lan: Optional[str] = None
    role: Optional[str] = "Player"
    created_at: datetime = Field(default_factory=now_utc)

class UserProfileCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = 4.0
    lan: Optional[str] = None
    role: Optional[str] = "Player"

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    lan: Optional[str] = None

async def generate_unique_lan() -> str:
    while True:
        code = 'LAN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        existing = await db.users.find_one({"lan": code})
        if not existing:
            return code

@app.post("/api/users", response_model=UserProfile)
async def create_user(user_data: UserProfileCreate):
    data = user_data.dict()
    if not data.get("lan"):
        data["lan"] = await generate_unique_lan()
    if not data.get("role"):
        data["role"] = "Player"
    user = UserProfile(**data)
    await db.users.insert_one(prepare_for_mongo(user.dict()))
    return user

@app.patch("/api/users/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, payload: UserProfileUpdate):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in payload.dict(exclude_unset=True).items() if v is not None}
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        user.update(update_data)
    
    return UserProfile(**user)

@app.post("/api/users/{user_id}/upload-picture")
async def upload_picture(user_id: str, file: UploadFile = File(...)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Save file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    fname = f"{user_id}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    url = f"/api/uploads/{fname}"
    await db.users.update_one({"id": user_id}, {"$set": {"photo_url": url}})
    return {"url": url}

    data = {k: v for k, v in payload.dict().items() if v is not None}
    if "lan" in data and data["lan"]:
        ex = await db.users.find_one({"lan": data["lan"]})
        if ex and ex.get("id") != user_id:
            raise HTTPException(status_code=400, detail="LAN already in use")
    if data:
        await db.users.update_one({"id": user_id}, {"$set": prepare_for_mongo(data)})
    doc = await db.users.find_one({"id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile(**parse_from_mongo(doc))

# ========= League/Format/Rating Tier Models =========
class LeagueCreate(BaseModel):
    name: str
    sport_type: Literal["Tennis", "Pickleball"]
    description: Optional[str] = None

class League(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    sport_type: str
    description: Optional[str] = None
    manager_id: str
    created_at: datetime = Field(default_factory=now_utc)

class FormatTierCreate(BaseModel):
    league_id: str
    name: str
    format_type: Literal["Singles", "Doubles", "Round Robin"]
    description: Optional[str] = None

class FormatTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    league_id: str
    name: str
    format_type: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

class RatingTierCreate(BaseModel):
    format_tier_id: str
    name: str
    min_rating: float = 3.0
    max_rating: float = 5.0
    max_players: int = 36
    competition_system: Literal["Team League Format", "Knockout System"] = "Team League Format"
    playoff_spots: Optional[int] = 8
    region: Optional[str] = None
    surface: Optional[str] = None

class RatingTier(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    format_tier_id: str
    name: str
    min_rating: float
    max_rating: float
    max_players: int
    competition_system: str
    playoff_spots: Optional[int] = None
    region: Optional[str] = None
    surface: Optional[str] = None
    join_code: str
    created_at: datetime = Field(default_factory=now_utc)

class RatingTierUpdate(BaseModel):
    min_rating: Optional[float] = None
    max_rating: Optional[float] = None

class CreateGroupsRequest(BaseModel):
    group_size: Optional[int] = None
    custom_names: Optional[List[str]] = None

class PlayerGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    name: str
    group_size: int
    created_at: datetime = Field(default_factory=now_utc)


def generate_join_code() -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ========= League/Format/Rating Tier Endpoints =========
@app.post("/api/leagues")
async def create_league(league: LeagueCreate, created_by: Optional[str] = None):
    if not created_by:
        raise HTTPException(status_code=400, detail="created_by (manager_id) is required")
    # verify user exists
    manager = await db.users.find_one({"id": created_by})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager user not found")
    row = League(name=league.name, sport_type=league.sport_type, description=league.description, manager_id=created_by)
    await db.leagues.insert_one(prepare_for_mongo(row.dict()))
    return parse_from_mongo(row.dict())

# ========= Join by Code & Memberships =========
class JoinByCodeRequest(BaseModel):
    join_code: str

class TierMembership(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rating_tier_id: str
    user_id: str
    status: Literal["Active", "Pending", "Rejected"] = "Active"
    created_at: datetime = Field(default_factory=now_utc)

@app.get("/api/rating-tiers/by-code/{code}")
async def get_tier_by_code(code: str):
    code = (code or "").strip().upper()
    tier = await db.rating_tiers.find_one({"join_code": code})
    if not tier:
        raise HTTPException(status_code=404, detail="Join code not found")
    fmt = await db.format_tiers.find_one({"id": tier.get("format_tier_id")})
    league = await db.leagues.find_one({"id": fmt.get("league_id")}) if fmt else None
    out = parse_from_mongo(tier)
    out["league_name"] = league.get("name") if league else None
    return out

@app.post("/api/join-by-code/{user_id}")
async def join_by_code(user_id: str, body: JoinByCodeRequest):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    code = (body.join_code or "").strip().upper()
    tier = await db.rating_tiers.find_one({"join_code": code})
    if not tier:
        raise HTTPException(status_code=404, detail="Invalid join code")
    # rating validation
    rating = user.get("rating_level", 4.0)
    min_r = float(tier.get("min_rating", 3.0))
    max_r = float(tier.get("max_rating", 5.0))
    if rating < min_r or rating > max_r:
        raise HTTPException(status_code=400, detail=f"Your rating {rating} is outside this tier range {min_r}-{max_r}")
    # duplicate check
    existing = await db.tier_memberships.find_one({"rating_tier_id": tier.get("id"), "user_id": user_id, "status": "Active"})
    if existing:
        raise HTTPException(status_code=400, detail="Already joined this tier")
    seat = TierMembership(rating_tier_id=tier.get("id"), user_id=user_id, status="Active")
    await db.tier_memberships.insert_one(prepare_for_mongo(seat.dict()))
    # Publish SSE events for listeners (format and rating scopes)
    try:
        fmt = await db.format_tiers.find_one({"id": tier.get("format_tier_id")})
        await publish_event("tier_memberships", {"rating_tier_id": tier.get("id")})
        await publish_event(f"tier_memberships:rating:{tier.get('id')}", {"rating_tier_id": tier.get("id")})
        if fmt:
            await publish_event(f"tier_memberships:format:{fmt.get('id')}", {"rating_tier_id": tier.get("id")})
    except Exception:
        pass
    return parse_from_mongo(seat.dict())

@app.get("/api/users/{user_id}/joined-tiers")
async def get_joined_tiers(user_id: str, sport_type: Optional[str] = None):
    memberships = await db.tier_memberships.find({"user_id": user_id, "status": "Active"}).to_list(1000)
    out = []
    for m in memberships:
        tier = await db.rating_tiers.find_one({"id": m.get("rating_tier_id")})
        if not tier:
            continue
        fmt = await db.format_tiers.find_one({"id": tier.get("format_tier_id")})
        league = await db.leagues.find_one({"id": fmt.get("league_id")}) if fmt else None
        # Only apply sport_type filter when league has a sport_type stored
        if sport_type and league and league.get("sport_type") and league.get("sport_type") != sport_type:
            continue
        # compute current players in tier
        current_players = await db.tier_memberships.count_documents({"rating_tier_id": tier.get("id"), "status": "Active"})
        out.append({
            "id": tier.get("id"),
            "name": tier.get("name"),
            "min_rating": tier.get("min_rating"),
            "max_rating": tier.get("max_rating"),
            "max_players": tier.get("max_players"),
            "current_players": int(current_players),
            "join_code": tier.get("join_code"),
            "league_name": league.get("name") if league else None,
            "sport_type": league.get("sport_type") if league else None,
            "competition_system": tier.get("competition_system"),
            "joined_at": m.get("created_at"),
            "status": m.get("status")
        })
    return out

@app.get("/api/leagues/{league_id}/format-tiers")
async def list_format_tiers(league_id: str):
    rows = await db.format_tiers.find({"league_id": league_id}).sort("created_at", 1).to_list(1000)
    return [parse_from_mongo(r) for r in rows]


# ========= SSE: Tier membership events =========
subscribers: Dict[str, List[asyncio.Queue]] = {}

async def publish_event(topic: str, data: Dict[str, Any]):
    queues = subscribers.get(topic, [])
    for q in queues:
        await q.put(data)

@app.get("/api/events/tier-memberships")
async def sse_tier_memberships(format_tier_id: Optional[str] = None, rating_tier_id: Optional[str] = None):
    topic = "tier_memberships"
    if format_tier_id:
        topic = f"tier_memberships:format:{format_tier_id}"
    if rating_tier_id:
        topic = f"tier_memberships:rating:{rating_tier_id}"
    q: asyncio.Queue = asyncio.Queue()
    subscribers.setdefault(topic, []).append(q)

    async def event_generator():
        try:
            while True:
                data = await q.get()
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            # cleanup
            subscribers[topic].remove(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/format-tiers")
async def create_format_tier(payload: FormatTierCreate):
    # validate league
    league = await db.leagues.find_one({"id": payload.league_id})
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    row = FormatTier(**payload.dict())
    await db.format_tiers.insert_one(prepare_for_mongo(row.dict()))
    return parse_from_mongo(row.dict())

@app.get("/api/format-tiers/{format_tier_id}/rating-tiers")
async def list_rating_tiers(format_tier_id: str):
    rows = await db.rating_tiers.find({"format_tier_id": format_tier_id}).sort("created_at", 1).to_list(1000)
    out = []
    for r in rows:
        doc = parse_from_mongo(r)
        count = await db.tier_memberships.count_documents({"rating_tier_id": doc.get("id"), "status": "Active"})
        doc["current_players"] = int(count)
        out.append(doc)
    return out

@app.get("/api/rating-tiers/{rating_tier_id}/members")
async def list_tier_members(rating_tier_id: str):
    memberships = await db.tier_memberships.find({"rating_tier_id": rating_tier_id, "status": "Active"}).to_list(1000)
    users = []
    for m in memberships:
        u = await db.users.find_one({"id": m.get("user_id")})
        if not u:
            continue
        uo = parse_from_mongo(u)
        users.append({
            "user_id": uo.get("id"),
            "name": uo.get("name"),
            "email": uo.get("email"),
            "rating_level": uo.get("rating_level", 4.0),
            "lan": uo.get("lan"),
            "photo_url": uo.get("photo_url"),
            "joined_at": m.get("created_at"),
        })
    return users

@app.delete("/api/rating-tiers/{rating_tier_id}/members/{user_id}")
async def remove_tier_member(rating_tier_id: str, user_id: str):
    res = await db.tier_memberships.delete_one({"rating_tier_id": rating_tier_id, "user_id": user_id, "status": "Active"})
    # publish updates
    try:
        tier = await db.rating_tiers.find_one({"id": rating_tier_id})
        fmt = await db.format_tiers.find_one({"id": tier.get("format_tier_id")}) if tier else None
        await publish_event("tier_memberships", {"rating_tier_id": rating_tier_id})
        await publish_event(f"tier_memberships:rating:{rating_tier_id}", {"rating_tier_id": rating_tier_id})
        if fmt:
            await publish_event(f"tier_memberships:format:{fmt.get('id')}", {"rating_tier_id": rating_tier_id})
    except Exception:
        pass
    return {"deleted": res.deleted_count}


@app.post("/api/rating-tiers")
async def create_rating_tier(payload: RatingTierCreate):
    # validate format tier
    fmt = await db.format_tiers.find_one({"id": payload.format_tier_id})
    if not fmt:
        raise HTTPException(status_code=404, detail="Format tier not found")
    # normalize rating bounds to 0.5 steps between 3.0 and 5.0
    def clamp_round(v: float) -> float:
        v = max(3.0, min(5.0, v))
        return round(v * 2) / 2
    min_r = clamp_round(payload.min_rating)
    max_r = clamp_round(payload.max_rating)
    if min_r > max_r:
        raise HTTPException(status_code=400, detail="min_rating must be <= max_rating")
    code = generate_join_code()
    row = RatingTier(
        format_tier_id=payload.format_tier_id,
        name=payload.name,
        min_rating=min_r,
        max_rating=max_r,
        max_players=payload.max_players,
        competition_system=payload.competition_system,
        playoff_spots=(payload.playoff_spots if payload.competition_system == "Team League Format" else None),
        region=payload.region,
        surface=payload.surface,
        join_code=code,
    )
    await db.rating_tiers.insert_one(prepare_for_mongo(row.dict()))
    return parse_from_mongo(row.dict())

@app.patch("/api/rating-tiers/{rating_tier_id}")
async def update_rating_tier(rating_tier_id: str, payload: RatingTierUpdate):
    updates: Dict[str, Any] = {}
    if payload.min_rating is not None:
        updates["min_rating"] = round(max(3.0, min(5.0, payload.min_rating)) * 2) / 2
    if payload.max_rating is not None:
        updates["max_rating"] = round(max(3.0, min(5.0, payload.max_rating)) * 2) / 2
    if updates:
        await db.rating_tiers.update_one({"id": rating_tier_id}, {"$set": updates})
    doc = await db.rating_tiers.find_one({"id": rating_tier_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Rating tier not found")
    return parse_from_mongo(doc)

@app.get("/api/rating-tiers/{rating_tier_id}/player-groups")
async def list_player_groups(rating_tier_id: str):
    rows = await db.player_groups.find({"rating_tier_id": rating_tier_id}).sort("created_at", 1).to_list(1000)
    return [parse_from_mongo(r) for r in rows]

@app.get("/api/rating-tiers/{rating_tier_id}/groups")
async def list_groups_alias(rating_tier_id: str):
    # compatibility alias used by older UI
    return await list_player_groups(rating_tier_id)

@app.post("/api/rating-tiers/{rating_tier_id}/create-groups")
async def create_groups(rating_tier_id: str, body: Dict[str, Any]):
    # support both camelCase and snake_case keys
    group_size = body.get("group_size") or body.get("groupSize") or 12
    custom_names = body.get("custom_names") or body.get("customNames")
    names: List[str]
    if isinstance(custom_names, list) and custom_names:
        names = [str(n) for n in custom_names]
    elif isinstance(custom_names, str) and custom_names.strip():
        names = [n.strip() for n in custom_names.split(',') if n.strip()]
    else:
        # default A, B, C ... based on rough count
        count = max(1, (group_size and 1) or 1)
        names = [f"Group {chr(65+i)}" for i in range(count)]
    created = []
    for nm in names:
        rec = PlayerGroup(rating_tier_id=rating_tier_id, name=nm, group_size=int(group_size))
        await db.player_groups.insert_one(prepare_for_mongo(rec.dict()))
        created.append(parse_from_mongo(rec.dict()))
    return created


@app.get("/api/users/search")
async def search_users(q: str):
    regex = {"$regex": q, "$options": "i"}
    rows = await db.users.find({"$or": [{"name": regex}, {"lan": q}]}).limit(20).to_list(20)
    return {"results": [{"id": r.get("id"), "name": r.get("name"), "lan": r.get("lan"), "email": r.get("email")} for r in rows]}

# ======== Auth & Notifications & Sports ========
class SocialLoginRequest(BaseModel):
    provider: str
    token: str
    email: EmailStr
    name: str
    provider_id: str
    role: Optional[str] = None
    rating_level: Optional[float] = None

@app.post("/api/auth/social-login")
async def social_login(body: SocialLoginRequest):
    doc = await db.users.find_one({"email": body.email})
    if not doc:
        # create a new user with defaults
        lan_code = await generate_unique_lan()
        user = {
            "id": str(uuid.uuid4()),
            "email": body.email,
            "name": body.name,
            "phone": None,
            "rating_level": (body.rating_level if body.rating_level is not None else 4.0),
            "lan": lan_code,
            "role": (body.role or "Player"),
            "sports_preferences": [],
            "created_at": now_utc().isoformat(),
            "auth": {"provider": body.provider, "provider_id": body.provider_id}
        }
        await db.users.insert_one(user)
        # Return clean user data without MongoDB artifacts
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "phone": user["phone"],
            "rating_level": user["rating_level"],
            "lan": user["lan"],
            "role": user["role"],
            "sports_preferences": user["sports_preferences"],
            "created_at": user["created_at"]
        }
    # update name and defaults if missing
    updates = {}
    if not doc.get("lan"):
        updates["lan"] = await generate_unique_lan()
    if doc.get("name") != body.name:
        updates["name"] = body.name
    if not doc.get("role"):
        updates["role"] = "Player"
    if doc.get("sports_preferences") is None:
        updates["sports_preferences"] = []
    # allow role escalation if provided
    if body.role and doc.get("role") != body.role:
        updates["role"] = body.role
    # allow rating_level update if provided
    if body.rating_level is not None and doc.get("rating_level") != body.rating_level:
        updates["rating_level"] = body.rating_level
    if updates:
        await db.users.update_one({"id": doc.get("id")}, {"$set": updates})
        doc.update(updates)
    # Return clean user data without MongoDB artifacts
    return {
        "id": doc.get("id"),
        "email": doc.get("email"),
        "name": doc.get("name"),
        "phone": doc.get("phone"),
        "rating_level": doc.get("rating_level"),
        "lan": doc.get("lan"),
        "role": doc.get("role"),
        "sports_preferences": doc.get("sports_preferences", []),
        "created_at": doc.get("created_at")
    }

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    doc = await db.users.find_one({"id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return parse_from_mongo(doc)

@app.get("/api/users/{user_id}/notifications")
async def get_user_notifications(user_id: str):
    rows = await db.rr_notifications.find({"user_ids": user_id}).sort("created_at", -1).to_list(200)
    return [parse_from_mongo(r) for r in rows]

@app.get("/api/users/{user_id}/leagues")
async def get_manager_leagues(user_id: str, sport_type: Optional[str] = None):
    # Return leagues managed by this user; gracefully handle when none exist
    filt = {"manager_id": user_id}
    if sport_type:
        filt["sport_type"] = sport_type
    try:
        leagues = await db.leagues.find(filt).to_list(1000)
    except Exception:
        leagues = []
    out = []
    for l in leagues:
        out.append({
            "id": l.get("id"),
            "name": l.get("name"),
            "sport_type": l.get("sport_type"),
            "created_at": l.get("created_at"),
        })
    return out

class SportsUpdateRequest(BaseModel):
    sports_preferences: List[str]

@app.patch("/api/users/{user_id}/sports")
async def update_user_sports(user_id: str, body: SportsUpdateRequest):
    await db.users.update_one({"id": user_id}, {"$set": {"sports_preferences": body.sports_preferences}})
    doc = await db.users.find_one({"id": user_id})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return parse_from_mongo(doc)

# ========= Round Robin Models =========
class RRConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier_id: str
    season_name: Optional[str] = None
    season_length: int = 9
    minimize_repeat_partners: bool = True
    track_first_match_badge: bool = False
    track_finished_badge: bool = True
    subgroup_labels: List[str] = Field(default_factory=list)
    subgroup_size: Optional[int] = None
    created_at: datetime = Field(default_factory=now_utc)

class RRSubgroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier_id: str
    label: str
    player_ids: List[str] = Field(default_factory=list)

class RRMatchStatus(str):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    PLAYED = "played"
    DISPUTED = "disputed"

class RRAvailability(BaseModel):
    user_id: str
    # Simple weekly availability strings like "Mon AM", "Wed PM", etc.
    windows: List[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=now_utc)

class RRMatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier_id: str
    week_index: int
    player_ids: List[str] = Field(min_items=4, max_items=4)
    status: str = RRMatchStatus.PROPOSED
    scheduled_at: Optional[str] = None
    scheduled_venue: Optional[str] = None
    proposed_slot_ids: List[str] = Field(default_factory=list)
    toss_winner_user_id: Optional[str] = None
    toss_choice: Optional[str] = None  # e.g., "serve" or "court"
    partner_override: Optional[Dict[str, Any]] = None  # {sets:[[pA,pB],[pC,pD]], confirmations:[user_ids]}
    created_at: datetime = Field(default_factory=now_utc)

class RRSlate(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier_id: str
    week_index: int
    match_ids: List[str] = Field(default_factory=list)

class RRSlot(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    proposed_by_user_id: str
    start: str  # iso
    venue_name: Optional[str] = None
    confirmations: List[str] = Field(default_factory=list)

class RRScoreSet(BaseModel):
    team1_games: int = Field(ge=0, le=7)
    team2_games: int = Field(ge=0, le=7)
    tiebreak_loser_points: Optional[int] = None  # e.g., 8 for 7-6(8)
    winners: List[str] = Field(min_items=2, max_items=2)
    losers: List[str] = Field(min_items=2, max_items=2)

class RRScorecard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    match_id: str
    sets: List[RRScoreSet]
    submitted_by_user_id: str
    approved_by_user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=now_utc)

class RRStandingRow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tier_id: str
    player_id: str
    matches_played: int = 0
    set_points: int = 0
    game_points: int = 0
    pct_game_win: float = 0.0
    updated_at: datetime = Field(default_factory=now_utc)

# ========= RR Admin =========
class RRConfigureRequest(BaseModel):
    season_name: Optional[str] = None
    season_length: Optional[int] = 9
    minimize_repeat_partners: Optional[bool] = True
    track_first_match_badge: Optional[bool] = False
    track_finished_badge: Optional[bool] = True
    subgroup_labels: Optional[List[str]] = None
    subgroup_size: Optional[int] = None

@app.post("/api/rr/tiers/{tier_id}/configure")
async def rr_configure(tier_id: str, body: RRConfigureRequest):
    cfg_doc = await db.rr_configs.find_one({"tier_id": tier_id})
    cfg = RRConfig(
        tier_id=tier_id,
        season_name=body.season_name or ("Season"),
        season_length=body.season_length or 9,
        minimize_repeat_partners=bool(body.minimize_repeat_partners),
        track_first_match_badge=bool(body.track_first_match_badge),
        track_finished_badge=bool(body.track_finished_badge),
        subgroup_labels=body.subgroup_labels or [],
        subgroup_size=body.subgroup_size,
    )
    if cfg_doc:
        await db.rr_configs.update_one({"tier_id": tier_id}, {"$set": prepare_for_mongo(cfg.dict())}, upsert=True)
    else:
        await db.rr_configs.insert_one(prepare_for_mongo(cfg.dict()))
    return {"status": "ok", "config": cfg.dict()}

class RRSubgroupRequest(BaseModel):
    player_ids: List[str]

@app.post("/api/rr/tiers/{tier_id}/subgroups/generate")
async def rr_generate_subgroups(tier_id: str, body: RRSubgroupRequest):
    cfg = await db.rr_configs.find_one({"tier_id": tier_id})
    if not cfg:
        raise HTTPException(status_code=400, detail="Configure tier first")
    labels = cfg.get("subgroup_labels") or []
    size = cfg.get("subgroup_size") or 0
    if not labels or not size:
        raise HTTPException(status_code=400, detail="Subgroup labels and size required")
    players = list(body.player_ids)
    random.shuffle(players)
    # clear old
    await db.rr_subgroups.delete_many({"tier_id": tier_id})
    idx = 0
    for label in labels:
        chunk = players[idx: idx + size]
        idx += size
        rec = RRSubgroup(tier_id=tier_id, label=label, player_ids=chunk)
        await db.rr_subgroups.insert_one(prepare_for_mongo(rec.dict()))
    return {"status": "ok"}

# ========= RR Scheduling =========

def _window_compatible(user_windows: List[str], desired: Optional[str]) -> bool:
    # If no desired window specified, treat as compatible
    if not desired:
        return True
    # Empty user windows means no constraint
    if user_windows is None or len(user_windows) == 0:
        return True
    return desired in set(user_windows)

async def _availability_map(user_ids: List[str]) -> Dict[str, List[str]]:
    avail = await db.rr_availability.find({"user_id": {"$in": user_ids}}).to_list(1000)
    by_user = {a.get("user_id"): (a.get("windows") or []) for a in avail}
    return {uid: by_user.get(uid, []) for uid in user_ids}

class _GreedyState(BaseModel):
    partner_counts: Dict[str, Dict[str, int]] = {}
    opponent_counts: Dict[str, Dict[str, int]] = {}

    def inc_partner(self, a: str, b: str):
        self.partner_counts.setdefault(a, {})[b] = self.partner_counts.get(a, {}).get(b, 0) + 1
        self.partner_counts.setdefault(b, {})[a] = self.partner_counts.get(b, {}).get(a, 0) + 1

    def inc_opponents(self, a: str, b: str):
        self.opponent_counts.setdefault(a, {})[b] = self.opponent_counts.get(a, {}).get(b, 0) + 1
        self.opponent_counts.setdefault(b, {})[a] = self.opponent_counts.get(b, {}).get(a, 0) + 1

    def partner_cost(self, a: str, b: str) -> int:
        return self.partner_counts.get(a, {}).get(b, 0)

    def opponent_cost(self, a: str, b: str) -> int:
        return self.opponent_counts.get(a, {}).get(b, 0)

async def _schedule_week(players: List[str], desired_window: Optional[str], state: _GreedyState, avail_map: Dict[str, List[str]]) -> Dict[str, Any]:
    # Greedy pairing within a week minimizing partner repeats; availability is hard constraint
    pool = players[:]
    random.shuffle(pool)
    matches: List[List[str]] = []
    infeasible_players: List[str] = []

    while len(pool) >= 4:
        # Try to pick a first player with compatible availability
        a = None
        for candidate in pool:
            if _window_compatible(avail_map.get(candidate, []), desired_window):
                a = candidate
                break
        if a is None:
            # none of remaining players match desired window
            infeasible_players.extend(pool)
            break
        pool.remove(a)

        # Choose best partner b for a
        candidates_b = [x for x in pool if _window_compatible(avail_map.get(x, []), desired_window)]
        if len(candidates_b) == 0:
            infeasible_players.append(a)
            continue
        b = min(candidates_b, key=lambda x: state.partner_cost(a, x))
        pool.remove(b)

        # Choose opponents c,d to minimize opponent repeats
        candidates_cd = [x for x in pool if _window_compatible(avail_map.get(x, []), desired_window)]
        if len(candidates_cd) < 2:
            # can’t form a full match; return leftover to infeasible
            infeasible_players.extend([a, b] + candidates_cd)
            break
        # naive: pick two that minimize sum of opponent costs vs a and b
        best_pair = None
        best_cost = 1e9
        for i in range(len(candidates_cd)):
            for j in range(i + 1, len(candidates_cd)):
                c, d = candidates_cd[i], candidates_cd[j]
                cost = state.opponent_cost(a, c) + state.opponent_cost(a, d) + state.opponent_cost(b, c) + state.opponent_cost(b, d)
                if cost < best_cost:
                    best_cost = cost
                    best_pair = (c, d)
        if best_pair is None:
            infeasible_players.extend([a, b])
            break
        c, d = best_pair
        pool.remove(c); pool.remove(d)

        # record match and update counts
        matches.append([a, b, c, d])
        state.inc_partner(a, b)
        state.inc_opponents(a, c); state.inc_opponents(a, d)
        state.inc_opponents(b, c); state.inc_opponents(b, d)

    return {"matches": matches, "infeasible": infeasible_players}

class RRScheduleRequest(BaseModel):
    player_ids: List[str]  # Active players only
    week_windows: Optional[Dict[int, str]] = None  # optional per-week window label

@app.post("/api/rr/tiers/{tier_id}/schedule")
async def rr_schedule_tier(tier_id: str, body: RRScheduleRequest):
    cfg = await db.rr_configs.find_one({"tier_id": tier_id})
    if not cfg:
        raise HTTPException(status_code=400, detail="Configure tier first")
    weeks = int(cfg.get("season_length", 9))
    players = list(body.player_ids)
    if len(players) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 players")

    # Preload availability for all players
    avail_map = await _availability_map(players)

    # Clear old
    await db.rr_slates.delete_many({"tier_id": tier_id})
    await db.rr_matches.delete_many({"tier_id": tier_id})

    # Greedy+backtracking-lite: use weekly greedy with state memory
    state = _GreedyState(partner_counts={}, opponent_counts={})
    conflicts: Dict[int, List[str]] = {}
    feasibility_score = 0

    for w in range(weeks):
        desired_window = None
        if body.week_windows and isinstance(body.week_windows, dict):
            desired_window = body.week_windows.get(w)
        # First greedy pass
        result = await _schedule_week(players, desired_window, state, avail_map)
        # Light local improvement: try swap pairs across leftover players if conflicts exist
        if result["infeasible"]:
            pool = result["infeasible"][:]
            # attempt to find any two swaps that enable a match
            tried = set()
            for i in range(len(pool)):
                for j in range(i+1, len(pool)):
                    a, b = pool[i], pool[j]
                    key = tuple(sorted([a, b]))
                    if key in tried:
                        continue
                    tried.add(key)
                    # try to create a match with any two compatible others from players
                    others = [p for p in players if p not in [a, b] and _window_compatible(avail_map.get(p, []), desired_window)]
                    if len(others) < 2:
                        continue
                    # pick two others that minimize opponent cost
                    best_pair = None
                    best_cost = 1e9
                    for x in range(len(others)):
                        for y in range(x+1, len(others)):
                            c, d = others[x], others[y]
                            cost = state.opponent_cost(a, c) + state.opponent_cost(a, d) + state.opponent_cost(b, c) + state.opponent_cost(b, d)
                            if cost < best_cost:
                                best_cost = cost
                                best_pair = (c, d)
                    if best_pair:
                        # record this extra match
                        c, d = best_pair
                        m = RRMatch(tier_id=tier_id, week_index=w, player_ids=[a, b, c, d])
                        await db.rr_matches.insert_one(prepare_for_mongo(m.dict()))
                        state.inc_partner(a, b)
                        state.inc_opponents(a, c); state.inc_opponents(a, d)
                        state.inc_opponents(b, c); state.inc_opponents(b, d)
        # Query matches we created this week to build slate
        week_matches = await db.rr_matches.find({"tier_id": tier_id, "week_index": w}).to_list(5000)
        match_ids: List[str] = [m.get("id") for m in week_matches]
        slate = RRSlate(tier_id=tier_id, week_index=w, match_ids=match_ids)
        await db.rr_slates.insert_one(prepare_for_mongo(slate.dict()))

        if result["infeasible"]:
            conflicts[w] = result["infeasible"]
        feasibility_score += len([1 for _ in week_matches])

        # compute a simple schedule_quality metric
    schedule_quality = 0
    # Recreate quality by iterating the created matches this run
    all_matches = await db.rr_matches.find({"tier_id": tier_id}).to_list(5000)
    for m in all_matches:
        a, b, c, d = m.get("player_ids", [None]*4)
        if not all([a,b,c,d]):
            continue
        # lower is better, so invert to quality by subtracting from a baseline (we'll just add inverse costs)
        schedule_quality += max(0, 5 - state.partner_cost(a, b))
        schedule_quality += max(0, 5 - (state.opponent_cost(a, c) + state.opponent_cost(a, d)))
        schedule_quality += max(0, 5 - (state.opponent_cost(b, c) + state.opponent_cost(b, d)))

    # Persist schedule meta for UI
    # Convert conflicts dict keys to strings for MongoDB compatibility
    conflicts_str_keys = {str(k): v for k, v in conflicts.items()}
    meta = {
        "id": str(uuid.uuid4()),
        "tier_id": tier_id,
        "feasibility_score": feasibility_score,
        "schedule_quality": schedule_quality,
        "conflicts": conflicts_str_keys,
        "created_at": now_utc().isoformat(),
    }
    await db.rr_schedule_meta.delete_many({"tier_id": tier_id})
    await db.rr_schedule_meta.insert_one(meta)

    return {"status": "ok", "weeks": weeks, "feasibility_score": feasibility_score, "conflicts": conflicts, "schedule_quality": schedule_quality}

@app.get("/api/rr/schedule-meta")
async def rr_schedule_meta(tier_id: str):
    meta = await db.rr_schedule_meta.find_one({"tier_id": tier_id})
    return parse_from_mongo(meta) if meta else {"tier_id": tier_id, "feasibility_score": 0, "schedule_quality": 0, "conflicts": {}}

@app.get("/api/rr/weeks")
async def rr_weeks(player_id: str, tier_id: Optional[str] = None):
    q = {"tier_id": tier_id} if tier_id else {}
    matches = await db.rr_matches.find(q).to_list(5000)
    user_matches = [m for m in matches if player_id in (m.get("player_ids") or [])]
    # attach player objects for avatars
    def attach_players(mdoc):
        ids = mdoc.get("player_ids") or []
        mdoc = parse_from_mongo(mdoc)
        mdoc["player_objs"] = []
        return mdoc, ids
    enriched = []
    for m in user_matches:
        mdoc, ids = attach_players(m)
        players = []
        for pid in ids:
            u = await db.users.find_one({"id": pid})
            if u:
                players.append({"id": u.get("id"), "name": u.get("name"), "photo_url": u.get("photo_url")})
        mdoc["player_objs"] = players
        enriched.append(mdoc)
    by_week: Dict[int, List[Dict[str, Any]]] = {}
    for m in enriched:
        by_week.setdefault(int(m.get("week_index", 0)), []).append(m)
    weeks = [{"week_index": k, "matches": v} for k, v in sorted(by_week.items(), key=lambda x: x[0])]
    return {"weeks": weeks}

# ========= RR Availability =========
class RRAvailabilityRequest(BaseModel):
    user_id: str
    windows: List[str]

@app.get("/api/rr/availability")
async def rr_get_availability(user_id: str):
    doc = await db.rr_availability.find_one({"user_id": user_id})
    if not doc:
        return {"user_id": user_id, "windows": []}
    return parse_from_mongo(doc)

@app.put("/api/rr/availability")
async def rr_put_availability(body: RRAvailabilityRequest):
    rec = RRAvailability(user_id=body.user_id, windows=body.windows, updated_at=now_utc())
    await db.rr_availability.update_one({"user_id": body.user_id}, {"$set": prepare_for_mongo(rec.dict())}, upsert=True)
    return {"status": "ok"}

# ========= RR Propose / Confirm / ICS =========
class ProposeSlotsRequest(BaseModel):
    slots: List[Dict[str, Any]]
    proposed_by_user_id: str

class ConfirmSlotRequest(BaseModel):
    slot_id: str
    user_id: str

@app.post("/api/rr/matches/{match_id}/propose-slots")
async def rr_propose_slots(match_id: str, body: ProposeSlotsRequest):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    created_ids: List[str] = []
    for s in (body.slots or [])[:3]:
        slot = RRSlot(match_id=match_id, proposed_by_user_id=body.proposed_by_user_id, start=s.get("start"), venue_name=s.get("venue_name"))
        await db.rr_slots.insert_one(prepare_for_mongo(slot.dict()))
        created_ids.append(slot.id)
    await db.rr_matches.update_one({"id": match_id}, {"$addToSet": {"proposed_slot_ids": {"$each": created_ids}}})
    return {"created": created_ids}

@app.post("/api/rr/matches/{match_id}/confirm-slot")
async def rr_confirm_slot(match_id: str, body: ConfirmSlotRequest):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    slot = await db.rr_slots.find_one({"id": body.slot_id, "match_id": match_id})
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    await db.rr_slots.update_one({"id": body.slot_id}, {"$addToSet": {"confirmations": body.user_id}})
    slot = await db.rr_slots.find_one({"id": body.slot_id})
    confs = set(slot.get("confirmations") or [])
    # Require all 4 players confirmation to lock
    players = m.get("player_ids") or []
    locked = all(p in confs for p in players)
    if locked:
        await db.rr_matches.update_one({"id": match_id}, {"$set": {"status": RRMatchStatus.CONFIRMED, "scheduled_at": slot.get("start"), "scheduled_venue": slot.get("venue_name")}})
        return {"locked": True, "scheduled_at": slot.get("start"), "venue": slot.get("venue_name")}
    return {"locked": False, "confirmations": list(confs)}

@app.get("/api/rr/matches/{match_id}/ics")
async def rr_match_ics(match_id: str):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m or m.get("status") != RRMatchStatus.CONFIRMED or not m.get("scheduled_at"):
        raise HTTPException(status_code=404, detail="Match not scheduled")
    dt = m.get("scheduled_at")
    if isinstance(dt, str):
        try:
            dtstart = datetime.fromisoformat(dt.replace('Z', '+00:00')).strftime("%Y%m%dT%H%M%SZ")
        except Exception:
            dtstart = now_utc().strftime("%Y%m%dT%H%M%SZ")
    else:
        dtstart = now_utc().strftime("%Y%m%dT%H%M%SZ")
    dtstamp = now_utc().strftime("%Y%m%dT%H%M%SZ")
    summary = f"Round Robin • Week {m.get('week_index')}"
    location = m.get("scheduled_venue") or "TBD"
    ics = f"BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//LeagueAce//RR//EN\nBEGIN:VEVENT\nUID:{m.get('id')}@leagueace\nDTSTAMP:{dtstamp}\nDTSTART:{dtstart}\nSUMMARY:{summary}\nLOCATION:{location}\nEND:VEVENT\nEND:VCALENDAR"
    return {"ics": ics}

# ========= RR Toss & Partner Override =========
class RRTossRequest(BaseModel):
    actor_user_id: str
    choice: Optional[str] = None  # 'serve' or 'court' or None (random choice)

@app.post("/api/rr/matches/{match_id}/toss")
async def rr_toss(match_id: str, body: RRTossRequest):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    if m.get("toss_winner_user_id"):
        raise HTTPException(status_code=400, detail="Toss already done")
    players = m.get("player_ids") or []
    if not players or len(players) != 4:
        raise HTTPException(status_code=400, detail="Match must have 4 players for toss")
    winner = random.choice(players)
    choice = body.choice if body.choice in ("serve", "court") else random.choice(["serve", "court"])
    await db.rr_matches.update_one({"id": match_id}, {"$set": {"toss_winner_user_id": winner, "toss_choice": choice}})
    await rr_audit("toss", match_id, body.actor_user_id, {"winner": winner, "choice": choice})
    await rr_notify(players, f"Toss: {winner} chose {choice}")
    return {"winner_user_id": winner, "choice": choice}

class RRPartnerOverrideRequest(BaseModel):
    actor_user_id: str
    sets: List[List[List[str]]]  # [[[p1,p2],[p3,p4]], ... x3]

@app.post("/api/rr/matches/{match_id}/partner-override")
async def rr_partner_override(match_id: str, body: RRPartnerOverrideRequest):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    players = set(m.get("player_ids") or [])
    if len(players) != 4:
        raise HTTPException(status_code=400, detail="Match must have 4 players")
    # Validate 3 sets and all players involved each set
    if len(body.sets) != 3:
        raise HTTPException(status_code=400, detail="Need 3 sets of override pairs")
    for st in body.sets:
        if len(st) != 2 or any(len(pair) != 2 for pair in st):
            raise HTTPException(status_code=400, detail="Each set requires two pairs of two players")
        flat = set(st[0] + st[1])
        if flat != players:
            raise HTTPException(status_code=400, detail="Each set must include exactly these 4 players")
    override = {"sets": body.sets, "confirmations": [body.actor_user_id]}
    await db.rr_matches.update_one({"id": match_id}, {"$set": {"partner_override": override}})
    await rr_audit("partner_override_propose", match_id, body.actor_user_id, {"sets": body.sets})
    await rr_notify(list(players), "Partner override proposed. All 4 players must confirm.")
    return {"status": "pending_confirmations"}

class RRPartnerOverrideConfirmRequest(BaseModel):
    user_id: str

@app.post("/api/rr/matches/{match_id}/partner-override/confirm")
async def rr_partner_override_confirm(match_id: str, body: RRPartnerOverrideConfirmRequest):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m or not m.get("partner_override"):
        raise HTTPException(status_code=404, detail="No override pending")
    override = m.get("partner_override")
    confs = set(override.get("confirmations") or [])
    if body.user_id in confs:
        return {"status": "already_confirmed"}
    confs.add(body.user_id)
    override["confirmations"] = list(confs)
    await db.rr_matches.update_one({"id": match_id}, {"$set": {"partner_override": override}})
    await rr_audit("partner_override_confirm", match_id, body.user_id, None)
    players = set(m.get("player_ids") or [])
    await rr_notify(list(players), f"Override confirmations: {len(confs)}/4")
    locked = all(p in confs for p in players)
    return {"status": "locked" if locked else "pending", "confirmations": len(confs)}

# ========= RR Let’s Play & Scorecard =========

# Let’s Play partner rotation logic helper
# Given 4 players [p1,p2,p3,p4], we rotate partners across 3 sets:
# - Set 1: (p1,p2) vs (p3,p4)
# - Set 2: (p1,p3) vs (p2,p4)
# - Set 3: (p1,p4) vs (p2,p3)
# If manual override is desired, frontend can submit sets using submit-scorecard with chosen winners/losers;
# a separate confirmation layer could be added later if required.

def rr_default_pairings(players: List[str]) -> List[List[List[str]]]:
    if len(players) != 4:
        raise ValueError("Exactly 4 players required")
    p1, p2, p3, p4 = players
    return [
        [[p1, p2], [p3, p4]],
        [[p1, p3], [p2, p4]],
        [[p1, p4], [p2, p3]],
    ]

class RRSubmitScorecard(BaseModel):
    sets: List[RRScoreSet]
    submitted_by_user_id: str
    use_default_pairings: Optional[bool] = False

class RRApproveRequest(BaseModel):
    approved_by_user_id: str

@app.post("/api/rr/matches/{match_id}/submit-scorecard")
async def rr_submit_scorecard(match_id: str, body: RRSubmitScorecard):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
    players = m.get("player_ids") or []
    if body.use_default_pairings:
        # no-op here; frontend can still submit scores reflecting default pairings
        _ = rr_default_pairings(players)
    if len(body.sets) != 3:
        raise HTTPException(status_code=400, detail="Exactly 3 sets required")
    # Validate winners/losers disjoint and size 2 each
    for s in body.sets:
        a = set(s.winners); b = set(s.losers)
        if len(a) != 2 or len(b) != 2 or (a & b):
            raise HTTPException(status_code=400, detail="Invalid set participants")
        if s.team1_games == s.team2_games:
            raise HTTPException(status_code=400, detail="Set games cannot tie without tiebreak representation")
    sc = RRScorecard(match_id=match_id, sets=body.sets, submitted_by_user_id=body.submitted_by_user_id)
    await db.rr_scorecards.insert_one(prepare_for_mongo(sc.dict()))
    return {"scorecard_id": sc.id, "status": "pending_approval"}

@app.post("/api/rr/matches/{match_id}/approve-scorecard")
async def rr_approve_scorecard(match_id: str, body: RRApproveRequest):
    sc = await db.rr_scorecards.find_one({"match_id": match_id}, sort=[["created_at", -1]])
    if not sc:
        raise HTTPException(status_code=404, detail="No scorecard to approve")
    await db.rr_scorecards.update_one({"id": sc.get("id")}, {"$set": {"approved_by_user_id": body.approved_by_user_id}})
    await db.rr_matches.update_one({"id": match_id}, {"$set": {"status": RRMatchStatus.PLAYED}})
    # Snapshot standings after approval for trend analysis
    await rr_recalc_standings(tier_id=sc.get("tier_id") if sc.get("tier_id") else None, match_id=match_id)
    await db.rr_snapshots.insert_one({
        "id": str(uuid.uuid4()),
        "tier_id": (await db.rr_matches.find_one({"id": match_id})).get("tier_id"),
        "created_at": now_utc().isoformat(),
        "rows": await db.rr_standings.find({"tier_id": (await db.rr_matches.find_one({"id": match_id})).get("tier_id")}).to_list(1000)
    })
    return {"status": "approved"}

async def rr_recalc_standings(tier_id: Optional[str], match_id: Optional[str] = None):
    # Recompute from all approved scorecards for the tier or by joining match->tier
    if not tier_id:
        m = await db.rr_matches.find_one({"id": match_id})
        if not m:
            return
        tier_id = m.get("tier_id")
    # Aggregate precise stats per player
    cards = await db.rr_scorecards.find({"approved_by_user_id": {"$ne": None}}).to_list(5000)
    stats: Dict[str, Dict[str, Any]] = {}
    for sc in cards:
        mid = sc.get("match_id")
        mm = await db.rr_matches.find_one({"id": mid})
        if not mm or mm.get("tier_id") != tier_id:
            continue
        participants = mm.get("player_ids") or []
        for pid in participants:
            stats.setdefault(pid, {"matches": 0, "set_pts": 0, "games_won": 0, "games_lost": 0})
        # count one match per participant
        for pid in participants:
            stats[pid]["matches"] += 1
        for s in sc.get("sets") or []:
            winners = s.get("winners") or []
            losers = s.get("losers") or []
            t1 = int(s.get("team1_games", 0)); t2 = int(s.get("team2_games", 0))
            # Determine which side won to allocate game counts
            if t1 > t2:
                win_games, lose_games = t1, t2
            else:
                win_games, lose_games = t2, t1
            # Ensure all winners and losers are in stats (safety check)
            for pid in winners + losers:
                if pid not in stats:
                    stats[pid] = {"matches": 0, "set_pts": 0, "games_won": 0, "games_lost": 0}
            for pid in winners:
                stats[pid]["set_pts"] += 1
                stats[pid]["games_won"] += win_games
                stats[pid]["games_lost"] += lose_games
            for pid in losers:
                stats[pid]["games_won"] += lose_games
                stats[pid]["games_lost"] += win_games
    # Upsert standings
    await db.rr_standings.delete_many({"tier_id": tier_id})
    for pid, vals in stats.items():
        total = vals["games_won"] + vals["games_lost"]
        pct = (vals["games_won"] / total) if total > 0 else 0.0
        row = RRStandingRow(
            tier_id=tier_id,
            player_id=pid,
            matches_played=vals["matches"],
            set_points=vals["set_pts"],
            game_points=vals["games_won"],
            pct_game_win=round(pct, 4),
            updated_at=now_utc(),
        )
        await db.rr_standings.insert_one(prepare_for_mongo(row.dict()))

@app.get("/api/rr/standings")
async def rr_get_standings(tier_id: str):
    rows = await db.rr_standings.find({"tier_id": tier_id}).to_list(1000)
    # attach user info for avatars
    for r in rows:
        u = await db.users.find_one({"id": r.get("player_id")})
        if u:
            r["user"] = {
                "id": u.get("id"),
                "name": u.get("name"),
                "photo_url": u.get("photo_url"),
                "lan": u.get("lan"),
                "rating_level": u.get("rating_level"),
            }
    # compute badges
    first_match_ids = set()
    finished_all_ids = set()
    matches = await db.rr_matches.find({"tier_id": tier_id}).to_list(5000)
    for r in rows:
        if int(r.get("matches_played", 0)) >= 1:
            first_match_ids.add(r.get("player_id"))
    weeks = set([int(m.get("week_index", 0)) for m in matches])
    total_weeks = len(weeks) if weeks else 0
    for r in rows:
        if total_weeks > 0 and int(r.get("matches_played", 0)) >= total_weeks:
            finished_all_ids.add(r.get("player_id"))

    # trend arrows: compare with last snapshot
    last_snapshot = await db.rr_snapshots.find({"tier_id": tier_id}).sort("created_at", -1).limit(1).to_list(1)
    prev = last_snapshot[0] if last_snapshot else None
    prev_ranks = {}
    if prev:
        # build rank map by player_id from previous snapshot rows
        prev_rows = prev.get("rows") or []
        # sort to rank by set_points then pct_game_win
        def _rank_key(r):
            return (-int(r.get("set_points", 0)), -float(r.get("pct_game_win", 0.0)))
        prev_sorted = sorted(prev_rows, key=_rank_key)
        for idx, r in enumerate(prev_sorted):
            prev_ranks[r.get("player_id")] = idx + 1

    # current sort
    def _key(r):
        return (-int(r.get("set_points", 0)), -float(r.get("pct_game_win", 0.0)))
    rows_sorted = sorted(rows, key=_key)

    out = []
    for idx, r in enumerate(rows_sorted):
        row = parse_from_mongo(r)
        pid = row.get("player_id")
        row["badges"] = []
        if pid in first_match_ids:
            row["badges"].append("first_match")
        if pid in finished_all_ids:
            row["badges"].append("finished_all")
        # trend
        if prev_ranks:
            prev_pos = prev_ranks.get(pid)
            if prev_pos is not None:
                delta = prev_pos - (idx + 1)
                row["trend"] = delta  # positive = up, negative = down
        out.append(row)

    return {"rows": out, "top8": out[:8]}

# ========= Health =========
@app.get("/api/health")
async def health():
    return {"status": "ok", "time": now_utc().isoformat()}

# ========= Shutdown =========
@app.on_event("shutdown")
async def shutdown_event():
    client.close()