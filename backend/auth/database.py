"""
Supabase Database Configuration using Supabase Python SDK.
Compatible with FastAPI async endpoints.
"""

import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
from backend.auth.config import get_settings

# Lazy initialization
db_client = None
db_available = False


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
    print("Supabase not available, running in limited mode.")
    return False


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    try:
        client = get_supabase_client()
        if not client or not db_available:
            return None
        
        response = client.table("users").select("*").eq("username", username).maybe_single().execute()
        user = response.data
        
        if user:
            # Convert UUID id to string for consistency
            user["id"] = str(user.get("id"))
            return user
        return None
        
    except Exception as e:
        print(f"Error getting user by username: {e}")
        return None


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email."""
    try:
        client = get_supabase_client()
        if not client or not db_available:
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
    try:
        client = get_supabase_client()
        if not client or not db_available:
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
    try:
        client = get_supabase_client()
        if not client or not db_available:
            return None
        
        # Ensure points are set
        if "points" not in user_data:
            user_data["points"] = 1000.0
        
        # Set created timestamp
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
    try:
        client = get_supabase_client()
        if not client or not db_available:
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
    try:
        client = get_supabase_client()
        if not client or not db_available:
            return False
        
        # Get current points
        user = await get_user_by_id(user_id)
        if not user:
            return False
        
        current_points = float(user.get("points", 0.0))
        new_points = current_points + delta
        
        # Update
        response = client.table("users").update({"points": new_points}).eq("id", user_id).execute()
        return len(response.data) > 0
        
    except Exception as e:
        print(f"Error updating points: {e}")
        return False


async def create_transaction(tx_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Create a transaction record."""
    try:
        client = get_supabase_client()
        if not client or not db_available:
            return None
        
        # Set created timestamp
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
    try:
        client = get_supabase_client()
        if not client or not db_available:
            return []
        
        response = client.table("transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
        
        transactions = response.data or []
        for tx in transactions:
            tx["id"] = str(tx.get("id"))
        
        return transactions
        
    except Exception as e:
        print(f"Error getting transactions: {e}")
        return []
