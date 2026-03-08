"""
Professional Asynchronous Entropy Calculator
Prevents system freeze during mass file encryption attacks
"""

import math
import hashlib
import logging
from typing import Optional, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from threading import Lock
import time

logger = logging.getLogger(__name__)


class AsyncEntropyCalculator:
    """
    High-performance asynchronous entropy and hash calculator.
    Uses process pool for parallel calculation without blocking main thread.
    Includes smart caching and sampling for large files.
    """
    
    def __init__(self, max_workers: int = 4, cache_ttl: int = 300):
        """
        Initialize async entropy calculator.
        
        Args:
            max_workers: Number of worker processes (default: 4)
            cache_ttl: Cache time to live in seconds (default: 300s = 5min)
        """
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.cache: Dict[str, Tuple[float, Dict]] = {}  # {file_path: (timestamp, result)}
        self.lock = Lock()
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.calculations_done = 0
        self.timeouts = 0
        
        logger.info(f"AsyncEntropyCalculator initialized with {max_workers} workers")
    
    def calculate_entropy_async(self, file_path: str, timeout: float = 5.0) -> Optional[Dict]:
        """
        Calculate entropy and hash asynchronously with caching.
        
        Args:
            file_path: Path to file
            timeout: Maximum time to wait (default: 5s)
        
        Returns:
            Dict with entropy, hash, and file info or None
        """
        # Check cache first
        cached = self._check_cache(file_path)
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        
        try:
            # Submit to process pool
            future = self.executor.submit(_calculate_file_metrics, file_path)
            result = future.result(timeout=timeout)
            
            if result:
                self.calculations_done += 1
                # Cache the result
                self._cache_result(file_path, result)
                return result
        
        except TimeoutError:
            self.timeouts += 1
            logger.warning(f"Entropy calculation timeout for {file_path}")
            return None
        except Exception as e:
            logger.error(f"Entropy calculation error for {file_path}: {e}")
            return None
        
        return None
    
    def calculate_entropy_sync(self, file_path: str) -> Optional[Dict]:
        """
        Synchronous fallback (for small files or when needed).
        
        Args:
            file_path: Path to file
        
        Returns:
            Dict with entropy, hash, and file info
        """
        # Check cache first
        cached = self._check_cache(file_path)
        if cached:
            self.cache_hits += 1
            return cached
        
        self.cache_misses += 1
        
        try:
            result = _calculate_file_metrics(file_path)
            if result:
                self.calculations_done += 1
                self._cache_result(file_path, result)
                return result
        except Exception as e:
            logger.error(f"Sync entropy calculation error: {e}")
        
        return None
    
    def _check_cache(self, file_path: str) -> Optional[Dict]:
        """Check if result is in cache and still valid"""
        with self.lock:
            if file_path in self.cache:
                timestamp, result = self.cache[file_path]
                if time.time() - timestamp < self.cache_ttl:
                    return result
                else:
                    # Remove expired entry
                    del self.cache[file_path]
        
        return None
    
    def _cache_result(self, file_path: str, result: Dict):
        """Cache calculation result"""
        with self.lock:
            self.cache[file_path] = (time.time(), result)
            
            # Limit cache size (keep most recent 500 entries)
            if len(self.cache) > 500:
                # Remove oldest 100 entries
                sorted_items = sorted(self.cache.items(), key=lambda x: x[1][0])
                for i in range(100):
                    del self.cache[sorted_items[i][0]]
    
    def clear_cache(self):
        """Clear all cached results"""
        with self.lock:
            self.cache.clear()
        logger.info("Entropy cache cleared")
    
    def get_stats(self) -> Dict:
        """Get performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': f"{hit_rate:.2f}%",
            'calculations_done': self.calculations_done,
            'timeouts': self.timeouts,
            'cache_size': len(self.cache)
        }
    
    def shutdown(self):
        """Shutdown executor gracefully"""
        self.executor.shutdown(wait=True)
        logger.info(f"AsyncEntropyCalculator shutdown. Stats: {self.get_stats()}")


def _calculate_file_metrics(file_path: str) -> Optional[Dict]:
    """
    Calculate entropy and hash for a file (runs in worker process).
    Smart sampling for large files to maintain performance.
    
    Args:
        file_path: Path to file
    
    Returns:
        Dict with entropy, hash, size, etc.
    """
    try:
        import os
        
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        
        # Strategy: Sample large files instead of reading entirely
        # For files > 10MB, sample first 1MB + middle 1MB + last 1MB
        if file_size > 10 * 1024 * 1024:  # 10MB
            return _calculate_sampled_metrics(file_path, file_size)
        else:
            return _calculate_full_metrics(file_path, file_size)
    
    except Exception as e:
        logger.error(f"Error calculating metrics for {file_path}: {e}")
        return None


def _calculate_full_metrics(file_path: str, file_size: int) -> Dict:
    """Calculate full metrics for small/medium files"""
    sha256_hash = hashlib.sha256()
    byte_frequencies = [0] * 256
    bytes_read = 0
    
    with open(file_path, "rb") as f:
        # Read in chunks
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            bytes_read += len(chunk)
            
            # Count byte frequencies for entropy
            for byte in chunk:
                byte_frequencies[byte] += 1
    
    # Calculate Shannon entropy
    entropy = 0.0
    if bytes_read > 0:
        for freq in byte_frequencies:
            if freq > 0:
                probability = freq / bytes_read
                entropy -= probability * math.log2(probability)
    
    return {
        'entropy': round(entropy, 4),
        'hash': sha256_hash.hexdigest(),
        'size': file_size,
        'sampled': False,
        'bytes_analyzed': bytes_read
    }


def _calculate_sampled_metrics(file_path: str, file_size: int) -> Dict:
    """
    Calculate metrics using smart sampling for large files.
    Samples: First 1MB + Middle 1MB + Last 1MB
    """
    sha256_hash = hashlib.sha256()
    byte_frequencies = [0] * 256
    sample_size = 1024 * 1024  # 1MB per sample
    bytes_analyzed = 0
    
    with open(file_path, "rb") as f:
        # Sample 1: First 1MB
        chunk = f.read(sample_size)
        sha256_hash.update(chunk)
        bytes_analyzed += len(chunk)
        for byte in chunk:
            byte_frequencies[byte] += 1
        
        # Sample 2: Middle 1MB
        if file_size > sample_size * 2:
            middle_pos = (file_size - sample_size) // 2
            f.seek(middle_pos)
            chunk = f.read(sample_size)
            sha256_hash.update(chunk)
            bytes_analyzed += len(chunk)
            for byte in chunk:
                byte_frequencies[byte] += 1
        
        # Sample 3: Last 1MB
        if file_size > sample_size:
            f.seek(max(0, file_size - sample_size))
            chunk = f.read(sample_size)
            sha256_hash.update(chunk)
            bytes_analyzed += len(chunk)
            for byte in chunk:
                byte_frequencies[byte] += 1
    
    # Calculate Shannon entropy
    entropy = 0.0
    if bytes_analyzed > 0:
        for freq in byte_frequencies:
            if freq > 0:
                probability = freq / bytes_analyzed
                entropy -= probability * math.log2(probability)
    
    return {
        'entropy': round(entropy, 4),
        'hash': sha256_hash.hexdigest(),
        'size': file_size,
        'sampled': True,
        'bytes_analyzed': bytes_analyzed,
        'sample_percentage': round((bytes_analyzed / file_size) * 100, 2)
    }


# Global instance
_entropy_calculator = None


def get_entropy_calculator(max_workers: int = 4, cache_ttl: int = 300) -> AsyncEntropyCalculator:
    """Get or create global entropy calculator instance"""
    global _entropy_calculator
    
    if _entropy_calculator is None:
        _entropy_calculator = AsyncEntropyCalculator(
            max_workers=max_workers,
            cache_ttl=cache_ttl
        )
    
    return _entropy_calculator
