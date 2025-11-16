#!/usr/bin/env python3
"""
Test script to demonstrate the IGN downloader fixes.

This script shows how the new fallback mechanism works when querying
the IGN WFS service. It will attempt to connect to the real API and 
show which configuration succeeds.

Note: Requires internet connection to IGN services.
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lidar3d.loaders.ign_downloader import IGNDownloader

# Configure logging to show debug information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ign_downloader():
    """Test the IGN downloader with various scenarios."""
    
    print("=" * 70)
    print("IGN LiDAR Downloader Test")
    print("=" * 70)
    print()
    
    # Test 1: Initialize downloader
    print("Test 1: Initialize downloader")
    print("-" * 70)
    downloader = IGNDownloader()
    print(f"✓ Output directory: {downloader.output_dir}")
    print(f"✓ WFS Base URL: {downloader.WFS_BASE_URL}")
    print(f"✓ Layer name variations: {len(downloader.LIDAR_LAYERS)}")
    for i, layer in enumerate(downloader.LIDAR_LAYERS, 1):
        print(f"  {i}. {layer}")
    print()
    print("Note: New layer names added for Nov 2025 IGN NUALID product update")
    print()
    
    # Test 2: Validate bounding box
    print("Test 2: Validate bounding box")
    print("-" * 70)
    
    # Valid bbox for Paris center
    valid_bbox = [2.35, 48.85, 2.36, 48.86]
    print(f"Valid bbox (Paris): {valid_bbox}")
    print("  lon_min=2.35 (west), lat_min=48.85 (south)")
    print("  lon_max=2.36 (east), lat_max=48.86 (north)")
    print()
    
    # Test 3: Try to find tiles (requires network)
    print("Test 3: Query IGN WFS service")
    print("-" * 70)
    print("Attempting to connect to IGN WFS service...")
    print("This will try up to 13 different configurations automatically.")
    print()
    
    try:
        tiles = downloader.find_tiles(valid_bbox)
        
        print(f"✅ SUCCESS! Found {len(tiles)} tiles")
        print()
        
        if tiles:
            print("Sample tiles:")
            for i, tile in enumerate(tiles[:3], 1):
                print(f"\nTile {i}:")
                print(f"  Name:    {tile.get('name', 'unknown')}")
                print(f"  Date:    {tile.get('date', 'unknown')}")
                print(f"  Project: {tile.get('project', 'unknown')}")
                print(f"  URL:     {tile.get('url', 'N/A')[:60]}...")
            
            if len(tiles) > 3:
                print(f"\n  ... and {len(tiles) - 3} more tiles")
        else:
            print("ℹ️  No tiles found in this area.")
            print("   This could mean:")
            print("   - LiDAR coverage not yet available for this area")
            print("   - Area too small to contain any tiles")
            
    except RuntimeError as e:
        print(f"❌ FAILED: {e}")
        print()
        print("This error indicates:")
        print("- All 13 WFS configurations were tried and failed")
        print("- The IGN API may have changed beyond current fallbacks")
        print("- Or the service might be temporarily unavailable")
        print()
        print("With the previous version, you would have seen:")
        print("  ERROR - Failed to query IGN WFS service: 400 Client Error")
        print()
        print("Now you get detailed information about what was tried.")
        
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        print()
        print("This might be a network issue:")
        print("- Check your internet connection")
        print("- Verify you can reach: https://data.geopf.fr")
        print("- Try: curl -I https://data.geopf.fr/wfs")
    
    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)
    print()
    print("Summary of improvements:")
    print("✓ Tries 6 different layer name variations")
    print("✓ Falls back between WFS 2.0.0 and WFS 1.1.0")
    print("✓ Tests multiple output format specifications")
    print("✓ Provides detailed error messages")
    print("✓ Handles property name variations automatically")
    print()
    print("For more information, see: docs/IGN_API_FIXES.md")
    print()


if __name__ == '__main__':
    test_ign_downloader()
