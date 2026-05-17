"""
Authentication and points API routes.
Updated for MongoDB and virtual points trading.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
from datetime import timedelta
import uuid
import secrets

from backend.auth.database import (
    db_available, init_db, get_user_by_username, create_user, get_user_by_email,
    get_user_by_id, update_user, get_points_balance, update_points,
    create_transaction, get_user_transactions
)
from backend.auth.schemas import (
    UserCreate, UserLogin, UserResponse, Token, MessageResponse, ForgotPassword,
    PointsBuySell, PointsBalance, TransactionResponse, MarketPrice
)
from backend.auth.token import create_access_token, decode_access_token
from backend.auth.oauth import get_oauth_client, get_available_providers, OAuthError
from backend.auth.config import get_settings
from backend.auth.models import pwd_context
from backend.auth.database import db_available

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")


# Initialize Supabase on startup
@router.on_event("startup")
async def startup():
    import asyncio
    try:
        await asyncio.wait_for(init_db(), timeout=15.0)
    except asyncio.TimeoutError:
        print("Supabase init timed out, continuing without DB.")


@router.get("/providers", response_model=dict)
async def list_providers():
    """Get list of available OAuth providers."""
    providers = get_available_providers()
    return {"providers": providers}


@router.get("/login/{provider}", response_model=dict)
async def oauth_login(provider: str, state: Optional[str] = Query(None)):
    """Redirect to OAuth provider authorization page."""
    try:
        client = get_oauth_client(provider)
        auth_url = client.get_authorization_url(state)
        return {"authorization_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create auth URL: {str(e)}")


@router.get("/callback/{provider}")
async def oauth_callback(
    provider: str, 
    code: str = Query(...),
    state: Optional[str] = Query(None)
):
    """Handle OAuth callback and create/update user."""
    try:
        client = get_oauth_client(provider)
        token_data = client.get_token(code)
        access_token = token_data.get("access_token")
        user_info = client.get_user_info(access_token)
        
        # Use email as username for OAuth users
        username = user_info.get("username") or user_info.get("email") or f"{provider}_{user_info['id'][:8]}"
        
        user = await get_user_by_email(user_info.get("email"))
        if user:
            # Update existing
            update_data = {
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url"),
                "provider": provider,
                "provider_id": str(user_info["id"])
            }
            await update_user(user["id"], update_data)
        else:
            # Create new OAuth user with initial points
            user_data = {
                "username": username,
                "email": user_info.get("email"),
                "full_name": user_info.get("name"),
                "avatar_url": user_info.get("avatar_url"),
                "provider": provider,
                "provider_id": str(user_info["id"]),
                "points": 1000.0  # Welcome bonus
            }
            user = await create_user(user_data)
        
        token_payload = {"sub": str(user["id"]), "username": user["username"]}
        access_token_jwt = create_access_token(
            data=token_payload,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return RedirectResponse(url=f"/#/login/success?token={access_token_jwt}&user_id={user['id']}")
        
    except OAuthError as e:
        raise HTTPException(status_code=400, detail=f"OAuth error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auth failed: {str(e)}")


@router.post("/register", response_model=MessageResponse)
async def register(user: UserCreate):
    """Register new local user with initial points."""
    # Check if user exists
    existing = await get_user_by_username(user.username) or await get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    # Hash password
    hashed_password = pwd_context.hash(user.password)
    
    user_data = {
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password,
        "points": 1000.0  # New user bonus
    }
    
    await create_user(user_data)
    return {"message": "注册成功！请登录", "success": True}


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """Local user login with credentials."""
    user = await get_user_by_username(credentials.username)
    if not user or not pwd_context.verify(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="账户已禁用")
    
    token_payload = {"sub": str(user["id"]), "username": user["username"]}
    access_token_jwt = create_access_token(
        data=token_payload,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token_jwt,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": UserResponse.model_validate(user)
    }


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(email_data: ForgotPassword, background_tasks: BackgroundTasks):
    """Send password reset email (mock for demo)."""
    user = await get_user_by_email(email_data.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "如果邮箱存在，重置链接已发送", "success": True}
    
    # In production: Generate reset token, send email via SMTP
    reset_token = secrets.token_urlsafe(32)
    # background_tasks.add_task(send_reset_email, email_data.email, reset_token)
    
    return {"message": "重置链接已发送，请检查邮箱 (demo mode)", "success": True}


@router.get("/me", response_model=UserResponse)
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user with points."""
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# Points API
@router.get("/points/balance", response_model=PointsBalance)
async def get_balance(token: str = Depends(oauth2_scheme)):
    """Get user points balance."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    points = await get_points_balance(user_id)
    return {"points": points}


@router.post("/points/buy", response_model=MessageResponse)
async def buy_points(form: PointsBuySell, token: str = Depends(oauth2_scheme)):
    """Buy virtual points."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    
    total = form.quantity * form.price
    fee = total * 0.01  # 1% fee
    net_cost = total + fee
    
    # Mock payment - in production integrate payment gateway
    # For demo, assume payment succeeds
    delta = form.quantity  # Points gained
    
    await update_points(user_id, delta)
    
    tx_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "quantity": form.quantity,
        "price": form.price,
        "total_price": total,
        "fee": fee,
        "type": "buy"
    }
    await create_transaction(tx_data)
    
    return {"message": f"购买成功！获得 {form.quantity} 点", "success": True}


@router.post("/points/sell", response_model=MessageResponse)
async def sell_points(form: PointsBuySell, token: str = Depends(oauth2_scheme)):
    """Sell virtual points."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    
    # Check balance
    points = await get_points_balance(user_id)
    if points < form.quantity:
        raise HTTPException(status_code=400, detail="虚拟点余额不足")
    
    total = form.quantity * form.price
    fee = total * 0.01
    net_income = total - fee
    
    delta = -form.quantity  # Points lost
    
    await update_points(user_id, delta)
    
    tx_data = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "quantity": form.quantity,
        "price": form.price,
        "total_price": total,
        "fee": fee,
        "type": "sell"
    }
    await create_transaction(tx_data)
    
    return {"message": f"出售成功！收入 {net_income:.2f} 元", "success": True}


@router.get("/points/history", response_model=List[TransactionResponse])
async def get_history(limit: int = Query(50), token: str = Depends(oauth2_scheme)):
    """Get user transaction history."""
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    transactions = await get_user_transactions(user_id, limit)
    return transactions


@router.get("/db/health")
async def db_health():
    """DB connection health check."""
    db_url = settings.SUPABASE_URL if settings.SUPABASE_URL else 'N/A'
    if db_url != 'N/A' and len(db_url) > 40:
        db_url = db_url[:20] + '...'
    return {
        "db_available": db_available,
        "database_url": db_url,
        "status": "healthy" if db_available else "limited"
    }


@router.get("/points/market", response_model=MarketPrice)
async def get_market_price():
    """Get current market price (mock)."""
    import random
    base_price = 0.12
    change = (random.random() - 0.5) * 0.1  # ±5%
    return {"current_price": base_price + change, "change_24h": change}

