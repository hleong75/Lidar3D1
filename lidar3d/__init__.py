"""
Lidar3D - LiDAR to 3DS Converter

A robust Python application for converting LiDAR HD data and OpenStreetMap 
data into high-quality 3DS files with textures.
"""

__version__ = "1.0.0"
__author__ = "Lidar3D Team"

from lidar3d.pipeline import Lidar3DPipeline
from lidar3d.utils.config import Config

__all__ = ["Lidar3DPipeline", "Config"]
