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


def kv_set_with_ttl(key: str, data, ttl_seconds: int):
    """Serialize and save JSON to Redis with a fixed TTL (seconds).

    The key will auto-expire after ttl_seconds regardless of subsequent reads.
    """
    if redis_client:
        try:
            redis_client.set(key, json.dumps(data, ensure_ascii=False), ex=ttl_seconds)
            return True
        except Exception as e:
            print(f"Redis set_with_ttl error for {key}: {e}")
    return False


def kv_ttl(key: str) -> int:
    """Return remaining TTL in seconds for a key.

    Returns:
      > 0 : seconds remaining
      -1  : key exists but has no expiry
      -2  : key does not exist (or expired)
    """
    if redis_client:
        try:
            return redis_client.ttl(key)
        except Exception as e:
            print(f"Redis ttl error for {key}: {e}")
    return -2


def kv_delete(key: str):
    """Delete a key from Redis."""
    if redis_client:
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error for {key}: {e}")
    return False
