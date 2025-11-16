#!/usr/bin/env python3
"""
Demo script for Lidar3D - creates a sample 3D model from synthetic LiDAR data.
This demonstrates the complete workflow without requiring real IGN LiDAR data.
"""
import sys
import logging
from pathlib import Path
import numpy as np
import tempfile
import shutil

# Setup path
sys.path.insert(0, str(Path(__file__).parent))

from lidar3d.utils.config import Config
from lidar3d.pipeline import Lidar3DPipeline
from tests.test_utils import create_sample_las_file

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_demo():
    """Create a complete demo showing all capabilities."""
    
    logger.info("=" * 70)
    logger.info("Lidar3D Demo - LiDAR to 3DS Conversion")
    logger.info("=" * 70)
    
    # Create temporary directory for demo
    demo_dir = Path(tempfile.mkdtemp(prefix='lidar3d_demo_'))
    logger.info(f"Demo directory: {demo_dir}")
    
    try:
        # Step 1: Create sample LiDAR data
        logger.info("\n[Step 1/5] Creating sample LiDAR data...")
        las_file = demo_dir / "sample_lidar.las"
        create_sample_las_file(str(las_file), num_points=2000)
        logger.info(f"  ✓ Created LiDAR file: {las_file}")
        logger.info(f"  ✓ File size: {las_file.stat().st_size / 1024:.1f} KB")
        
        # Step 2: Configure pipeline
        logger.info("\n[Step 2/5] Configuring processing pipeline...")
        config = Config()
        config.set('input.lidar_file', str(las_file))
        # Use a very small bbox to avoid long OSM queries
        config.set('input.osm_bbox', [48.8566, 2.3522, 48.8567, 2.3523])
        
        output_file = demo_dir / "output_model.3ds"
        config.set('output.file', str(output_file))
        config.set('output.texture_file', 'model_texture.png')
        config.set('output.texture_size', 1024)
        
        config.set('processing.point_cloud_downsample', 1.5)
        config.set('processing.mesh_method', 'poisson')
        config.set('processing.remove_outliers', False)
        config.set('processing.simplify_mesh', False)
        
        logger.info("  ✓ Configuration complete")
        logger.info(f"  ✓ Input: {las_file.name}")
        logger.info(f"  ✓ Output: {output_file.name}")
        logger.info(f"  ✓ Texture size: {config.get('output.texture_size')}x{config.get('output.texture_size')}")
        
        # Step 3: Run pipeline
        logger.info("\n[Step 3/5] Running processing pipeline...")
        logger.info("  → Loading LiDAR data...")
        logger.info("  → Loading OSM data (may timeout, which is OK for demo)...")
        logger.info("  → Processing point cloud...")
        logger.info("  → Generating mesh...")
        logger.info("  → Creating textures...")
        logger.info("  → Exporting to 3DS...")
        
        pipeline = Lidar3DPipeline(config)
        success = pipeline.run()
        
        if not success:
            logger.error("  ✗ Pipeline failed")
            return False
        
        logger.info("  ✓ Pipeline completed successfully!")
        
        # Step 4: Verify outputs
        logger.info("\n[Step 4/5] Verifying outputs...")
        
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            logger.info(f"  ✓ 3DS file created: {output_file.name} ({size_kb:.1f} KB)")
        else:
            logger.error(f"  ✗ 3DS file not found: {output_file}")
            return False
        
        texture_file = output_file.parent / config.get('output.texture_file')
        if texture_file.exists():
            size_kb = texture_file.stat().st_size / 1024
            logger.info(f"  ✓ Texture created: {texture_file.name} ({size_kb:.1f} KB)")
        else:
            logger.warning(f"  ! Texture file not found: {texture_file}")
        
        # Step 5: Summary
        logger.info("\n[Step 5/5] Demo Summary")
        logger.info("  " + "=" * 60)
        logger.info(f"  Input LiDAR points:    2000")
        logger.info(f"  Output 3DS file:       {output_file}")
        logger.info(f"  Texture file:          {texture_file}")
        logger.info(f"  Demo directory:        {demo_dir}")
        logger.info("  " + "=" * 60)
        
        logger.info("\n✓ Demo completed successfully!")
        logger.info(f"\nOutput files are in: {demo_dir}")
        logger.info("You can import the .3ds file into Blender, 3ds Max, or other 3D software.")
        
        # Keep the demo files for inspection
        logger.info(f"\nNote: Demo files will remain at {demo_dir}")
        logger.info("      Delete this directory when you're done exploring the outputs.")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    try:
        success = create_demo()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("\nDemo interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
