"""
Main processing pipeline for LiDAR to 3DS conversion.
"""
import logging
from pathlib import Path
from typing import Optional
import numpy as np

from lidar3d.loaders.lidar_loader import LidarLoader
from lidar3d.loaders.osm_loader import OSMLoader
from lidar3d.processors.point_cloud import PointCloudProcessor
from lidar3d.textures.texture_generator import TextureGenerator
from lidar3d.exporters.threeds_exporter import ThreeDSExporter
from lidar3d.utils.config import Config

logger = logging.getLogger(__name__)


class Lidar3DPipeline:
    """Main processing pipeline for converting LiDAR and OSM data to 3DS."""
    
    def __init__(self, config: Config):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.lidar_loader = None
        self.osm_loader = None
        self.processor = None
        self.texture_gen = None
        self.exporter = None
        
    def run(self) -> bool:
        """
        Run the complete pipeline.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Starting Lidar3D pipeline")
            
            # Validate configuration
            if not self.config.validate():
                logger.error("Invalid configuration")
                return False
            
            # Step 1: Load LiDAR data
            if not self._load_lidar():
                return False
            
            # Step 2: Load OSM data
            if not self._load_osm():
                return False
            
            # Step 3: Process point cloud
            if not self._process_point_cloud():
                return False
            
            # Step 4: Generate mesh
            if not self._generate_mesh():
                return False
            
            # Step 5: Generate textures
            if not self._generate_textures():
                return False
            
            # Step 6: Export to 3DS
            if not self._export_3ds():
                return False
            
            logger.info("Pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return False
    
    def _load_lidar(self) -> bool:
        """Load LiDAR data."""
        try:
            lidar_file = self.config.get('input.lidar_file')
            logger.info(f"Loading LiDAR data from {lidar_file}")
            
            self.lidar_loader = LidarLoader(lidar_file)
            if not self.lidar_loader.load():
                logger.error("Failed to load LiDAR data")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading LiDAR: {e}")
            return False
    
    def _load_osm(self) -> bool:
        """Load OSM data."""
        try:
            bbox = self.config.get('input.osm_bbox')
            logger.info(f"Loading OSM data for bbox {bbox}")
            
            self.osm_loader = OSMLoader(tuple(bbox))
            if not self.osm_loader.load():
                logger.warning("Failed to load OSM data, continuing without it")
            
            return True
            
        except Exception as e:
            logger.warning(f"Error loading OSM data, continuing without it: {e}")
            return True  # OSM is optional, so don't fail the pipeline
    
    def _process_point_cloud(self) -> bool:
        """Process the point cloud."""
        try:
            logger.info("Processing point cloud")
            
            self.processor = PointCloudProcessor()
            
            # Get points and colors from LiDAR
            points = self.lidar_loader.get_points()
            colors = self.lidar_loader.get_colors()
            
            if points is None:
                logger.error("No points to process")
                return False
            
            # Create point cloud
            if not self.processor.create_point_cloud(points, colors):
                return False
            
            # Downsample if configured
            downsample = self.config.get('processing.point_cloud_downsample')
            if downsample and downsample > 0:
                logger.info(f"Downsampling with voxel size {downsample}")
                if not self.processor.downsample(downsample):
                    logger.warning("Downsampling failed, continuing with original")
            
            # Remove outliers if configured
            if self.config.get('processing.remove_outliers', False):
                logger.info("Removing outliers")
                if not self.processor.remove_outliers():
                    logger.warning("Outlier removal failed, continuing")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing point cloud: {e}")
            return False
    
    def _generate_mesh(self) -> bool:
        """Generate mesh from point cloud."""
        try:
            logger.info("Generating mesh")
            
            # Estimate normals first
            if not self.processor.estimate_normals():
                logger.error("Failed to estimate normals")
                return False
            
            # Choose mesh method
            method = self.config.get('processing.mesh_method', 'poisson')
            
            if method == 'poisson':
                depth = 9 if self.config.get('processing.texture_quality') == 'high' else 8
                if not self.processor.create_mesh_poisson(depth=depth):
                    logger.error("Failed to create mesh with Poisson reconstruction")
                    return False
            elif method == 'ball_pivoting':
                if not self.processor.create_mesh_ball_pivoting():
                    logger.error("Failed to create mesh with Ball Pivoting")
                    return False
            else:
                logger.error(f"Unknown mesh method: {method}")
                return False
            
            # Simplify mesh if configured
            if self.config.get('processing.simplify_mesh', False):
                target = self.config.get('processing.target_triangles', 100000)
                logger.info(f"Simplifying mesh to {target} triangles")
                if not self.processor.simplify_mesh(target):
                    logger.warning("Mesh simplification failed, continuing with original")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating mesh: {e}")
            return False
    
    def _generate_textures(self) -> bool:
        """Generate textures for the mesh."""
        try:
            logger.info("Generating textures")
            
            texture_size = self.config.get('output.texture_size', 2048)
            self.texture_gen = TextureGenerator(texture_size)
            
            # Get mesh data
            mesh_data = self.processor.get_mesh_data()
            if mesh_data is None:
                logger.error("No mesh data for texture generation")
                return False
            
            vertices, faces = mesh_data
            
            # Get colors from LiDAR if available
            colors = self.lidar_loader.get_colors()
            
            # Try to match colors to mesh vertices if we have colors
            if colors is not None and len(colors) > 0:
                # For simplicity, use procedural textures with OSM data
                # In a more advanced version, we would properly transfer colors
                osm_data = {
                    'buildings': self.osm_loader.get_buildings() if self.osm_loader else [],
                    'roads': self.osm_loader.get_roads() if self.osm_loader else [],
                }
                if not self.texture_gen.create_procedural_texture(vertices, faces, osm_data):
                    logger.warning("Failed to create procedural texture, using default")
                    self.texture_gen.create_default_texture()
            else:
                # No colors, create default texture
                logger.info("No color data, creating default texture")
                self.texture_gen.create_default_texture()
            
            # Save texture
            texture_file = self.config.get('output.texture_file', 'texture.png')
            output_dir = Path(self.config.get('output.file')).parent
            texture_path = output_dir / texture_file
            
            if not self.texture_gen.save_texture(str(texture_path)):
                logger.error("Failed to save texture")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating textures: {e}")
            return False
    
    def _export_3ds(self) -> bool:
        """Export to 3DS format."""
        try:
            logger.info("Exporting to 3DS")
            
            self.exporter = ThreeDSExporter()
            
            # Get mesh data
            mesh_data = self.processor.get_mesh_data()
            if mesh_data is None:
                logger.error("No mesh data to export")
                return False
            
            vertices, faces = mesh_data
            
            # Get UV coordinates
            uv_coords = self.texture_gen.get_uv_coords()
            
            # Set mesh data
            self.exporter.set_mesh_data(vertices, faces, uv_coords)
            
            # Set texture
            texture_file = self.config.get('output.texture_file', 'texture.png')
            output_dir = Path(self.config.get('output.file')).parent
            texture_path = output_dir / texture_file
            self.exporter.set_texture(str(texture_path))
            
            # Export
            output_file = self.config.get('output.file')
            if not self.exporter.export(output_file):
                logger.error("Failed to export to 3DS")
                return False
            
            logger.info(f"Successfully exported to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to 3DS: {e}")
            return False
