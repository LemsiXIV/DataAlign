# Docker Temp File Fix - Summary

## Problem Identified
The Excel export was showing incorrect data (1004 for all sections) because:

1. **System Temp Directory Issue**: The application was using Python's `tempfile.NamedTemporaryFile()` which creates files in `/tmp` inside the Docker container
2. **Non-Persistent Storage**: The `/tmp` directory is NOT mounted as a volume in Docker, so files can be lost or corrupted
3. **Data Corruption**: Between comparison and download, the pickle files containing comparison results were getting corrupted or lost

## Docker Configuration Analysis
From `docker-compose.yml`:
```yaml
volumes:
  - uploads_data:/app/uploads    # ✅ Persistent
  - temp_data:/app/temp         # ✅ Persistent 
```

But Python's `tempfile` was using `/tmp` which is NOT persistent.

## Fix Applied
Changed in `app/routes/comparaison.py`:

### Before (Problematic):
```python
temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl')
# Creates files in /tmp (non-persistent)
```

### After (Fixed):
```python
# Use app/temp directory which is mounted as a volume in Docker
temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
os.makedirs(temp_dir, exist_ok=True)

# Generate unique filename
temp_filename = f"comparison_results_{uuid.uuid4().hex}.pkl"
temp_path = os.path.join(temp_dir, temp_filename)

# Write pickle file to persistent temp directory
with open(temp_path, 'wb') as temp_file:
    pickle.dump(temp_results, temp_file)
```

## Additional Improvements
1. **Cleanup Function**: Added `cleanup_old_temp_files()` to prevent disk space issues
2. **Unique Filenames**: Using UUID to prevent filename conflicts
3. **Error Handling**: Better file operations with explicit open/close

## Testing Instructions

### 1. Restart Docker Container
```bash
docker-compose down
docker-compose up -d
```

### 2. Test Comparison & Excel Export
1. Upload two CSV files
2. Run comparison
3. Verify web results show correct statistics
4. Download Excel file
5. Check that Excel contains the same statistics as web display

### 3. Expected Results
- Web display: Correct statistics (e.g., 250 écarts fichier 1, 180 écarts fichier 2, 1200 communs)
- Excel download: SAME statistics as web display (not 1004 for everything)

## Files Changed
- `app/routes/comparaison.py`: Fixed temp file handling in both `compare()` and `fast_compare()` functions

## Why This Fixes The Issue
1. **Persistent Storage**: Temp files now stored in `/app/temp` which is mounted as `temp_data` volume
2. **Data Integrity**: Files persist between HTTP requests and container operations
3. **No Data Loss**: Comparison results are safely stored until download is complete
4. **Cleanup**: Old files are automatically removed to prevent disk space issues

## Verification
After applying this fix, the Excel export should contain the exact same data counts as displayed on the web interface, resolving the "1004" issue completely.
