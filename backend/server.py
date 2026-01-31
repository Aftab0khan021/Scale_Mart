from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import redis.asyncio as redis
import json
from celery import Celery
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379')

# Redis connection
redis_client = redis.from_url(redis_url, decode_responses=True)

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
    logger = logging.getLogger(__name__)
    logger.warning("⚠️  WARNING: Using default JWT_SECRET! Set a secure random string in production!")
    logger.warning("   Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")

security = HTTPBearer()

app = FastAPI(title="ScaleMart API")
api_router = APIRouter(prefix="/api")

# Models
class UserSignup(BaseModel):
    email: EmailStr
    password: str
    name: str

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

class FlashBuyRequest(BaseModel):
    product_id: str
    quantity: int = 1

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_email: str
    product_id: str
    product_name: str
    quantity: int
    total_price: float
    status: str  # pending, processing, confirmed, failed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OrderStatus(BaseModel):
    order_id: str
    status: str
    message: str

class AdminStats(BaseModel):
    total_orders: int
    pending_orders: int
    total_revenue: float
    sales_velocity: float
    queue_size: int
    products_low_stock: List[dict]

class RestockRequest(BaseModel):
    product_id: str
    quantity: int

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_jwt_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_jwt_token(token)
    user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return User(**user)

# Rate Limiting
async def check_rate_limit(user_id: str, action: str, limit: int = 10, window: int = 60):
    key = f"rate_limit:{user_id}:{action}"
    count = await redis_client.get(key)
    
    if count and int(count) >= limit:
        raise HTTPException(status_code=429, detail="Too many requests. Please try again later.")
    
    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, window)
    await pipe.execute()

# Celery Task for Order Processing
@celery_app.task(name='process_order')
def process_order_task(order_data: dict):
    """Background task to process order and update database"""
    import time
    from pymongo import MongoClient
    
    # Simulate processing time
    time.sleep(2)
    
    # Update order status in MongoDB
    mongo_client = MongoClient(os.environ['MONGO_URL'])
    db = mongo_client[os.environ['DB_NAME']]
    
    order_data['status'] = 'confirmed'
    order_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    db.orders.update_one(
        {"id": order_data['id']},
        {"$set": {"status": "confirmed", "updated_at": order_data['updated_at']}}
    )
    
    return {"order_id": order_data['id'], "status": "confirmed"}

# Initialize Products in Redis (seed data)
async def initialize_products():
    products = [
        {
            "id": "prod_1",
            "name": "Premium Wireless Headphones",
            "description": "High-quality noise-cancelling headphones",
            "price": 299.99,
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=500",
            "stock": 50,
            "flash_sale": True,
            "discount_percent": 40
        },
        {
            "id": "prod_2",
            "name": "Smart Fitness Watch",
            "description": "Track your health and fitness goals",
            "price": 199.99,
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=500",
            "stock": 30,
            "flash_sale": True,
            "discount_percent": 50
        },
        {
            "id": "prod_3",
            "name": "4K Action Camera",
            "description": "Capture your adventures in stunning detail",
            "price": 399.99,
            "image_url": "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=500",
            "stock": 20,
            "flash_sale": True,
            "discount_percent": 35
        },
        {
            "id": "prod_4",
            "name": "Mechanical Gaming Keyboard",
            "description": "RGB backlit with tactile switches",
            "price": 149.99,
            "image_url": "https://images.unsplash.com/photo-1595225476474-87563907a212?w=500",
            "stock": 100,
            "flash_sale": False,
            "discount_percent": 0
        },
        {
            "id": "prod_5",
            "name": "Portable Bluetooth Speaker",
            "description": "Waterproof with 24-hour battery life",
            "price": 79.99,
            "image_url": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=500",
            "stock": 75,
            "flash_sale": False,
            "discount_percent": 0
        },
        {
            "id": "prod_6",
            "name": "USB-C Charging Hub",
            "description": "6-in-1 multiport adapter",
            "price": 49.99,
            "image_url": "https://images.unsplash.com/photo-1625948515291-69613efd103f?w=500",
            "stock": 150,
            "flash_sale": False,
            "discount_percent": 0
        }
    ]
    
    for product in products:
        # Store product in Redis
        await redis_client.set(f"product:{product['id']}", json.dumps(product))
        # Store stock separately for atomic operations
        await redis_client.set(f"stock:{product['id']}", product['stock'])

# API Routes
@api_router.post("/auth/signup")
async def signup(user_data: UserSignup):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    token = create_jwt_token(user.id, user.email)
    
    return {
        "token": token,
        "user": {"id": user.id, "email": user.email, "name": user.name}
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user['password']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_jwt_token(user['id'], user['email'])
    
    return {
        "token": token,
        "user": {"id": user['id'], "email": user['email'], "name": user['name']}
    }

@api_router.get("/products", response_model=List[Product])
async def get_products():
    """Get all products from Redis cache"""
    products = []
    
    # Get all product keys
    keys = await redis_client.keys("product:*")
    
    if not keys:
        # Initialize if empty
        await initialize_products()
        keys = await redis_client.keys("product:*")
    
    for key in keys:
        product_data = await redis_client.get(key)
        if product_data:
            product = json.loads(product_data)
            # Get real-time stock from Redis
            stock = await redis_client.get(f"stock:{product['id']}")
            product['stock'] = int(stock) if stock else 0
            products.append(product)
    
    return products

@api_router.post("/flash-buy", response_model=OrderStatus)
async def flash_buy(
    request: FlashBuyRequest,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """Flash buy with atomic inventory locking"""
    # Rate limiting - max 10 requests per minute per user
    await check_rate_limit(current_user.id, "flash_buy", limit=10, window=60)
    
    # Atomic decrement in Redis
    stock_key = f"stock:{request.product_id}"
    
    # Check if product exists
    product_data = await redis_client.get(f"product:{request.product_id}")
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = json.loads(product_data)
    
    # Atomic decrement
    new_stock = await redis_client.decr(stock_key, request.quantity)
    
    if new_stock < 0:
        # Rollback - increment back
        await redis_client.incr(stock_key, request.quantity)
        raise HTTPException(status_code=400, detail="Out of stock!")
    
    # Calculate price
    price = product['price']
    if product.get('flash_sale') and product.get('discount_percent'):
        price = price * (1 - product['discount_percent'] / 100)
    
    total_price = price * request.quantity
    
    # Create order
    order = Order(
        user_id=current_user.id,
        user_email=current_user.email,
        product_id=request.product_id,
        product_name=product['name'],
        quantity=request.quantity,
        total_price=round(total_price, 2),
        status="pending"
    )
    
    order_dict = order.model_dump()
    order_dict['created_at'] = order_dict['created_at'].isoformat()
    order_dict['updated_at'] = order_dict['updated_at'].isoformat()
    
    await db.orders.insert_one(order_dict)
    
    # Queue order for async processing
    process_order_task.delay(order_dict)
    
    return OrderStatus(
        order_id=order.id,
        status="pending",
        message="Order queued! Processing in background."
    )

@api_router.get("/orders", response_model=List[Order])
async def get_user_orders(current_user: User = Depends(get_current_user)):
    """Get user's order history"""
    orders = await db.orders.find({"user_id": current_user.id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for order in orders:
        if isinstance(order['created_at'], str):
            order['created_at'] = datetime.fromisoformat(order['created_at'])
        if isinstance(order['updated_at'], str):
            order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return orders

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order_status(order_id: str, current_user: User = Depends(get_current_user)):
    """Get specific order status"""
    order = await db.orders.find_one({"id": order_id, "user_id": current_user.id}, {"_id": 0})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if isinstance(order['created_at'], str):
        order['created_at'] = datetime.fromisoformat(order['created_at'])
    if isinstance(order['updated_at'], str):
        order['updated_at'] = datetime.fromisoformat(order['updated_at'])
    
    return Order(**order)

@api_router.get("/admin/stats", response_model=AdminStats)
async def get_admin_stats(current_user: User = Depends(get_current_user)):
    """Get admin dashboard statistics"""
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Pending orders
    pending_orders = await db.orders.count_documents({"status": "pending"})
    
    # Total revenue (confirmed orders only)
    pipeline = [
        {"$match": {"status": "confirmed"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
    ]
    revenue_result = await db.orders.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]['total'] if revenue_result else 0
    
    # Sales velocity (orders in last minute)
    one_minute_ago = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    recent_orders = await db.orders.count_documents({
        "created_at": {"$gte": one_minute_ago}
    })
    
    # Queue size (Celery inspection)
    queue_size = pending_orders  # Simplified - in production, inspect Celery queue
    
    # Low stock products
    products_low_stock = []
    keys = await redis_client.keys("product:*")
    for key in keys:
        product_data = await redis_client.get(key)
        if product_data:
            product = json.loads(product_data)
            stock = await redis_client.get(f"stock:{product['id']}")
            stock_int = int(stock) if stock else 0
            if stock_int < 10:
                products_low_stock.append({
                    "id": product['id'],
                    "name": product['name'],
                    "stock": stock_int
                })
    
    return AdminStats(
        total_orders=total_orders,
        pending_orders=pending_orders,
        total_revenue=round(total_revenue, 2),
        sales_velocity=recent_orders,
        queue_size=queue_size,
        products_low_stock=products_low_stock
    )

@api_router.post("/admin/restock")
async def restock_product(request: RestockRequest, current_user: User = Depends(get_current_user)):
    """Admin endpoint to restock products"""
    stock_key = f"stock:{request.product_id}"
    
    # Check if product exists
    product_data = await redis_client.get(f"product:{request.product_id}")
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Add stock
    new_stock = await redis_client.incrby(stock_key, request.quantity)
    
    return {"product_id": request.product_id, "new_stock": new_stock, "message": "Stock updated successfully"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "scalemart-api"}

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

@app.on_event("startup")
async def startup_event():
    try:
        await initialize_products()
        logger.info("ScaleMart API started and products initialized")
    except Exception as e:
        logger.warning(f"Could not initialize Redis products: {e}")
        logger.info("ScaleMart API started WITHOUT Redis cache - app will work but slower")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    try:
        await redis_client.close()
    except:
        pass  # Redis wasn't connected