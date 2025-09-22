from fastapi import FastAPI, HTTPException
from prisma import Prisma
import redis
import json
import time
from contextlib import asynccontextmanager

db = Prisma()
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Prisma (PostgreSQL) and initialize Redis
    await db.connect()
    # Test Redis connection
    try:
        redis_client.ping()
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
    yield
    # Shutdown: Disconnect from Prisma and close Redis connection
    await db.disconnect()
    redis_client.close()

app = FastAPI(lifespan=lifespan)

@app.get("/user/{username}")
async def get_user(username: str):
    cache_key = f"user:{username}"
    start = time.time()
    # 1. Check Redis
    cached = redis_client.get(cache_key)
    if cached:
        duration = (time.time() - start) * 1000
        return {"source": "redis", "time_ms": duration, "data": json.loads(cached)}
    # 2. Fetch from Postgres
    user = await db.user.find_unique(
        where={"username": username},
        include={"posts": True},
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # 3. Cache in Redis
    redis_client.setex(cache_key, 60, json.dumps(user.dict(), default=str))
    duration = (time.time() - start) * 1000
    return {"source": "postgres", "time_ms": duration, "data": user.dict()}