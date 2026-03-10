import os
import json

REDIS_URL = os.environ.get("REDIS_URL") or os.environ.get("KV_URL")

redis_client = None
if REDIS_URL:
    try:
        import redis
        # KV_URL typically comes from Vercel KV or Upstash, and often looks like redis://...
        # Ensure we decode responses to work directly with strings
        redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    except Exception as e:
        print(f"Failed to initialize Redis client: {e}")

def kv_get(key: str):
    """Retrieve and parse JSON from Redis."""
    if redis_client:
        try:
            val = redis_client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            print(f"Redis get error for {key}: {e}")
    return None

def kv_set(key: str, data):
    """Serialize and save JSON to Redis."""
    if redis_client:
        try:
            redis_client.set(key, json.dumps(data, ensure_ascii=False))
            return True
        except Exception as e:
            print(f"Redis set error for {key}: {e}")
    return False
