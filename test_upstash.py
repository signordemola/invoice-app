import redis

from app.config import settings

connect_url = redis.from_url(settings.UPSTASH_REDIS_BROKER_URL)
print(connect_url.ping())
print(connect_url.info())