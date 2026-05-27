"""
Database Configuration using Supabase Python SDK with demo fallback.
Compatible with FastAPI async endpoints.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.auth.config import get_settings
from backend.auth.models import pwd_context

# Lazy initialization
db_client = None
db_available = False

# Demo users for when database is not available
DEMO_USERS = {
    "demo": {
        "id": "demo-user-1",
        "username": "demo",
        "email": "demo@example.com",
        "hashed_password": pwd_context.hash("demo123"),
        "points": 1000.0,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    },
    "test": {
        "id": "demo-user-2",
        "username": "test",
        "email": "test@example.com",
        "hashed_password": pwd_context.hash("test123"),
        "points": 500.0,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
}

# Demo transactions for demo users
DEMO_TRANSACTIONS = {
    "demo-user-1": [
        {"id": "tx-1", "user_id": "demo-user-1", "quantity": 100, "price": 0.12, "total_price": 12.0, "fee": 0.12, "type": "buy", "created_at": "2024-01-15T10:30:00"},
        {"id": "tx-2", "user_id": "demo-user-1", "quantity": 50, "price": 0.15, "total_price": 7.5, "fee": 0.075, "type": "sell", "created_at": "2024-01-16T14:20:00"}
    ]
}


def get_supabase_client():
    """Lazy initialize Supabase client."""
    global db_client
    if db_client is not None:
        return db_client
    
    try:
        from supabase import create_client, Client
        settings = get_settings()
        
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            print("Supabase URL or Key not configured")
            return None
        
        db_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return db_client
    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        return None


async def init_db():
    """Test connection with retry, then ensure tables exist."""
    global db_available
    max_retries = 2
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Supabase init attempt {attempt}/{max_retries}...")
            client = get_supabase_client()
            
            if not client:
                print("Supabase client not available")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                continue
            
            # Test connection by fetching something simple
            response = client.table("users").select("count", count="exact").limit(1).execute()
            print("Supabase ping successful - Connected!")
            
            db_available = True
            return True
            
        except Exception as ping_error:
            print(f"Ping failed (attempt {attempt}): {ping_error}")
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)
    
    db_available = False
    print("Supabase not available, running in DEMO mode with mock users.")
    return False


def is_demo_mode():
    """Check if running in demo mode (no database)."""
    return not db_available


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    # Demo mode fallback
    if not db_available:
        return DEMO_USERS.get(username)
    
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        response = client.table("users").select("*").eq("username", username).maybe_single().execute()
        user = response.data
        
        if user:
            user["id"] = str(user.get("id"))
            return user
        return None
        
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    # Demo mode fallback
    if not db_available:
        for user in DEMO_USERS.values():
            if user.get("email") == email:
                return user
        return None
    
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        response = client.table("users").select("*").eq("email", email).maybe_single().execute()
        user = response.data
        
        if user:
            user["id"] = str(user.get("id"))
            return user
        return None
        
    except Exception as e:
        print(f"Error getting user by email: {e}")
        return None


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID (UUID)."""
    # Demo mode fallback
    if not db_available:
        for user in DEMO_USERS.values():
            if user.get("id") == user_id:
                return user
        return None
    
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        response = client.table("users").select("*").eq("id", user_id).maybe_single().execute()
        user = response.data
        
        if user:
            user["id"] = str(user.get("id"))
            return user
        return None
        
    except Exception as e:
        print(f"Error getting user by id: {e}")
        return None


async def create_user(user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create new user."""
    # Demo mode fallback - create in memory
    if not db_available:
        username = user_data.get("username")
        if username in DEMO_USERS:
            return None
        new_user = {
            "id": f"demo-user-{len(DEMO_USERS) + 1}",
            "username": username,
            "email": user_data.get("email"),
            "hashed_password": user_data.get("hashed_password"),
            "points": user_data.get("points", 1000.0),
            "is_active": True,
            "is_superuser": False,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        DEMO_USERS[username] = new_user
        return new_user
    
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        if "points" not in user_data:
            user_data["points"] = 1000.0
        
        user_data["created_at"] = datetime.utcnow().isoformat()
        
        response = client.table("users").insert(user_data).execute()
        
        if response.data:
            created_user = response.data[0]
            created_user["id"] = str(created_user.get("id"))
            return created_user
        return None
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return None


async def update_user(user_id: str, update_data: Dict[str, Any]) -> bool:
    """Update existing user."""
    # Demo mode fallback
    if not db_available:
        for user in DEMO_USERS.values():
            if user.get("id") == user_id:
                user.update(update_data)
                return True
        return False
    
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        response = client.table("users").update(update_data).eq("id", user_id).execute()
        return len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating user: {e}")
        return False


async def get_points_balance(user_id: str) -> float:
    """Get user's points balance."""
    try:
        user = await get_user_by_id(user_id)
        if user:
            return float(user.get("points", 0.0))
        return 0.0
        
    except Exception as e:
        print(f"Error getting points balance: {e}")
        return 0.0


async def update_points(user_id: str, delta: float) -> bool:
    """Update user's points by delta."""
    # Demo mode fallback
    if not db_available:
        for user in DEMO_USERS.values():
            if user.get("id") == user_id:
                user["points"] = float(user.get("points", 0.0)) + delta
                return True
        return False
    
    try:
        client = get_supabase_client()
        if not client:
            return False
        
        user = await get_user_by_id(user_id)
        if not user:
            return False
        
        current_points = float(user.get("points", 0.0))
        new_points = current_points + delta
        
        response = client.table("users").update({"points": new_points}).eq("id", user_id).execute()
        return len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating points: {e}")
        return False


async def create_transaction(tx_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a transaction record."""
    # Demo mode fallback
    if not db_available:
        tx_data["id"] = f"tx-{len(DEMO_TRANSACTIONS.get(tx_data.get('user_id'), [])) + 1}"
        tx_data["created_at"] = datetime.utcnow().isoformat()
        user_id = tx_data.get("user_id")
        if user_id not in DEMO_TRANSACTIONS:
            DEMO_TRANSACTIONS[user_id] = []
        DEMO_TRANSACTIONS[user_id].insert(0, tx_data)
        return tx_data
    
    try:
        client = get_supabase_client()
        if not client:
            return None
        
        tx_data["created_at"] = datetime.utcnow().isoformat()
        
        response = client.table("transactions").insert(tx_data).execute()
        
        if response.data:
            tx = response.data[0]
            tx["id"] = str(tx.get("id"))
            return tx
        return None
        
    except Exception as e:
        print(f"Error creating transaction: {e}")
        return None


async def get_user_transactions(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Get user's transaction history."""
    # Demo mode fallback
    if not db_available:
        return DEMO_TRANSACTIONS.get(user_id, [])[:limit]
    
    try:
        client = get_supabase_client()
        if not client:
            return []
        
        response = client.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        
        transactions = response.data or []
        for tx in transactions:
            tx["id"] = str(tx.get("id"))
        
        return transactions
        
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []
