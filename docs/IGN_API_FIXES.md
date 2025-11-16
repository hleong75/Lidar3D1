# IGN WFS API Fixes and Troubleshooting

## Issue Description

Users were experiencing 400 Bad Request errors when attempting to download LiDAR data from IGN's WFS service:

```
2025-11-16 18:59:25,422 - lidar3d.loaders.ign_downloader - ERROR - Failed to query IGN WFS service: 
400 Client Error: Bad Request for url: https://data.geopf.fr/wfs?...
```

## Root Causes

The 400 error can occur due to several reasons:

1. **Layer Name Changes**: IGN periodically updates layer names as their data products evolve
2. **WFS Version Compatibility**: Some endpoints require specific WFS versions
3. **Parameter Format**: Different WFS versions use different parameter names
4. **Output Format**: Some servers are strict about output format specifications

## Solution

The downloader now implements a robust fallback mechanism that tries multiple configurations automatically:

### 1. Multiple Layer Names

The downloader attempts these layer names in order:

```python
LIDAR_LAYERS = [
    "LIDARHD_FXX_1-0:dalles",  # Updated layer for France-wide coverage
    "LIDARHD_1-0:dalles",       # Original layer name
    "LIDARHD:dalles",           # Simplified version
]
```

### 2. WFS Version Fallback

**WFS 2.0.0** (tried first):
```python
{
    'service': 'WFS',
    'version': '2.0.0',
    'request': 'GetFeature',
    'typeNames': 'LIDARHD_FXX_1-0:dalles',  # Plural!
    'outputFormat': 'application/json',
    'bbox': '2.35,48.85,2.36,48.86,EPSG:4326',
    'count': 1000  # WFS 2.0.0 parameter
}
```

**WFS 1.1.0** (fallback):
```python
{
    'service': 'WFS',
    'version': '1.1.0',
    'request': 'GetFeature',
    'typeName': 'LIDARHD_FXX_1-0:dalles',  # Singular!
    'outputFormat': 'application/json',
    'bbox': '2.35,48.85,2.36,48.86,EPSG:4326',
    'maxFeatures': 1000  # WFS 1.1.0 parameter
}
```

### 3. Output Format Variations

Tries multiple format specifications:
- `application/json` (standard MIME type)
- `json` (simplified)

### 4. Property Name Flexibility

Handles various property name conventions:

| Expected Property | Fallback Names |
|------------------|----------------|
| `url_telech` | `url_telechargement`, `url` |
| `nom_dalle` | `nom` |
| `date_vol` | `date` |
| `projet` | `project` |

## How It Works

The downloader attempts up to 7 different configurations:

1. Try each layer name with WFS 2.0.0 + `application/json` (3 attempts)
2. Try each layer name with WFS 1.1.0 + `application/json` (3 attempts)
3. Try first layer name with WFS 2.0.0 + `json` (1 attempt)

Once a configuration succeeds, it's used for all subsequent requests in that session.

## Error Messages

### Before Fix
```
ERROR - Failed to query IGN WFS service: 400 Client Error: Bad Request
```

### After Fix
```
ERROR - Failed to query IGN WFS service after trying 7 configurations. 
The API may have changed or the service may be unavailable. 
Tried layer names: LIDARHD_FXX_1-0:dalles, LIDARHD_1-0:dalles, LIDARHD:dalles
```

The improved error message helps diagnose:
- How many configurations were attempted
- Which layer names were tried
- Whether it's a temporary service issue or API change

## Testing

All unit tests pass with the new implementation:

```bash
$ python -m unittest tests.loaders.test_ign_downloader -v
test_find_tiles_success ... ok
test_find_tiles_request_error ... ok
test_download_tile_success ... ok
# ... 12 tests total
OK
```

## Manual Testing

To test with the real IGN API (requires internet):

```bash
# Test automatic download
python -m lidar3d.main \
  --ign-auto-download \
  --ign-bbox "2.35,48.85,2.36,48.86" \
  --max-tiles 1 \
  --output test.3ds
```

You should see logs indicating which configuration succeeded:

```
INFO - Searching for LiDAR HD tiles in bbox: [2.35, 48.85, 2.36, 48.86]
DEBUG - Trying WFS configuration 1/7
INFO - Successfully connected with configuration 1
INFO - Found X LiDAR HD tiles
```

## Troubleshooting

### Still Getting 400 Errors?

1. **Check Internet Connection**: Ensure you can reach `data.geopf.fr`
   ```bash
   curl -I https://data.geopf.fr/wfs
   ```

2. **Verify Bounding Box**: Ensure coordinates are in France
   - France longitude: approximately -5 to 10
   - France latitude: approximately 41 to 51

3. **Check IGN Service Status**: Visit https://geoservices.ign.fr/ for service announcements

4. **Enable Debug Logging**: Get detailed request information
   ```bash
   python -m lidar3d.main --log-level DEBUG ...
   ```

### Network Timeout

If requests timeout, increase the timeout in `ign_downloader.py`:

```python
response = requests.get(self.WFS_BASE_URL, params=params, timeout=60)  # Increase from 30
```

### No Tiles Found

If the API works but returns no tiles:
- The area may not have LiDAR coverage yet
- Try a larger bounding box
- Check IGN's coverage map: https://geoservices.ign.fr/lidarhd

## Future Improvements

1. **Cache Working Configuration**: Save successful config to avoid retries
2. **Capabilities Discovery**: Query WFS GetCapabilities to find correct layer names
3. **User Configuration**: Allow users to override layer names in config file
4. **API Version Detection**: Auto-detect the correct WFS version

## References

- IGN GeoPF Services: https://geoservices.ign.fr/
- WFS 2.0.0 Specification: https://www.ogc.org/standards/wfs
- LIDAR HD Documentation: https://geoservices.ign.fr/lidarhd
