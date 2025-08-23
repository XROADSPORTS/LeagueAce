import os
import uuid
import random
import string
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

app = FastAPI()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

# Database setup (MongoDB)
MONGO_URL = os.environ.get("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client["leagueace"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions

def now_utc() -> datetime:
    return datetime.utcnow()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ======== Models ========
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
    rating_level: Optional[float] = 4.0
    lan: Optional[str] = None
    role: Optional[str] = "Player"
    password: Optional[str] = None
    confirm_password: Optional[str] = None

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    lan: Optional[str] = None

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

# ======== Helpers ========
async def generate_unique_lan() -> str:
    while True:
        code = 'LAN-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        existing = await db.users.find_one({"lan": code})
        if not existing:
            return code

# NOTE: parse_from_mongo and prepare_for_mongo existed earlier; preserving behavior

def parse_from_mongo(doc: Dict[str, Any]):
    if not doc:
        return doc
    d = dict(doc)
    d.pop("_id", None)
    return d

def prepare_for_mongo(doc: Dict[str, Any]):
    d = dict(doc)
    d.pop("_id", None)
    return d

# ========= Users =========
@app.post("/api/users", response_model=UserProfile)
async def create_user(user_data: UserProfileCreate):
    # Prevent duplicate accounts by email
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists. Please sign in instead.")

    # Generate LAN and defaults
    lan_code = user_data.lan or await generate_unique_lan()
    role = user_data.role or "Player"

    # Validate password for form signup
    password_hash = None
    if user_data.password or user_data.confirm_password:
        if not user_data.password or not user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Password and confirm password are required")
        if user_data.password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        if len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters long")
        password_hash = get_password_hash(user_data.password)

    doc = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "name": user_data.name,
        "phone": user_data.phone,
        # Rating level optional for managers; default to 4.0 if not provided
        "rating_level": (user_data.rating_level if user_data.rating_level is not None else 4.0),
        "lan": lan_code,
        "role": role,
        "sports_preferences": [],
        "created_at": now_utc().isoformat(),
    }
    if password_hash:
        doc["auth"] = {"provider": "Email", "password_hash": password_hash}

    await db.users.insert_one(doc)

    # Return sanitized response
    return UserProfile(**{
        "id": doc["id"],
        "email": doc["email"],
        "name": doc["name"],
        "phone": doc.get("phone"),
        "rating_level": doc.get("rating_level", 4.0),
        "lan": doc.get("lan"),
        "role": doc.get("role", "Player"),
        "created_at": datetime.fromisoformat(doc["created_at"]) if isinstance(doc.get("created_at"), str) else doc.get("created_at")
    })

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
    save_path = os.path.join(UPLOAD_DIR, fname)
    with open(save_path, "wb") as f:
        f.write(await file.read())
    url = f"/api/uploads/{fname}"
    await db.users.update_one({"id": user_id}, {"$set": {"photo_url": url}})
    return {"url": url}

# ========= Auth =========
class SocialLoginRequest(BaseModel):
    provider: str
    token: str
    email: EmailStr
    name: str
    provider_id: str
    role: Optional[str] = None
    rating_level: Optional[float] = None

@app.post("/api/auth/login-email")
async def login_email(req: EmailLoginRequest):
    doc = await db.users.find_one({"email": req.email})
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    auth = doc.get("auth") or {}
    password_hash = auth.get("password_hash")
    if not password_hash:
        raise HTTPException(status_code=400, detail="Password not set for this account. Use social sign-in or contact support.")
    if not verify_password(req.password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Return clean user
    return {
        "id": doc.get("id"),
        "email": doc.get("email"),
        "name": doc.get("name"),
        "phone": doc.get("phone"),
        "rating_level": doc.get("rating_level"),
        "lan": doc.get("lan"),
        "role": doc.get("role"),
        "sports_preferences": doc.get("sports_preferences", []),
        "created_at": doc.get("created_at"),
        "photo_url": doc.get("photo_url")
    }

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
    # update defaults if missing and allow role escalation
    updates: Dict[str, Any] = {}
    if not doc.get("lan"):
        updates["lan"] = await generate_unique_lan()
    if doc.get("name") != body.name:
        updates["name"] = body.name
    if not doc.get("role"):
        updates["role"] = "Player"
    if body.role and doc.get("role") != body.role:
        updates["role"] = body.role
    if body.rating_level is not None and doc.get("rating_level") != body.rating_level:
        updates["rating_level"] = body.rating_level
    if updates:
        await db.users.update_one({"id": doc.get("id")}, {"$set": updates})
        doc.update(updates)
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

# ========= Other endpoints (leagues, rating tiers, rr, etc.) =========
# ... The remainder of server.py remains unchanged ...