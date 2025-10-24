"""
Tool Performance Cache System
Optimizes tool loading and execution by implementing intelligent caching
"""
import asyncio
import time
from typing import Dict, Type, Any, Optional
from dataclasses import dataclass
from python.helpers.tool import Tool
from python.helpers.extract_tools import load_classes_from_file
from python.helpers.print_style import PrintStyle


@dataclass
class ToolCacheEntry:
    """Cache entry for a tool class"""
    tool_class: Type[Tool]
    last_accessed: float
    access_count: int
    file_path: str
    file_mtime: float


class ToolCache:
    """High-performance tool caching system"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self._cache: Dict[str, ToolCacheEntry] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._lock = asyncio.Lock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'loads': 0
        }
    
    async def get_tool_class(self, tool_name: str, agent_profile: str = None) -> Optional[Type[Tool]]:
        """Get tool class with intelligent caching"""
        cache_key = f"{agent_profile}:{tool_name}" if agent_profile else f"default:{tool_name}"
        
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
                    return entry.tool_class
                else:
                    # TTL expired, remove from cache
                    del self._cache[cache_key]
                    self._stats['evictions'] += 1
            
            # Cache miss - load tool class
            self._stats['misses'] += 1
            tool_class = await self._load_tool_class(tool_name, agent_profile)
            
            if tool_class:
                # Add to cache
                await self._add_to_cache(cache_key, tool_class, tool_name, agent_profile)
                self._stats['loads'] += 1
            
            return tool_class
    
    async def _load_tool_class(self, tool_name: str, agent_profile: str = None) -> Optional[Type[Tool]]:
        """Load tool class from file system"""
        try:
            # Try agent-specific tool first
            if agent_profile:
                try:
                    file_path = f"agents/{agent_profile}/tools/{tool_name}.py"
                    classes = load_classes_from_file(file_path, Tool)
                    if classes:
                        return classes[0]
                except Exception:
                    pass
            
            # Try default tool
            try:
                file_path = f"python/tools/{tool_name}.py"
                classes = load_classes_from_file(file_path, Tool)
                if classes:
                    return classes[0]
            except Exception:
                pass
                
        except Exception as e:
            PrintStyle(font_color="yellow").print(f"ToolCache: Failed to load {tool_name}: {e}")
        
        return None
    
    async def _add_to_cache(self, cache_key: str, tool_class: Type[Tool], tool_name: str, agent_profile: str = None):
        """Add tool class to cache with LRU eviction"""
        current_time = time.time()
        
        # Determine file path for mtime tracking
        if agent_profile:
            file_path = f"agents/{agent_profile}/tools/{tool_name}.py"
        else:
            file_path = f"python/tools/{tool_name}.py"
        
        # Get file modification time
        try:
            import os
            file_mtime = os.path.getmtime(file_path)
        except:
            file_mtime = current_time
        
        # Create cache entry
        entry = ToolCacheEntry(
            tool_class=tool_class,
            last_accessed=current_time,
            access_count=1,
            file_path=file_path,
            file_mtime=file_mtime
        )
        
        # Check if cache is full
        if len(self._cache) >= self._max_size:
            # LRU eviction
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
        
        self._cache[cache_key] = entry
    
    async def invalidate_tool(self, tool_name: str, agent_profile: str = None):
        """Invalidate cached tool class"""
        cache_key = f"{agent_profile}:{tool_name}" if agent_profile else f"default:{tool_name}"
        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
    
    async def clear_cache(self):
        """Clear all cached tool classes"""
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


# Global tool cache instance
_tool_cache = ToolCache()


async def get_cached_tool_class(tool_name: str, agent_profile: str = None) -> Optional[Type[Tool]]:
    """Get tool class with caching"""
    return await _tool_cache.get_tool_class(tool_name, agent_profile)


async def invalidate_tool_cache(tool_name: str, agent_profile: str = None):
    """Invalidate cached tool class"""
    await _tool_cache.invalidate_tool(tool_name, agent_profile)


async def clear_tool_cache():
    """Clear all cached tool classes"""
    await _tool_cache.clear_cache()


def get_tool_cache_stats() -> Dict[str, Any]:
    """Get tool cache performance statistics"""
    return _tool_cache.get_stats()


async def cleanup_tool_cache():
    """Cleanup expired cache entries"""
    await _tool_cache.cleanup_expired()
