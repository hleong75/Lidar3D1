"""
IGN LiDAR HD automatic downloader.

This module handles automatic downloading of LiDAR HD data from IGN (Institut 
national de l'information géographique et forestière) based on a bounding box.
"""
import logging
import os
from pathlib import Path
from typing import List, Tuple, Optional
import requests
from xml.etree import ElementTree as ET
import tempfile

logger = logging.getLogger(__name__)


class IGNDownloader:
    """
    Download LiDAR HD data from IGN based on geographic bounding box.
    
    The IGN provides LiDAR HD data in 1km x 1km tiles via WFS service.
    This class queries available tiles and downloads the LAZ files.
    """
    
    # Public WFS endpoint (no API key required for basic access)
    WFS_BASE_URL = "https://data.geopf.fr/wfs"
    
    # Layer names to try (IGN sometimes updates these)
    # Try multiple variations to handle API changes
    # Based on IGN's evolving API and product naming (Nov 2025 update)
    LIDAR_LAYERS = [
        "NUALHD_1-0:dalles",        # New NUALID product layer (Nov 2025)
        "LIDARHD-NUALID:dalles",    # Alternative NUALID naming
        "LIDARHD_NUALID:dalles",    # Underscore variant
        "LIDARHD_FXX_1-0:dalles",   # Previous layer name for France
        "LIDARHD_1-0:dalles",       # Original layer name
        "LIDARHD:dalles",           # Simplified version
    ]
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the IGN downloader.
        
        Args:
            output_dir: Directory to save downloaded files. If None, uses temp directory.
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.output_dir = Path(tempfile.gettempdir()) / "lidar3d_downloads"
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"IGN Downloader initialized. Output directory: {self.output_dir}")
    
    def _try_wfs_request(self, params: dict) -> Optional[dict]:
        """
        Try a WFS request with given parameters.
        
        Args:
            params: WFS request parameters
            
        Returns:
            JSON response data if successful, None otherwise
        """
        try:
            logger.debug(f"Trying WFS request with params: {params}")
            response = requests.get(self.WFS_BASE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Check if we got valid GeoJSON response
                if 'features' in data:
                    return data
                else:
                    logger.debug(f"Response missing 'features' key")
                    return None
            else:
                logger.debug(f"Request failed with status {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            logger.debug(f"Request failed with exception: {e}")
            return None
    
    def find_tiles(self, bbox: List[float]) -> List[dict]:
        """
        Find available LiDAR HD tiles within a bounding box.
        
        Args:
            bbox: Bounding box as [lon_min, lat_min, lon_max, lat_max] in WGS84
            
        Returns:
            List of tile information dictionaries with 'name', 'url', and 'bbox' keys
        """
        logger.info(f"Searching for LiDAR HD tiles in bbox: {bbox}")
        
        # Validate bbox
        if len(bbox) != 4:
            raise ValueError("Bounding box must have 4 values: [lon_min, lat_min, lon_max, lat_max]")
        
        lon_min, lat_min, lon_max, lat_max = bbox
        
        if not (-180 <= lon_min <= 180 and -180 <= lon_max <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        if not (-90 <= lat_min <= 90 and -90 <= lat_max <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if lon_min >= lon_max or lat_min >= lat_max:
            raise ValueError("Invalid bounding box: min values must be less than max values")
        
        # Try multiple WFS configurations to handle API changes
        # IGN sometimes updates layer names and WFS versions
        configurations = []
        
        # Try each layer name with WFS 2.0.0
        for layer in self.LIDAR_LAYERS:
            configurations.append({
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typeNames': layer,  # WFS 2.0.0 uses 'typeNames' (plural)
                'outputFormat': 'application/json',
                'bbox': f"{lon_min},{lat_min},{lon_max},{lat_max},EPSG:4326",
                'count': 1000
            })
        
        # Try with WFS 1.1.0 as fallback (uses different parameter names)
        for layer in self.LIDAR_LAYERS:
            configurations.append({
                'service': 'WFS',
                'version': '1.1.0',
                'request': 'GetFeature',
                'typeName': layer,  # WFS 1.1.0 uses 'typeName' (singular)
                'outputFormat': 'application/json',
                'bbox': f"{lon_min},{lat_min},{lon_max},{lat_max},EPSG:4326",
                'maxFeatures': 1000  # WFS 1.1.0 uses 'maxFeatures' instead of 'count'
            })
        
        # Try alternative output formats
        for layer in self.LIDAR_LAYERS[:1]:  # Only try first layer with alternative formats
            configurations.append({
                'service': 'WFS',
                'version': '2.0.0',
                'request': 'GetFeature',
                'typeNames': layer,
                'outputFormat': 'json',  # Some servers prefer 'json' over 'application/json'
                'bbox': f"{lon_min},{lat_min},{lon_max},{lat_max},EPSG:4326",
                'count': 1000
            })
        
        # Try each configuration until one works
        data = None
        successful_config = None
        
        for i, config in enumerate(configurations, 1):
            logger.debug(f"Trying WFS configuration {i}/{len(configurations)}")
            data = self._try_wfs_request(config)
            if data:
                successful_config = config
                logger.info(f"Successfully connected with configuration {i}")
                logger.debug(f"Working config: {config}")
                break
        
        if not data:
            error_msg = (
                f"Failed to query IGN WFS service after trying {len(configurations)} configurations. "
                f"The API may have changed or the service may be unavailable. "
                f"Tried layer names: {', '.join(self.LIDAR_LAYERS)}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        features = data.get('features', [])
        
        if not features:
            logger.warning(f"No LiDAR HD tiles found in bbox {bbox}")
            return []
        
        tiles = []
        for feature in features:
            props = feature.get('properties', {})
            
            # Extract download URL - try multiple property names
            url_telechargement = props.get('url_telech') or props.get('url_telechargement') or props.get('url')
            if not url_telechargement:
                logger.debug(f"Feature missing download URL, properties: {props.keys()}")
                continue
            
            tile_info = {
                'name': props.get('nom_dalle') or props.get('nom') or 'unknown',
                'url': url_telechargement,
                'date': props.get('date_vol') or props.get('date') or 'unknown',
                'project': props.get('projet') or props.get('project') or 'unknown',
            }
            
            tiles.append(tile_info)
        
        logger.info(f"Found {len(tiles)} LiDAR HD tiles")
        return tiles
    
    def download_tile(self, tile_info: dict) -> Optional[Path]:
        """
        Download a single LiDAR tile.
        
        Args:
            tile_info: Tile information dictionary with 'url' and 'name' keys
            
        Returns:
            Path to downloaded file, or None if download failed
        """
        url = tile_info.get('url')
        name = tile_info.get('name', 'tile')
        
        if not url:
            logger.error("No download URL in tile info")
            return None
        
        # Ensure filename ends with .laz
        if not name.endswith('.laz'):
            name = f"{name}.laz"
        
        output_path = self.output_dir / name
        
        # Skip if already downloaded
        if output_path.exists():
            logger.info(f"Tile already downloaded: {name}")
            return output_path
        
        try:
            logger.info(f"Downloading tile: {name}")
            logger.debug(f"URL: {url}")
            
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Log progress every 10MB
                        if total_size > 0 and downloaded % (10 * 1024 * 1024) == 0:
                            progress = (downloaded / total_size) * 100
                            logger.debug(f"Download progress: {progress:.1f}%")
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"Downloaded: {name} ({file_size_mb:.1f} MB)")
            
            return output_path
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download tile {name}: {e}")
            # Clean up partial download
            if output_path.exists():
                output_path.unlink()
            return None
        except Exception as e:
            logger.error(f"Error downloading tile {name}: {e}")
            if output_path.exists():
                output_path.unlink()
            return None
    
    def download_tiles_in_bbox(self, bbox: List[float], max_tiles: int = 10) -> List[Path]:
        """
        Download all available LiDAR tiles in a bounding box.
        
        Args:
            bbox: Bounding box as [lon_min, lat_min, lon_max, lat_max] in WGS84
            max_tiles: Maximum number of tiles to download (default: 10)
            
        Returns:
            List of paths to downloaded LAZ files
        """
        # Find available tiles
        tiles = self.find_tiles(bbox)
        
        if not tiles:
            logger.warning("No tiles found to download")
            return []
        
        # Limit number of tiles
        if len(tiles) > max_tiles:
            logger.warning(f"Found {len(tiles)} tiles, but limiting to {max_tiles}")
            tiles = tiles[:max_tiles]
        
        # Download tiles
        downloaded_files = []
        for i, tile_info in enumerate(tiles, 1):
            logger.info(f"Downloading tile {i}/{len(tiles)}")
            file_path = self.download_tile(tile_info)
            if file_path:
                downloaded_files.append(file_path)
        
        logger.info(f"Successfully downloaded {len(downloaded_files)} tiles")
        return downloaded_files
    
    def merge_laz_files(self, laz_files: List[Path], output_file: Path) -> bool:
        """
        Merge multiple LAZ files into one.
        
        Args:
            laz_files: List of LAZ file paths to merge
            output_file: Output merged LAZ file path
            
        Returns:
            True if successful, False otherwise
        """
        if not laz_files:
            logger.error("No LAZ files to merge")
            return False
        
        if len(laz_files) == 1:
            # Just return the single file
            logger.info("Only one tile, no merge needed")
            return True
        
        try:
            import laspy
            import numpy as np
            
            logger.info(f"Merging {len(laz_files)} LAZ files")
            
            # Read first file to get header
            first_las = laspy.read(str(laz_files[0]))
            
            # Collect all points
            all_points = [first_las]
            
            for laz_file in laz_files[1:]:
                las = laspy.read(str(laz_file))
                all_points.append(las)
            
            # Merge point clouds
            merged = laspy.merge(all_points)
            
            # Write merged file
            logger.info(f"Writing merged file: {output_file}")
            merged.write(str(output_file))
            
            logger.info(f"Successfully merged {len(laz_files)} files into {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge LAZ files: {e}")
            return False


def download_ign_data(bbox: List[float], output_dir: Optional[str] = None, 
                     max_tiles: int = 10) -> Optional[Path]:
    """
    Convenience function to download IGN LiDAR HD data for a bounding box.
    
    Args:
        bbox: Bounding box as [lon_min, lat_min, lon_max, lat_max] in WGS84
        output_dir: Directory to save files (optional)
        max_tiles: Maximum number of tiles to download
        
    Returns:
        Path to downloaded/merged LAZ file, or None if failed
    """
    downloader = IGNDownloader(output_dir)
    
    try:
        # Download tiles
        laz_files = downloader.download_tiles_in_bbox(bbox, max_tiles)
        
        if not laz_files:
            return None
        
        # If single file, return it
        if len(laz_files) == 1:
            return laz_files[0]
        
        # If multiple files, merge them
        merged_file = downloader.output_dir / "merged_lidar.laz"
        if downloader.merge_laz_files(laz_files, merged_file):
            return merged_file
        else:
            # Return first file if merge fails
            logger.warning("Merge failed, returning first tile")
            return laz_files[0]
            
    except Exception as e:
        logger.error(f"Failed to download IGN data: {e}")
        return None
