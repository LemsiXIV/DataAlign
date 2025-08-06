"""
Memory management utilities for handling large files efficiently
"""
import gc
import psutil
import os
from typing import Optional
import pandas as pd

class MemoryManager:
    """Utility class for managing memory usage during file operations"""
    
    @staticmethod
    def get_memory_usage() -> dict:
        """Get current memory usage statistics"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': process.memory_percent(),       # Percentage of system memory
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    @staticmethod
    def check_memory_threshold(threshold_percent: float = 80.0) -> bool:
        """Check if memory usage is above threshold"""
        memory_info = MemoryManager.get_memory_usage()
        return memory_info['percent'] > threshold_percent
    
    @staticmethod
    def force_garbage_collection():
        """Force garbage collection to free memory"""
        gc.collect()
    
    @staticmethod
    def optimize_dataframe_memory(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage by downcasting numeric types"""
        original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        # Optimize numeric columns
        for col in df.select_dtypes(include=['int64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='integer')
        
        for col in df.select_dtypes(include=['float64']).columns:
            df[col] = pd.to_numeric(df[col], downcast='float')
        
        # Optimize object columns (strings)
        for col in df.select_dtypes(include=['object']).columns:
            if df[col].nunique() / len(df) < 0.5:  # If less than 50% unique values
                df[col] = df[col].astype('category')
        
        optimized_memory = df.memory_usage(deep=True).sum() / 1024 / 1024
        
        print(f"Memory optimization: {original_memory:.2f} MB → {optimized_memory:.2f} MB "
              f"(saved {original_memory - optimized_memory:.2f} MB)")
        
        return df
    
    @staticmethod
    def estimate_comparison_memory(file1_rows: int, file2_rows: int, 
                                  num_columns: int, safety_factor: float = 3.0) -> float:
        """Estimate memory required for comparison operation"""
        # Rough estimation: each cell takes ~8 bytes on average
        bytes_per_row = num_columns * 8
        
        # Memory for both files + merge operations
        estimated_mb = (file1_rows + file2_rows) * bytes_per_row * safety_factor / 1024 / 1024
        
        return estimated_mb
    
    @staticmethod
    def should_use_chunking(file1_info: dict, file2_info: dict, 
                           available_memory_mb: Optional[float] = None) -> bool:
        """Determine if chunking should be used based on file size and available memory"""
        if available_memory_mb is None:
            available_memory_mb = MemoryManager.get_memory_usage()['available_mb']
        
        total_rows = file1_info['total_rows'] + file2_info['total_rows']
        max_columns = max(file1_info['total_columns'], file2_info['total_columns'])
        
        estimated_memory = MemoryManager.estimate_comparison_memory(
            file1_info['total_rows'], file2_info['total_rows'], max_columns
        )
        
        # Use chunking if estimated memory > 50% of available memory
        # or if files are very large regardless of memory
        return (estimated_memory > available_memory_mb * 0.5 or 
                total_rows > 50000 or 
                max_columns > 200)

class ChunkProcessor:
    """Process data in chunks to manage memory efficiently"""
    
    def __init__(self, chunk_size: int = 5000):
        self.chunk_size = chunk_size
        self.memory_manager = MemoryManager()
    
    def process_with_memory_monitoring(self, process_func, *args, **kwargs):
        """Execute a function while monitoring memory usage"""
        initial_memory = self.memory_manager.get_memory_usage()
        print(f"Initial memory usage: {initial_memory['rss_mb']:.2f} MB")
        
        try:
            result = process_func(*args, **kwargs)
            
            final_memory = self.memory_manager.get_memory_usage()
            memory_increase = final_memory['rss_mb'] - initial_memory['rss_mb']
            
            print(f"Final memory usage: {final_memory['rss_mb']:.2f} MB "
                  f"(+{memory_increase:.2f} MB)")
            
            # Force garbage collection if memory usage is high
            if final_memory['percent'] > 70:
                self.memory_manager.force_garbage_collection()
                gc_memory = self.memory_manager.get_memory_usage()
                print(f"After garbage collection: {gc_memory['rss_mb']:.2f} MB")
            
            return result
            
        except MemoryError as e:
            print("Memory error occurred. Attempting garbage collection...")
            self.memory_manager.force_garbage_collection()
            raise e
    
    def adaptive_chunk_size(self, total_rows: int, available_memory_mb: float) -> int:
        """Calculate optimal chunk size based on available memory"""
        # Aim to use no more than 25% of available memory per chunk
        target_memory_mb = available_memory_mb * 0.25
        
        # Rough estimate: 1000 rows with 100 columns ≈ 1 MB
        estimated_chunk_size = int(target_memory_mb * 1000 / 100)
        
        # Bounds checking
        min_chunk = 1000
        max_chunk = 10000
        
        optimal_chunk = max(min_chunk, min(max_chunk, estimated_chunk_size))
        
        print(f"Calculated optimal chunk size: {optimal_chunk} rows "
              f"(target memory: {target_memory_mb:.1f} MB)")
        
        return optimal_chunk
