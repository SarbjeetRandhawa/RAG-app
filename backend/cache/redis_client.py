import os
import redis
import logging

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        self.enabled = os.environ.get("ENABLE_REDIS", "true").lower() == "true"
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.client = None
        
        if self.enabled:
            try:
                self.client = redis.Redis.from_url(self.redis_url, decode_responses=True, protocol=2)
                # Test connection
                self.client.ping()
                logger.info("Connected to Redis successfully.")
            except redis.exceptions.ConnectionError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to normal execution.")
                self.client = None
                self.enabled = False
            except Exception as e:
                logger.warning(f"Unexpected Redis error: {e}. Falling back to normal execution.")
                self.client = None
                self.enabled = False
                
    def is_available(self) -> bool:
        """Live check — pings Redis to verify it's actually reachable."""
        if not self.enabled or self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception:
            return False
        
    def get_client(self):
        return self.client

redis_client = RedisClient()
