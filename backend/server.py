import os
import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient

# ========= FastAPI app =========
app = FastAPI(title="LeagueAce API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ingress handles real origin; keep permissive for internal routing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= DB =========
MONGO_URL = os.environ.get("MONGO_URL")
if not MONGO_URL:
    raise RuntimeError("MONGO_URL not set in backend/.env")

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
    created_at: datetime = Field(default_factory=now_utc)

class UserProfileCreate(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    rating_level: float = 4.0
    lan: Optional[str] = None

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
    user = UserProfile(**data)
    await db.users.insert_one(prepare_for_mongo(user.dict()))
    return user

@app.patch("/api/users/{user_id}", response_model=UserProfile)
async def update_user(user_id: str, payload: UserProfileUpdate):
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

@app.get("/api/users/search")
async def search_users(q: str):
    regex = {"$regex": q, "$options": "i"}
    rows = await db.users.find({"$or": [{"name": regex}, {"lan": q}]}).limit(20).to_list(20)
    return {"results": [{"id": r.get("id"), "name": r.get("name"), "lan": r.get("lan"), "email": r.get("email")} for r in rows]}

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
class RRScheduleRequest(BaseModel):
    player_ids: List[str]  # Active players only

@app.post("/api/rr/tiers/{tier_id}/schedule")
async def rr_schedule_tier(tier_id: str, body: RRScheduleRequest):
    cfg = await db.rr_configs.find_one({"tier_id": tier_id})
    if not cfg:
        raise HTTPException(status_code=400, detail="Configure tier first")
    weeks = int(cfg.get("season_length", 9))
    players = list(body.player_ids)
    if len(players) < 4:
        raise HTTPException(status_code=400, detail="Need at least 4 players")
    # Clear old
    await db.rr_slates.delete_many({"tier_id": tier_id})
    await db.rr_matches.delete_many({"tier_id": tier_id})

    # Very simple greedy: for each week, shuffle and group into 4s
    for w in range(weeks):
        week_players = players[:]
        random.shuffle(week_players)
        match_ids: List[str] = []
        for i in range(0, len(week_players) - (len(week_players) % 4), 4):
            group = week_players[i: i + 4]
            m = RRMatch(tier_id=tier_id, week_index=w, player_ids=group)
            await db.rr_matches.insert_one(prepare_for_mongo(m.dict()))
            match_ids.append(m.id)
        slate = RRSlate(tier_id=tier_id, week_index=w, match_ids=match_ids)
        await db.rr_slates.insert_one(prepare_for_mongo(slate.dict()))
    return {"status": "ok", "weeks": weeks}

@app.get("/api/rr/weeks")
async def rr_weeks(player_id: str, tier_id: Optional[str] = None):
    q = {"tier_id": tier_id} if tier_id else {}
    matches = await db.rr_matches.find(q).to_list(5000)
    user_matches = [m for m in matches if player_id in (m.get("player_ids") or [])]
    by_week: Dict[int, List[Dict[str, Any]]] = {}
    for m in user_matches:
        by_week.setdefault(int(m.get("week_index", 0)), []).append(parse_from_mongo(m))
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

# ========= RR Let’s Play & Scorecard =========
class RRSubmitScorecard(BaseModel):
    sets: List[RRScoreSet]
    submitted_by_user_id: str

class RRApproveRequest(BaseModel):
    approved_by_user_id: str

@app.post("/api/rr/matches/{match_id}/submit-scorecard")
async def rr_submit_scorecard(match_id: str, body: RRSubmitScorecard):
    m = await db.rr_matches.find_one({"id": match_id})
    if not m:
        raise HTTPException(status_code=404, detail="Match not found")
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
    sc = await db.rr_scorecards.find_one({"match_id": match_id}, sort=[("created_at", -1)])
    if not sc:
        raise HTTPException(status_code=404, detail="No scorecard to approve")
    await db.rr_scorecards.update_one({"id": sc.get("id")}, {"$set": {"approved_by_user_id": body.approved_by_user_id}})
    await db.rr_matches.update_one({"id": match_id}, {"$set": {"status": RRMatchStatus.PLAYED}})
    await rr_recalc_standings(tier_id=sc.get("tier_id") if sc.get("tier_id") else None, match_id=match_id)
    return {"status": "approved"}

async def rr_recalc_standings(tier_id: Optional[str], match_id: Optional[str] = None):
    # Recompute from all approved scorecards for the tier or by joining match->tier
    if not tier_id:
        m = await db.rr_matches.find_one({"id": match_id})
        if not m:
            return
        tier_id = m.get("tier_id")
    # Aggregate
    cards = await db.rr_scorecards.find({"approved_by_user_id": {"$ne": None}}).to_list(5000)
    points: Dict[str, Dict[str, Any]] = {}
    for sc in cards:
        mid = sc.get("match_id")
        mm = await db.rr_matches.find_one({"id": mid})
        if not mm or mm.get("tier_id") != tier_id:
            continue
        for s in sc.get("sets") or []:
            winners = s.get("winners") or []
            losers = s.get("losers") or []
            t1 = int(s.get("team1_games", 0)); t2 = int(s.get("team2_games", 0))
            wp = 10 * max(t1, t2); lp = 10 * min(t1, t2)
            for pid in winners:
                row = points.setdefault(pid, {"matches": 0, "set_pts": 0, "game_pts": 0})
                row["set_pts"] += 1
                row["game_pts"] += wp
            for pid in losers:
                row = points.setdefault(pid, {"matches": 0, "set_pts": 0, "game_pts": 0})
                row["game_pts"] += lp
        # Count match played for each participant
        for pid in mm.get("player_ids") or []:
            row = points.setdefault(pid, {"matches": 0, "set_pts": 0, "game_pts": 0})
            row["matches"] += 1
    # Upsert standings
    await db.rr_standings.delete_many({"tier_id": tier_id})
    for pid, vals in points.items():
        total_games = vals["game_pts"]
        # % game win approximated via normalized over max possible; we use ratio winners/(winners+losers)
        # Here without per-set breakdown, we compute as share of won-game points; simplistic approximation
        pct = 0.0  # can be refined when storing per-set games by player side
        row = RRStandingRow(tier_id=tier_id, player_id=pid, matches_played=vals["matches"], set_points=vals["set_pts"], game_points=vals["game_pts"], pct_game_win=pct, updated_at=now_utc())
        await db.rr_standings.insert_one(prepare_for_mongo(row.dict()))

@app.get("/api/rr/standings")
async def rr_get_standings(tier_id: str):
    rows = await db.rr_standings.find({"tier_id": tier_id}).to_list(1000)
    # Sort by set_points desc, then pct_game_win desc
    rows_sorted = sorted(rows, key=lambda r: (-int(r.get("set_points", 0)), -float(r.get("pct_game_win", 0.0))))
    out = [parse_from_mongo(r) for r in rows_sorted]
    return {"rows": out, "top8": out[:8]}

# ========= Health =========
@app.get("/api/health")
async def health():
    return {"status": "ok", "time": now_utc().isoformat()}

# ========= Shutdown =========
@app.on_event("shutdown")
async def shutdown_event():
    client.close()