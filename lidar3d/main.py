"""
Main entry point for Lidar3D application.
"""
import argparse
import logging
import sys
from pathlib import Path

from lidar3d.utils.config import Config
from lidar3d.pipeline import Lidar3DPipeline


def setup_logging(level: str = 'INFO'):
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert LiDAR HD data and OSM to 3DS format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with command line arguments
  python -m lidar3d.main --input data.laz --osm-bbox "48.8566,2.3522,48.8606,2.3562" --output output.3ds
  
  # Using a configuration file
  python -m lidar3d.main --config config.yaml
  
  # Generate example configuration
  python -m lidar3d.main --generate-config example_config.yaml
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to YAML configuration file'
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        help='Path to input LiDAR file (LAS/LAZ format)'
    )
    
    parser.add_argument(
        '--osm-bbox',
        type=str,
        help='OSM bounding box as "lat_min,lon_min,lat_max,lon_max"'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Path to output 3DS file'
    )
    
    parser.add_argument(
        '--texture-size',
        type=int,
        default=2048,
        help='Texture size in pixels (default: 2048)'
    )
    
    parser.add_argument(
        '--downsample',
        type=float,
        default=0.5,
        help='Point cloud downsample voxel size (default: 0.5)'
    )
    
    parser.add_argument(
        '--mesh-method',
        choices=['poisson', 'ball_pivoting'],
        default='poisson',
        help='Mesh generation method (default: poisson)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--generate-config',
        type=str,
        metavar='FILE',
        help='Generate example configuration file and exit'
    )
    
    return parser.parse_args()


def generate_example_config(output_path: str) -> bool:
    """
    Generate an example configuration file.
    
    Args:
        output_path: Path to save the example config
        
    Returns:
        True if successful
    """
    config = Config()
    
    # Set example values
    config.set('input.lidar_file', 'path/to/lidar_data.laz')
    config.set('input.osm_bbox', [48.8566, 2.3522, 48.8606, 2.3562])
    config.set('output.file', 'output.3ds')
    config.set('output.texture_file', 'texture.png')
    config.set('output.texture_size', 2048)
    config.set('processing.point_cloud_downsample', 0.5)
    config.set('processing.mesh_resolution', 1.0)
    config.set('processing.mesh_method', 'poisson')
    config.set('processing.texture_quality', 'high')
    config.set('processing.remove_outliers', True)
    config.set('processing.simplify_mesh', False)
    config.set('processing.target_triangles', 100000)
    
    if config.save(output_path):
        print(f"Example configuration saved to {output_path}")
        return True
    else:
        print(f"Failed to save configuration to {output_path}")
        return False


def main():
    """Main function."""
    args = parse_arguments()
    
    # Generate config if requested
    if args.generate_config:
        return 0 if generate_example_config(args.generate_config) else 1
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Load or create configuration
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config = Config.from_file(args.config)
        else:
            logger.info("Using command line arguments")
            config = Config()
            
            # Set values from command line
            if args.input:
                config.set('input.lidar_file', args.input)
            
            if args.osm_bbox:
                # Parse bbox string
                try:
                    bbox = [float(x.strip()) for x in args.osm_bbox.split(',')]
                    if len(bbox) != 4:
                        raise ValueError()
                    config.set('input.osm_bbox', bbox)
                except:
                    logger.error("Invalid OSM bbox format. Use: lat_min,lon_min,lat_max,lon_max")
                    return 1
            
            if args.output:
                config.set('output.file', args.output)
            
            config.set('output.texture_size', args.texture_size)
            config.set('processing.point_cloud_downsample', args.downsample)
            config.set('processing.mesh_method', args.mesh_method)
        
        # Validate configuration
        if not config.validate():
            logger.error("Configuration validation failed")
            return 1
        
        # Create output directory if needed
        output_file = Path(config.get('output.file'))
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Run pipeline
        logger.info("Starting Lidar3D processing pipeline")
        pipeline = Lidar3DPipeline(config)
        
        if pipeline.run():
            logger.info("Pipeline completed successfully!")
            return 0
        else:
            logger.error("Pipeline failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
