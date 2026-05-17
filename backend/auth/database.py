"""
MongoDB database configuration using Motor (async).
Compatible with FastAPI async endpoints.
"""

import motor.motor_asyncio
import asyncio
from backend.auth.config import get_settings


settings = get_settings()

# Lazy initialization
client = None
db = None
users_collection = None
transactions_collection = None

db_available = False


async def init_db():
    """Test connection with retry, then initialize indexes."""
    global client, db, users_collection, transactions_collection, db_available
    max_retries = 2
    ping_success = False
    
    # Initialize client lazily
    try:
        if client is None:
            print("Initializing MongoDB client...")
            client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.DATABASE_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
                retryWrites=True,
                authMechanism="DEFAULT",
                authSource="admin",
                w="majority",
                maxPoolSize=10,
            )
            db = client.geoflow
            users_collection = db.users
            transactions_collection = db.transactions
    except Exception as init_error:
        print(f"Failed to initialize MongoDB client: {init_error}")
        return
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"MongoDB init attempt {attempt}/{max_retries}...")
            await client.admin.command("ping")
            print("MongoDB ping successful - Connected to Atlas!")
            ping_success = True
            break
        except Exception as ping_error:
            print(f"Ping failed (attempt {attempt}): {ping_error}")
            if attempt == max_retries:
                print("MongoDB not available, running in limited mode.")
                break
            await asyncio.sleep(2 ** attempt)
    if ping_success:
        try:
            # Indexes only after ping success
            await users_collection.create_index("username", unique=True)
            await users_collection.create_index("email", unique=True)
            await users_collection.create_index("provider_id", unique=True, sparse=True)
            await transactions_collection.create_index("user_id")
            await transactions_collection.create_index("created_at")
            db_available = True
            print("MongoDB indexes created successfully")
        except Exception as index_error:
            print(f"Index creation failed: {index_error}")
            db_available = False
    else:
        db_available = False
        print("ERROR: MongoDB ping failed after retries. Check .env DATABASE_URL and Atlas whitelist.")
        print("App continues with limited DB functionality.")


async def get_user_by_username(username: str):
    user = await users_collection.find_one({"username": username})
    if user:
        user["id"] = user["_id"]
        user.pop("_id")
    return user


from bson import ObjectId

async def get_user_by_email(email: str):
    user = await users_collection.find_one({"email": email})
    if user:
        user["id"] = str(user["_id"])
        user.pop("_id")
    return user


async def create_user(user_data: dict):
    result = await users_collection.insert_one(user_data)
    user_data["_id"] = result.inserted_id
    user_data["id"] = str(result.inserted_id)
    del user_data["_id"]
    return user_data


async def get_user_by_id(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        user["id"] = str(user["_id"])
        user.pop("_id")
    return user


async def update_user(user_id: str, update_data: dict):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    return result.modified_count > 0


async def get_points_balance(user_id: str):
    user = await users_collection.find_one(
        {"_id": ObjectId(user_id)},
        {"points": 1}
    )
    return user["points"] if user else 0.0


async def update_points(user_id: str, delta: float):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"points": delta}}
    )
    return result.modified_count > 0


async def create_transaction(tx_data: dict):
    result = await transactions_collection.insert_one(tx_data)
    tx_data["_id"] = result.inserted_id
    tx_data["id"] = str(result.inserted_id)
    del tx_data["_id"]
    return tx_data


async def get_user_transactions(user_id: str, limit: int = 50):
    cursor = transactions_collection.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    transactions = await cursor.to_list(length=limit)
    for tx in transactions:
        tx["id"] = str(tx["_id"])
        del tx["_id"]
    return transactions

