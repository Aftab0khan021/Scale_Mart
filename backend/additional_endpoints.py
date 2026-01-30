"""
Additional API endpoints for enhanced features
Add these to your server.py
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import StreamingResponse
from typing import Optional, List
import csv
import io
from datetime import datetime, timezone, timedelta

# ============================================================================
# PRODUCT SEARCH
# ============================================================================

@api_router.get("/products/search")
async def search_products(
    q: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    flash_sale_only: bool = False
):
    """
    Search and filter products
    - q: Search query (searches name and description)
    - category: Filter by category
    - min_price, max_price: Price range
    - flash_sale_only: Show only flash sale items
    """
    query = {}
    
    # Text search
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}}
        ]
    
    # Category filter
    if category:
        query["category"] = category
    
    # Price range
    if min_price is not None or max_price is not None:
        query["price"] = {}
        if min_price is not None:
            query["price"]["$gte"] = min_price
        if max_price is not None:
            query["price"]["$lte"] = max_price
    
    # Flash sale filter
    if flash_sale_only:
        query["flash_sale"] = True
    
    # Get products from Redis (or MongoDB if you prefer)
    all_products = []
    for i in range(1, 7):  # Assuming 6 products
        product_data = await redis_client.get(f"product:prod_{i}")
        if product_data:
            import json
            product = json.loads(product_data)
            
            # Get current stock
            stock = await redis_client.get(f"stock:prod_{i}")
            product['stock'] = int(stock) if stock else 0
            
            # Apply filters
            matches = True
            
            if q:
                search_text = f"{product['name']} {product['description']}".lower()
                if q.lower() not in search_text:
                    matches = False
            
            if category and product.get('category', 'general') != category:
                matches = False
            
            if min_price is not None and product['price'] < min_price:
                matches = False
            
            if max_price is not None and product['price'] > max_price:
                matches = False
            
            if flash_sale_only and not product.get('flash_sale', False):
                matches = False
            
            if matches:
                all_products.append(product)
    
    return {
        "results": all_products,
        "count": len(all_products),
        "query": q
    }


# ============================================================================
# ORDER CANCELLATION
# ============================================================================

@api_router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Cancel an order (only if status is 'pending')
    """
    # Find order
    order = await db.orders.find_one({"id": order_id})
    
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check ownership
    if order['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this order")
    
    # Check if cancellable
    if order['status'] != 'pending':
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order['status']}'. Only pending orders can be cancelled."
        )
    
    # Check time limit (e.g., can only cancel within 5 minutes)
    created_at = order['created_at']
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
    
    time_diff = datetime.now(timezone.utc) - created_at
    if time_diff > timedelta(minutes=5):
        raise HTTPException(
            status_code=400,
            detail="Order can only be cancelled within 5 minutes of placement"
        )
    
    # Restore stock in Redis
    product_id = order['product_id']
    quantity = order['quantity']
    await redis_client.incrby(f"stock:{product_id}", quantity)
    
    # Update order status
    await db.orders.update_one(
        {"id": order_id},
        {
            "$set": {
                "status": "cancelled",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "cancelled_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {
        "success": True,
        "message": "Order cancelled successfully",
        "order_id": order_id,
        "refunded_stock": quantity
    }


# ============================================================================
# CSV EXPORT
# ============================================================================

@api_router.get("/admin/orders/export")
async def export_orders_csv(
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    Export orders to CSV (admin only)
    """
    # TODO: Add admin check
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Admin access required")
    
    # Build query
    query = {}
    if start_date or end_date:
        query['created_at'] = {}
        if start_date:
            query['created_at']['$gte'] = start_date
        if end_date:
            query['created_at']['$lte'] = end_date
    
    # Fetch orders
    orders = await db.orders.find(query).to_list(length=10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Order ID',
        'User Email',
        'Product Name',
        'Quantity',
        'Total Price',
        'Status',
        'Created At',
        'Updated At'
    ])
    
    # Write data
    for order in orders:
        writer.writerow([
            order.get('id', ''),
            order.get('user_email', ''),
            order.get('product_name', ''),
            order.get('quantity', 0),
            order.get('total_price', 0),
            order.get('status', ''),
            order.get('created_at', ''),
            order.get('updated_at', '')
        ])
    
    # Prepare response
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=orders_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# ============================================================================
# ANALYTICS DASHBOARD
# ============================================================================

@api_router.get("/admin/analytics")
async def get_analytics(
    current_user: User = Depends(get_current_user),
    days: int = 7
):
    """
    Get analytics data for dashboard
    """
    # Calculate date range
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days)
    
    # Total orders
    total_orders = await db.orders.count_documents({})
    
    # Orders by status
    pending_orders = await db.orders.count_documents({"status": "pending"})
    confirmed_orders = await db.orders.count_documents({"status": "confirmed"})
    cancelled_orders = await db.orders.count_documents({"status": "cancelled"})
    
    # Total revenue
    revenue_pipeline = [
        {"$match": {"status": "confirmed"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
    ]
    revenue_result = await db.orders.aggregate(revenue_pipeline).to_list(length=1)
    total_revenue = revenue_result[0]['total'] if revenue_result else 0
    
    # Revenue by day (last 7 days)
    daily_revenue_pipeline = [
        {
            "$match": {
                "status": "confirmed",
                "created_at": {"$gte": start_date.isoformat()}
            }
        },
        {
            "$group": {
                "_id": {"$substr": ["$created_at", 0, 10]},  # Group by date
                "revenue": {"$sum": "$total_price"},
                "orders": {"$sum": 1}
            }
        },
        {"$sort": {"_id": 1}}
    ]
    daily_revenue = await db.orders.aggregate(daily_revenue_pipeline).to_list(length=days)
    
    # Top products
    top_products_pipeline = [
        {"$match": {"status": "confirmed"}},
        {
            "$group": {
                "_id": "$product_id",
                "product_name": {"$first": "$product_name"},
                "total_sold": {"$sum": "$quantity"},
                "revenue": {"$sum": "$total_price"}
            }
        },
        {"$sort": {"total_sold": -1}},
        {"$limit": 5}
    ]
    top_products = await db.orders.aggregate(top_products_pipeline).to_list(length=5)
    
    # Low stock products
    low_stock_products = []
    for i in range(1, 7):
        product_data = await redis_client.get(f"product:prod_{i}")
        if product_data:
            import json
            product = json.loads(product_data)
            stock = await redis_client.get(f"stock:prod_{i}")
            stock_count = int(stock) if stock else 0
            
            if stock_count < 20:  # Low stock threshold
                low_stock_products.append({
                    "id": product['id'],
                    "name": product['name'],
                    "stock": stock_count
                })
    
    # Sales velocity (orders per hour)
    recent_orders = await db.orders.count_documents({
        "created_at": {"$gte": (end_date - timedelta(hours=1)).isoformat()}
    })
    
    return {
        "summary": {
            "total_orders": total_orders,
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": round(total_revenue, 2),
            "sales_velocity": recent_orders
        },
        "daily_revenue": [
            {
                "date": item['_id'],
                "revenue": round(item['revenue'], 2),
                "orders": item['orders']
            }
            for item in daily_revenue
        ],
        "top_products": [
            {
                "product_id": item['_id'],
                "product_name": item['product_name'],
                "total_sold": item['total_sold'],
                "revenue": round(item['revenue'], 2)
            }
            for item in top_products
        ],
        "low_stock_products": low_stock_products
    }


# Usage: Add these endpoints to your server.py by copying them into the file
