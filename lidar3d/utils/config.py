"""
Configuration management utilities.
"""
import logging
from pathlib import Path
from typing import Any, Dict
import yaml

logger = logging.getLogger(__name__)


class Config:
    """Configuration management."""
    
    DEFAULT_CONFIG = {
        'input': {
            'lidar_file': None,
            'osm_bbox': None,  # [lat_min, lon_min, lat_max, lon_max]
        },
        'output': {
            'file': 'output.3ds',
            'texture_file': 'texture.png',
            'texture_size': 2048,
        },
        'processing': {
            'point_cloud_downsample': 0.5,
            'mesh_resolution': 1.0,
            'mesh_method': 'poisson',  # 'poisson' or 'ball_pivoting'
            'texture_quality': 'high',
            'remove_outliers': True,
            'simplify_mesh': False,
            'target_triangles': 100000,
        },
        'logging': {
            'level': 'INFO',
        }
    }
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """
        Initialize configuration.
        
        Args:
            config_dict: Configuration dictionary (uses defaults if None)
        """
        import copy
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        if config_dict:
            self._update_recursive(self.config, config_dict)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Config':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Config instance
        """
        try:
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            return cls(config_dict)
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            return cls()
    
    def _update_recursive(self, base: dict, update: dict):
        """Recursively update configuration dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._update_recursive(base[key], value)
            else:
                base[key] = value
    
    def get(self, path: str, default: Any = None) -> Any:
        """
        Get configuration value by path.
        
        Args:
            path: Dot-separated path (e.g., 'input.lidar_file')
            default: Default value if path not found
            
        Returns:
            Configuration value
        """
        keys = path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, path: str, value: Any):
        """
        Set configuration value by path.
        
        Args:
            path: Dot-separated path (e.g., 'input.lidar_file')
            value: Value to set
        """
        keys = path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not self.get('input.lidar_file'):
            logger.error("Missing required field: input.lidar_file")
            return False
        
        if not self.get('input.osm_bbox'):
            logger.error("Missing required field: input.osm_bbox")
            return False
        
        # Validate OSM bbox format
        bbox = self.get('input.osm_bbox')
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            logger.error("OSM bbox must be [lat_min, lon_min, lat_max, lon_max]")
            return False
        
        return True
    
    def save(self, config_path: str) -> bool:
        """
        Save configuration to YAML file.
        
        Args:
            config_path: Path to save configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {e}")
            return False
