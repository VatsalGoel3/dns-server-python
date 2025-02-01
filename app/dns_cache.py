from collections import defaultdict
import time
import threading
import logging

class DNSCache:
    def __init__(self, cleanup_interval=60):
        # Cache structure: {(domain_name, query_type): (expiry_time, response_data)}
        self._cache = {}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._start_cleanup_thread()

    def _start_cleanup_thread(self):
        """Starts a background thread to periodically clean expired entries"""
        def cleanup_loop():
            while True:
                self.cleanup_expired()
                time.sleep(self._cleanup_interval)
        
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()

    def get(self, domain_name: str, query_type: int) -> bytes:
        """Retrieve cached response if exists and not expired"""
        with self._lock:
            cache_key = (domain_name.lower(), query_type)
            if cache_key in self._cache:
                expiry_time, response = self._cache[cache_key]
                if time.time() < expiry_time:
                    logging.debug(f"Cache hit for {domain_name} (type: {query_type})")
                    return response
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
                    logging.debug(f"Cache entry expired for {domain_name}")
            return None

    def store(self, domain_name: str, query_type: int, response: bytes, ttl: int):
        """Store response in cache with expiry based on TTL"""
        with self._lock:
            cache_key = (domain_name.lower(), query_type)
            expiry_time = time.time() + ttl
            # Store original response without packet ID modification
            self._cache[cache_key] = (expiry_time, response)
            logging.debug(f"Cached response for {domain_name} (TTL: {ttl}s)")

    def cleanup_expired(self):
        """Remove expired entries from cache"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, (expiry, _) in self._cache.items() 
                if current_time >= expiry
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logging.debug(f"Cleaned up {len(expired_keys)} expired cache entries") 