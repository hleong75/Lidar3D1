#!/usr/bin/env python3
"""
Demo script showing automatic IGN LiDAR data download.

This demonstrates the new automatic download feature without requiring
network access (uses mock data for demonstration).
"""
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Demonstrate automatic download feature."""
    
    logger.info("=" * 70)
    logger.info("IGN Automatic Download Feature Demo")
    logger.info("=" * 70)
    
    logger.info("""
    
NEW FEATURE: Automatic IGN LiDAR HD Data Download
==================================================

The program can now automatically download LiDAR HD data from IGN!

USAGE EXAMPLES:
---------------

1. Basic automatic download:
   
   python -m lidar3d.main \\
     --ign-auto-download \\
     --ign-bbox "2.35,48.85,2.36,48.86" \\
     --output model.3ds


2. Limit number of tiles:
   
   python -m lidar3d.main \\
     --ign-auto-download \\
     --ign-bbox "2.35,48.85,2.36,48.86" \\
     --max-tiles 5 \\
     --output model.3ds


3. High quality with automatic download:
   
   python -m lidar3d.main \\
     --ign-auto-download \\
     --ign-bbox "2.35,48.85,2.36,48.86" \\
     --texture-size 4096 \\
     --downsample 0.2 \\
     --output high_quality.3ds


HOW IT WORKS:
-------------

1. You provide a geographic bounding box (lon_min, lat_min, lon_max, lat_max)
2. The program queries IGN's WFS service to find available LiDAR tiles
3. LAZ files are automatically downloaded to a temporary directory
4. If multiple tiles are found, they can be merged automatically
5. The processing pipeline continues normally with the downloaded data


BBOX FORMAT:
------------

--ign-bbox uses: lon_min,lat_min,lon_max,lat_max
                 (longitude first!)

Example for Paris center:
  --ign-bbox "2.35,48.85,2.36,48.86"
  
  Where:
    2.35  = minimum longitude (west)
    48.85 = minimum latitude (south)
    2.36  = maximum longitude (east)
    48.86 = maximum latitude (north)


BENEFITS:
---------

✓ No need to manually download files from IGN website
✓ Automatically finds correct tiles for your area of interest
✓ Downloads only necessary data
✓ Can limit number of tiles to control processing time
✓ Works seamlessly with existing pipeline


BACKWARD COMPATIBILITY:
-----------------------

The original manual file mode still works:

  python -m lidar3d.main \\
    --input my_file.laz \\
    --osm-bbox "48.85,2.35,48.86,2.36" \\
    --output model.3ds


REQUIREMENTS:
-------------

✓ Internet connection to access IGN services
✓ Valid geographic coordinates for France
✓ Sufficient disk space for downloaded tiles
  (tiles are typically 5-50 MB each)

    """)
    
    logger.info("=" * 70)
    logger.info("To test the feature with real data, run:")
    logger.info("")
    logger.info("  python -m lidar3d.main \\")
    logger.info("    --ign-auto-download \\")
    logger.info("    --ign-bbox \"2.35,48.85,2.36,48.86\" \\")
    logger.info("    --max-tiles 3 \\")
    logger.info("    --output test_model.3ds")
    logger.info("")
    logger.info("=" * 70)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
