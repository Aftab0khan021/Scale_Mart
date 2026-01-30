"""
WebSocket manager for real-time updates
Handles stock updates, order notifications, and flash sale countdowns
"""
import socketio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # Configure properly in production
    logger=True,
    engineio_logger=False
)

# Track connected clients
connected_clients: Dict[str, Any] = {}


@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    logger.info(f"🔌 WebSocket client connected: {sid}")
    connected_clients[sid] = {
        'connected_at': environ.get('HTTP_DATE'),
        'subscriptions': []
    }
    await sio.emit('connection_established', {
        'status': 'connected',
        'client_id': sid
    }, room=sid)


@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    logger.info(f"🔌 WebSocket client disconnected: {sid}")
    if sid in connected_clients:
        del connected_clients[sid]


@sio.event
async def subscribe_product(sid, data):
    """Subscribe to product stock updates"""
    product_id = data.get('product_id')
    if product_id:
        room_name = f"product_{product_id}"
        await sio.enter_room(sid, room_name)
        
        if sid in connected_clients:
            connected_clients[sid]['subscriptions'].append(product_id)
        
        logger.info(f"📦 Client {sid} subscribed to product {product_id}")
        await sio.emit('subscribed', {
            'product_id': product_id,
            'status': 'subscribed'
        }, room=sid)


@sio.event
async def unsubscribe_product(sid, data):
    """Unsubscribe from product stock updates"""
    product_id = data.get('product_id')
    if product_id:
        room_name = f"product_{product_id}"
        await sio.leave_room(sid, room_name)
        
        if sid in connected_clients and product_id in connected_clients[sid]['subscriptions']:
            connected_clients[sid]['subscriptions'].remove(product_id)
        
        logger.info(f"📦 Client {sid} unsubscribed from product {product_id}")


@sio.event
async def subscribe_user_orders(sid, data):
    """Subscribe to user's order notifications"""
    user_id = data.get('user_id')
    if user_id:
        room_name = f"user_{user_id}"
        await sio.enter_room(sid, room_name)
        logger.info(f"👤 Client {sid} subscribed to user {user_id} orders")


# Helper functions for broadcasting

async def broadcast_stock_update(product_id: str, new_stock: int):
    """Broadcast stock update to all subscribed clients"""
    await sio.emit(
        'stock_update',
        {
            'product_id': product_id,
            'stock': new_stock,
            'timestamp': str(logger.time())
        },
        room=f"product_{product_id}"
    )
    logger.info(f"📢 Broadcasted stock update for {product_id}: {new_stock}")


async def broadcast_order_notification(user_id: str, order_data: dict):
    """Send order notification to specific user"""
    await sio.emit(
        'order_notification',
        {
            'order_id': order_data.get('id'),
            'status': order_data.get('status'),
            'message': f"Order {order_data.get('id')} is now {order_data.get('status')}",
            'timestamp': str(logger.time())
        },
        room=f"user_{user_id}"
    )
    logger.info(f"📬 Sent order notification to user {user_id}")


async def broadcast_flash_sale_start(product_id: str, product_data: dict):
    """Announce flash sale start"""
    await sio.emit(
        'flash_sale_start',
        {
            'product_id': product_id,
            'product_name': product_data.get('name'),
            'discount': product_data.get('discount_percent'),
            'stock': product_data.get('stock')
        },
        room='flash_sales'
    )
    logger.info(f"🔥 Announced flash sale for {product_id}")


async def get_connected_clients_count():
    """Get number of connected clients"""
    return len(connected_clients)


# Usage in server.py:
"""
from websocket_manager import sio, broadcast_stock_update, broadcast_order_notification
from socketio import ASGIApp

# Wrap FastAPI app
socket_app = ASGIApp(sio, app)

# In flash_buy endpoint, after stock update:
await broadcast_stock_update(product_id, new_stock)

# In order processing, after confirmation:
await broadcast_order_notification(user_id, order_data)
"""
