import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import difflib
import re

class CachingSystem:
    def __init__(self, cache_dir: Optional[Path] = None, max_age_days: float = 7.0):
        """Initialize the caching system"""
        self.cache_dir = cache_dir or Path(os.getcwd()) / "cache"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.cache_db_path = self.cache_dir / "cache.json"
        self.max_age_days = max_age_days
        
        # Initialize cache
        self._init_cache_db()
        
        # Stats tracking
        self.stats = {
            "total_calls": 0,
            "cached_calls": 0,
            "tokens_used": 0,
            "tokens_saved": 0
        }
        
        # Load stats if they exist
        stats_path = self.cache_dir / "stats.json"
        if stats_path.exists():
            with open(stats_path, 'r') as f:
                self.stats = json.load(f)
    
    def _init_cache_db(self):
        """Initialize the cache database file if it doesn't exist"""
        if not self.cache_db_path.exists():
            with open(self.cache_db_path, 'w') as f:
                json.dump({}, f)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load the current cache from disk"""
        with open(self.cache_db_path, 'r') as f:
            return json.load(f)
    
    def _save_cache(self, cache_data: Dict[str, Any]):
        """Save the cache to disk"""
        with open(self.cache_db_path, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def _save_stats(self):
        """Save the stats to disk"""
        stats_path = self.cache_dir / "stats.json"
        with open(stats_path, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def store(self, key: str, data: Any):
        """Store data in the cache"""
        cache = self._load_cache()
        
        # Add timestamp for expiration
        entry = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        cache[key] = entry
        self._save_cache(cache)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve data from the cache"""
        cache = self._load_cache()
        
        if key not in cache:
            return None
        
        entry = cache[key]
        
        # Check if entry has expired
        timestamp = datetime.fromisoformat(entry["timestamp"])
        if (datetime.now() - timestamp) > timedelta(days=self.max_age_days):
            self.invalidate(key)
            return None
        
        return entry["data"]
    
    def invalidate(self, key: str):
        """Invalidate a specific cache entry"""
        cache = self._load_cache()
        
        if key in cache:
            del cache[key]
            self._save_cache(cache)
    
    def invalidate_all(self):
        """Invalidate all cache entries"""
        self._save_cache({})
    
    def cleanup(self):
        """Remove expired entries from the cache"""
        cache = self._load_cache()
        now = datetime.now()
        
        to_delete = []
        for key, entry in cache.items():
            timestamp = datetime.fromisoformat(entry["timestamp"])
            if (now - timestamp) > timedelta(days=self.max_age_days):
                to_delete.append(key)
        
        # Remove expired entries
        for key in to_delete:
            del cache[key]
        
        self._save_cache(cache)
        return len(to_delete)
    
    def record_api_call(self, call_type: str, tokens: int, cached: bool):
        """Record API call statistics"""
        self.stats["total_calls"] += 1
        
        if cached:
            self.stats["cached_calls"] += 1
            self.stats["tokens_saved"] += tokens
        else:
            self.stats["tokens_used"] += tokens
        
        self._save_stats()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current caching statistics"""
        stats = self.stats.copy()
        
        # Calculate derived statistics
        if stats["total_calls"] > 0:
            stats["cache_hit_rate"] = stats["cached_calls"] / stats["total_calls"]
        else:
            stats["cache_hit_rate"] = 0
            
        if (stats["tokens_used"] + stats["tokens_saved"]) > 0:
            stats["token_savings_percent"] = (stats["tokens_saved"] / 
                                             (stats["tokens_used"] + stats["tokens_saved"]) * 100)
        else:
            stats["token_savings_percent"] = 0
        
        return stats

class CacheSimilarityDetector:
    def __init__(self, cache_system: CachingSystem, similarity_threshold: float = 0.8):
        """Initialize the similarity detector"""
        self.cache = cache_system
        self.similarity_threshold = similarity_threshold
    
    def _compute_task_hash(self, task_content: str) -> str:
        """Compute a hash for the task content"""
        return hashlib.md5(task_content.encode()).hexdigest()
    
    def _extract_task_text(self, task_content: str) -> str:
        """Extract meaningful text from task content, removing frontmatter"""
        # Remove YAML frontmatter
        content = re.sub(r"^---\s*.*?---\s*", "", task_content, flags=re.DOTALL)
        return content.strip()
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        # Use difflib's SequenceMatcher for similarity
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def find_similar_task(self, task_content: str) -> Optional[Dict[str, Any]]:
        """Find similar task in cache"""
        task_hash = self._compute_task_hash(task_content)
        
        # First check if exact task is in cache
        cache_key = f"analysis_{task_hash}"
        if self.cache.retrieve(cache_key) is not None:
            return None  # Task is already in cache
        
        # Extract meaningful text
        task_text = self._extract_task_text(task_content)
        
        # Load all cached analyses
        cache_data = self.cache._load_cache()
        
        best_match = None
        best_similarity = 0
        
        for key, entry in cache_data.items():
            # Only look at analysis entries
            if not key.startswith("analysis_"):
                continue
            
            # Get cached task content
            cached_hash = key.replace("analysis_", "")
            cached_task_key = f"task_{cached_hash}"
            cached_task = self.cache.retrieve(cached_task_key)
            
            if cached_task is None:
                continue
            
            # Calculate similarity
            cached_text = self._extract_task_text(cached_task)
            similarity = self._calculate_similarity(task_text, cached_text)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry["data"]
        
        # Return best match if it's above threshold
        if best_similarity >= self.similarity_threshold:
            return best_match
        
        return None
    
    def cache_task_analysis(self, task_content: str, analysis: Dict[str, Any]):
        """Cache task content and its analysis"""
        task_hash = self._compute_task_hash(task_content)
        
        # Store task content
        self.cache.store(f"task_{task_hash}", task_content)
        
        # Store analysis
        self.cache.store(f"analysis_{task_hash}", analysis)

class TaskCache:
    def __init__(self, root_dir: Optional[Path] = None):
        """Initialize the task caching system"""
        self.root_dir = root_dir or Path(os.getcwd())
        self.cache_dir = self.root_dir / "cache"
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        
        self.caching_system = CachingSystem(self.cache_dir)
        self.similarity_detector = CacheSimilarityDetector(self.caching_system)
    
    def get_cached_analysis(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis for a task if available"""
        task_path = self._find_task_file(task_id)
        
        if not task_path:
            return None
        
        task_content = task_path.read_text()
        
        # Try to find similar task
        similar_analysis = self.similarity_detector.find_similar_task(task_content)
        
        if similar_analysis:
            # Record token savings (estimation)
            estimated_tokens = similar_analysis.get("estimated_tokens", 500)
            self.caching_system.record_api_call("analysis", estimated_tokens, cached=True)
            
            # Return the cached analysis
            return similar_analysis
        
        return None
    
    def cache_analysis(self, task_id: str, analysis: Dict[str, Any], tokens_used: int):
        """Cache analysis for a task"""
        task_path = self._find_task_file(task_id)
        
        if not task_path:
            return
        
        task_content = task_path.read_text()
        
        # Add estimated tokens
        analysis["estimated_tokens"] = tokens_used
        
        # Cache the task and analysis
        self.similarity_detector.cache_task_analysis(task_content, analysis)
        
        # Record token usage
        self.caching_system.record_api_call("analysis", tokens_used, cached=False)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get caching statistics"""
        return self.caching_system.get_statistics()
    
    def _find_task_file(self, task_id: str) -> Optional[Path]:
        """Find task file by ID"""
        todo_dir = self.root_dir / "TASKS" / "TODO"
        
        if not todo_dir.exists():
            return None
        
        for file in todo_dir.glob(f"{task_id}*.md"):
            return file
        
        return None

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Task caching system")
    parser.add_argument("--cleanup", action="store_true", help="Clean up expired cache entries")
    parser.add_argument("--stats", action="store_true", help="Show caching statistics")
    parser.add_argument("--invalidate", help="Invalidate specific cache entry")
    parser.add_argument("--invalidate-all", action="store_true", help="Invalidate all cache entries")
    
    args = parser.parse_args()
    
    cache = TaskCache()
    
    if args.cleanup:
        removed = cache.caching_system.cleanup()
        print(f"Removed {removed} expired cache entries")
    
    if args.stats:
        stats = cache.get_statistics()
        print("Caching Statistics:")
        print(f"  Total API calls: {stats['total_calls']}")
        print(f"  Cached calls: {stats['cached_calls']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.2f}")
        print(f"  Tokens used: {stats['tokens_used']}")
        print(f"  Tokens saved: {stats['tokens_saved']}")
        print(f"  Token savings: {stats['token_savings_percent']:.2f}%")
    
    if args.invalidate:
        cache.caching_system.invalidate(args.invalidate)
        print(f"Invalidated cache entry: {args.invalidate}")
    
    if args.invalidate_all:
        cache.caching_system.invalidate_all()
        print("Invalidated all cache entries")