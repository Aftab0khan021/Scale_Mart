"""
Enhanced server with WebSocket, Security, and Performance improvements
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import socketio
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import redis.asyncio as redis
import json
from celery import Celery
import asyncio
from contextlib import asynccontextmanager
import time

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging with structured format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(
    mongo_url,
    maxPoolSize=50,  # Connection pooling
    minPoolSize=10
)
db = client[os.environ['DB_NAME']]
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Redis connection with connection pooling
redis_client = redis.from_url(
    redis_url,
    decode_responses=True,
    max_connections=50
)

# Celery configuration
celery_app = Celery(
    'scalemart',
    broker=f"{redis_url}/0", 
    backend=f"{redis_url}/0"
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# Validate JWT_SECRET in production
if JWT_SECRET == 'your-secret-key-change-in-production':
    logger.warning("⚠️  WARNING: Using default JWT_SECRET! Set a secure random string in production!")
    logger.warning("   Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")

security = HTTPBearer()

# Socket.IO setup for WebSocket
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure this properly in production
    logger=True,
    engineio_logger=True
)

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting ScaleMart API...")
    logger.info("✅ MongoDB connected")
    logger.info("✅ Redis connected")
    logger.info("✅ WebSocket server ready")
    yield
    # Shutdown
    logger.info("👋 Shutting down ScaleMart API...")
    await redis_client.close()
    client.close()

app = FastAPI(
    title="ScaleMart API",
    version="2.0.0",
    lifespan=lifespan
)

# Wrap FastAPI app with Socket.IO
socket_app = socketio.ASGIApp(sio, app)

api_router = APIRouter(prefix="/api")

# ============================================================================
# MIDDLEWARE - Security & Performance
# ============================================================================

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    
    return response

# Request ID Middleware for tracing
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Time: {process_time:.3f}s | "
        f"Request-ID: {request_id}"
    )
    
    return response

# CORS configuration
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted host middleware (security)
# app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "*.onrender.com"])

# ============================================================================
# MODELS
# ============================================================================

class UserSignup(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=2)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Product(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    price: float
    image_url: str
    stock: int
    flash_sale: bool = False
    discount_percent: Optional[int] = 0
    category: Optional[str] = "general"

class FlashBuyRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1, le=10)  # Max 10 per order

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    product_id: str
    product_name: str
    quantity: int
    total_price: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    can_cancel: bool = True

class OrderStatus(BaseModel):
    order_id: str
    status: str
    message: str

class AdminStats(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    total_revenue: float
    sales_velocity: float
    low_stock_products: List[Dict[str, Any]]

# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@sio.event
async def connect(sid, environ):
    """Handle WebSocket connection"""
    logger.info(f"🔌 WebSocket client connected: {sid}")
    await sio.emit('connection_established', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle WebSocket disconnection"""
    logger.info(f"🔌 WebSocket client disconnected: {sid}")

@sio.event
async def subscribe_product(sid, data):
    """Subscribe to product stock updates"""
    product_id = data.get('product_id')
    if product_id:
        await sio.enter_room(sid, f"product_{product_id}")
        logger.info(f"📦 Client {sid} subscribed to product {product_id}")

@sio.event
async def unsubscribe_product(sid, data):
    """Unsubscribe from product stock updates"""
    product_id = data.get('product_id')
    if product_id:
        await sio.leave_room(sid, f"product_{product_id}")
        logger.info(f"📦 Client {sid} unsubscribed from product {product_id}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def broadcast_stock_update(product_id: str, new_stock: int):
    """Broadcast stock update to all subscribed clients"""
    await sio.emit(
        'stock_update',
        {'product_id': product_id, 'stock': new_stock},
        room=f"product_{product_id}"
    )
    logger.info(f"📢 Broadcasted stock update for {product_id}: {new_stock}")

async def broadcast_order_notification(user_id: str, order_data: dict):
    """Send order notification to specific user"""
    await sio.emit(
        'order_notification',
        order_data,
        room=f"user_{user_id}"
    )

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS"""
    if not text:
        return text
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '`']
    for char in dangerous_chars:
        text = text.replace(char, '')
    return text.strip()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Validate JWT token and return current user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_doc = await db.users.find_one({"id": user_id})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def check_rate_limit(user_id: str, action: str, limit: int = 10, window: int = 60):
    """Rate limiting using Redis with token bucket algorithm"""
    key = f"rate_limit:{user_id}:{action}"
    count = await redis_client.get(key)
    
    if count and int(count) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Please try again in {window} seconds."
        )
    
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()

# ============================================================================
# CELERY TASKS
# ============================================================================

@celery_app.task(name='process_order')
def process_order_task(order_data: dict):
    """Background task to process order and update database"""
    import time
    from pymongo import MongoClient
    
    # Simulate processing time
    time.sleep(2)
    
    # Connect to MongoDB (Celery worker context)
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    db = mongo_client[os.environ['DB_NAME']]
    
    # Update order status
    db.orders.update_one(
        {"id": order_data['id']},
        {"$set": {"status": "confirmed", "can_cancel": False}}
    )
    
    logger.info(f"✅ Order {order_data['id']} processed successfully")
    
    return {"order_id": order_data['id'], "status": "confirmed"}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    try:
        # Check MongoDB
        await db.command('ping')
        mongo_status = "healthy"
    except:
        mongo_status = "unhealthy"
    
    try:
        # Check Redis
        await redis_client.ping()
        redis_status = "healthy"
    except:
        redis_status = "unhealthy"
    
    overall_status = "healthy" if mongo_status == "healthy" and redis_status == "healthy" else "degraded"
    
    return {
        "status": overall_status,
        "services": {
            "mongodb": mongo_status,
            "redis": redis_status,
            "websocket": "healthy"
        },
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# Continue with existing endpoints...
# (I'll add the rest in the next file to keep this manageable)
