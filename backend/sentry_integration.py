"""
Sentry integration for error tracking and performance monitoring.
Add this to backend/server.py
"""
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
import os

# Initialize Sentry
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
    traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions
    profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
    environment=os.environ.get("ENVIRONMENT", "development"),
    integrations=[
        FastApiIntegration(),
        RedisIntegration(),
        CeleryIntegration(),
    ],
    # Send default PII (Personally Identifiable Information)
    send_default_pii=False,
    # Enable performance monitoring
    enable_tracing=True,
)

# Custom error tracking function
def track_error(error: Exception, context: dict = None):
    """Track an error with additional context"""
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_context(key, value)
        sentry_sdk.capture_exception(error)

# Custom performance tracking
def track_performance(operation_name: str):
    """Context manager for tracking performance of operations"""
    return sentry_sdk.start_transaction(op=operation_name, name=operation_name)

# Usage example in server.py:
"""
# At the top of server.py, after imports:
from sentry_integration import sentry_sdk, track_error, track_performance

# In flash_buy endpoint:
@api_router.post("/flash-buy", response_model=OrderStatus)
async def flash_buy(
    request: FlashBuyRequest,
    current_user: User = Depends(get_current_user),
):
    with track_performance("flash_buy"):
        try:
            # ... existing code ...
        except Exception as e:
            track_error(e, {
                "user_id": current_user.id,
                "product_id": request.product_id,
                "quantity": request.quantity
            })
            raise
"""
