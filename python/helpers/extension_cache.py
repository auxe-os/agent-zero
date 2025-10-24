"""
Extension Performance Cache System
Optimizes extension loading and execution by implementing intelligent caching
"""
import asyncio
import time
from typing import Dict, List, Type, Any, Optional
from dataclasses import dataclass
from python.helpers.extension import Extension
from python.helpers.extract_tools import load_classes_from_folder
from python.helpers import files


@dataclass
class ExtensionCacheEntry:
    """Cache entry for extension classes"""
    classes: List[Type[Extension]]
    last_accessed: float
    access_count: int
    folder_path: str
    folder_mtime: float


class ExtensionCache:
    """High-performance extension caching system"""
    
    def __init__(self, max_size: int = 50, ttl_seconds: int = 300):
        self._cache: Dict[str, ExtensionCacheEntry] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'loads': 0
        }
    
    async def get_extensions(self, extension_point: str, agent_profile: Optional[str] = None) -> List[Type[Extension]]:
        """Get extension classes with intelligent caching"""
        cache_key = f"{agent_profile}:{extension_point}" if agent_profile else f"default:{extension_point}"
        
        async with self._lock:
            # Check cache first
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                current_time = time.time()
                
                # Check TTL
                if current_time - entry.last_accessed < self._ttl_seconds:
                    entry.last_accessed = current_time
                    entry.access_count += 1
                    self._stats['hits'] += 1
                    return entry.classes
                else:
                    # TTL expired, remove from cache
                    del self._cache[cache_key]
                    self._stats['evictions'] += 1
            
            # Cache miss - load extension classes
            self._stats['misses'] += 1
            classes = await self._load_extensions(extension_point, agent_profile)
            
            if classes:
                # Add to cache
                await self._add_to_cache(cache_key, classes, extension_point, agent_profile)
                self._stats['loads'] += 1
            
            return classes
    
    async def _load_extensions(self, extension_point: str, agent_profile: Optional[str] = None) -> List[Type[Extension]]:
        """Load extension classes from file system"""
        try:
            # Try agent-specific extensions first
            if agent_profile:
                try:
                    folder_path = f"agents/{agent_profile}/extensions/{extension_point}"
                    if files.exists(folder_path):
                        classes = load_classes_from_folder(folder_path, "*", Extension)
                        if classes:
                            return classes
                except Exception:
                    pass
            
            # Try default extensions
            try:
                folder_path = f"python/extensions/{extension_point}"
                if files.exists(folder_path):
                    classes = load_classes_from_folder(folder_path, "*", Extension)
                    return classes
            except Exception:
                pass
                
        except Exception as e:
            print(f"ExtensionCache: Failed to load {extension_point}: {e}")
        
        return []
    
    async def _add_to_cache(self, cache_key: str, classes: List[Type[Extension]], extension_point: str, agent_profile: Optional[str] = None):
        """Add extension classes to cache with LRU eviction"""
        current_time = time.time()
        
        # Determine folder path for mtime tracking
        if agent_profile:
            folder_path = f"agents/{agent_profile}/extensions/{extension_point}"
        else:
            folder_path = f"python/extensions/{extension_point}"
        
        # Get folder modification time (use most recent file in folder)
        try:
            import os
            folder_mtime = 0
            if os.path.exists(folder_path):
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            file_mtime = os.path.getmtime(file_path)
                            folder_mtime = max(folder_mtime, file_mtime)
        except:
            folder_mtime = current_time
        
        # Create cache entry
        entry = ExtensionCacheEntry(
            classes=classes,
            last_accessed=current_time,
            access_count=1,
            folder_path=folder_path,
            folder_mtime=folder_mtime
        )
        
        # Check if cache is full
        if len(self._cache) >= self._max_size:
            # LRU eviction
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
        
        self._cache[cache_key] = entry
    
    async def invalidate_extension(self, extension_point: str, agent_profile: Optional[str] = None):
        """Invalidate cached extension classes"""
        cache_key = f"{agent_profile}:{extension_point}" if agent_profile else f"default:{extension_point}"
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
    
    async def clear_cache(self):
        """Clear all cached extension classes"""
        async with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'max_size': self._max_size,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests,
            'hits': self._stats['hits'],
            'misses': self._stats['misses'],
            'evictions': self._stats['evictions'],
            'loads': self._stats['loads']
        }
    
    async def cleanup_expired(self):
        """Remove expired entries from cache"""
        current_time = time.time()
        async with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry.last_accessed > self._ttl_seconds
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats['evictions'] += 1


# Global extension cache instance
_extension_cache = ExtensionCache()


async def get_cached_extensions(extension_point: str, agent_profile: Optional[str] = None) -> List[Type[Extension]]:
    """Get extension classes with caching"""
    return await _extension_cache.get_extensions(extension_point, agent_profile)


async def invalidate_extension_cache(extension_point: str, agent_profile: Optional[str] = None):
    """Invalidate cached extension classes"""
    await _extension_cache.invalidate_extension(extension_point, agent_profile)


async def clear_extension_cache():
    """Clear all cached extension classes"""
    await _extension_cache.clear_cache()


def get_extension_cache_stats() -> Dict[str, Any]:
    """Get extension cache performance statistics"""
    return _extension_cache.get_stats()


async def cleanup_extension_cache():
    """Cleanup expired cache entries"""
    await _extension_cache.cleanup_expired()
