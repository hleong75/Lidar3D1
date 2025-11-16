"""
LiDAR data loader for IGN HD LiDAR files (LAS/LAZ format).
"""
import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np

try:
    import laspy
except ImportError:
    raise ImportError("laspy is required. Install with: pip install laspy[lazrs]")

logger = logging.getLogger(__name__)


class LidarLoader:
    """Load and process LiDAR data from LAS/LAZ files."""
    
    def __init__(self, file_path: str):
        """
        Initialize the LiDAR loader.
        
        Args:
            file_path: Path to the LAS/LAZ file
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file format is invalid
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"LiDAR file not found: {file_path}")
        
        if self.file_path.suffix.lower() not in ['.las', '.laz']:
            raise ValueError(f"Invalid file format. Expected .las or .laz, got {self.file_path.suffix}")
        
        self.las_data = None
        self.points = None
        self.colors = None
        self.classifications = None
        
    def load(self) -> bool:
        """
        Load the LiDAR data from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading LiDAR data from {self.file_path}")
            self.las_data = laspy.read(str(self.file_path))
            
            # Extract coordinates
            self.points = np.vstack([
                self.las_data.x,
                self.las_data.y,
                self.las_data.z
            ]).T
            
            # Extract colors if available
            if hasattr(self.las_data, 'red') and hasattr(self.las_data, 'green') and hasattr(self.las_data, 'blue'):
                self.colors = np.vstack([
                    self.las_data.red,
                    self.las_data.green,
                    self.las_data.blue
                ]).T.astype(np.float32) / 65535.0  # Normalize to [0, 1]
            else:
                logger.warning("No color information found in LiDAR data")
                self.colors = None
            
            # Extract classification if available
            if hasattr(self.las_data, 'classification'):
                self.classifications = np.array(self.las_data.classification)
            else:
                self.classifications = None
            
            logger.info(f"Loaded {len(self.points)} points from LiDAR data")
            return True
            
        except Exception as e:
            logger.error(f"Error loading LiDAR data: {e}")
            return False
    
    def get_points(self) -> Optional[np.ndarray]:
        """
        Get point coordinates.
        
        Returns:
            Nx3 array of [x, y, z] coordinates, or None if not loaded
        """
        return self.points
    
    def get_colors(self) -> Optional[np.ndarray]:
        """
        Get point colors.
        
        Returns:
            Nx3 array of [r, g, b] colors in [0, 1] range, or None if not available
        """
        return self.colors
    
    def get_classifications(self) -> Optional[np.ndarray]:
        """
        Get point classifications.
        
        Returns:
            N array of classification codes, or None if not available
        """
        return self.classifications
    
    def get_bounds(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get bounding box of the point cloud.
        
        Returns:
            Tuple of (min_bounds, max_bounds) as 3D arrays, or None if not loaded
        """
        if self.points is None:
            return None
        return np.min(self.points, axis=0), np.max(self.points, axis=0)
    
    def filter_by_classification(self, classification_codes: list) -> np.ndarray:
        """
        Filter points by classification codes.
        
        Args:
            classification_codes: List of classification codes to keep
            
        Returns:
            Boolean mask for points matching the classification
        """
        if self.classifications is None:
            logger.warning("No classification data available")
            return np.ones(len(self.points), dtype=bool)
        
        mask = np.isin(self.classifications, classification_codes)
        logger.info(f"Filtered {np.sum(mask)} points with classifications {classification_codes}")
        return mask
    
    def get_ground_points(self) -> Optional[np.ndarray]:
        """
        Get ground points (classification code 2).
        
        Returns:
            Nx3 array of ground points, or None if not available
        """
        if self.points is None or self.classifications is None:
            return None
        
        mask = self.classifications == 2
        return self.points[mask]
    
    def get_building_points(self) -> Optional[np.ndarray]:
        """
        Get building points (classification code 6).
        
        Returns:
            Nx3 array of building points, or None if not available
        """
        if self.points is None or self.classifications is None:
            return None
        
        mask = self.classifications == 6
        return self.points[mask]
