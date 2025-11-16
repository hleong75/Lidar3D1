"""
OpenStreetMap data loader and processor.
"""
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np

try:
    import overpy
except ImportError:
    raise ImportError("overpy is required. Install with: pip install overpy")

logger = logging.getLogger(__name__)


class OSMLoader:
    """Load and process OpenStreetMap data."""
    
    def __init__(self, bbox: Tuple[float, float, float, float]):
        """
        Initialize the OSM loader.
        
        Args:
            bbox: Bounding box as (lat_min, lon_min, lat_max, lon_max)
        """
        self.bbox = bbox
        self.api = overpy.Overpass()
        self.buildings = []
        self.roads = []
        self.water = []
        self.landuse = []
        
    def load(self) -> bool:
        """
        Load OSM data for the bounding box.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Loading OSM data for bbox: {self.bbox}")
            
            # Load buildings
            self._load_buildings()
            
            # Load roads
            self._load_roads()
            
            # Load water features
            self._load_water()
            
            # Load landuse
            self._load_landuse()
            
            logger.info(f"Loaded {len(self.buildings)} buildings, "
                       f"{len(self.roads)} roads, "
                       f"{len(self.water)} water features, "
                       f"{len(self.landuse)} landuse polygons")
            return True
            
        except Exception as e:
            logger.error(f"Error loading OSM data: {e}")
            return False
    
    def _load_buildings(self):
        """Load building data from OSM."""
        try:
            query = f"""
            [out:json];
            (
              way["building"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
              relation["building"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
            );
            out body;
            >;
            out skel qt;
            """
            result = self.api.query(query)
            
            for way in result.ways:
                building = {
                    'id': way.id,
                    'tags': way.tags,
                    'nodes': [(float(node.lat), float(node.lon)) for node in way.nodes]
                }
                
                # Extract height if available
                if 'height' in way.tags:
                    try:
                        height_str = way.tags['height'].replace('m', '').strip()
                        building['height'] = float(height_str)
                    except:
                        building['height'] = None
                elif 'building:levels' in way.tags:
                    try:
                        levels = int(way.tags['building:levels'])
                        building['height'] = levels * 3.0  # Assume 3m per level
                    except:
                        building['height'] = None
                else:
                    building['height'] = None
                
                self.buildings.append(building)
                
        except Exception as e:
            logger.warning(f"Error loading buildings: {e}")
    
    def _load_roads(self):
        """Load road data from OSM."""
        try:
            query = f"""
            [out:json];
            (
              way["highway"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
            );
            out body;
            >;
            out skel qt;
            """
            result = self.api.query(query)
            
            for way in result.ways:
                road = {
                    'id': way.id,
                    'tags': way.tags,
                    'nodes': [(float(node.lat), float(node.lon)) for node in way.nodes]
                }
                self.roads.append(road)
                
        except Exception as e:
            logger.warning(f"Error loading roads: {e}")
    
    def _load_water(self):
        """Load water feature data from OSM."""
        try:
            query = f"""
            [out:json];
            (
              way["natural"="water"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
              way["waterway"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
            );
            out body;
            >;
            out skel qt;
            """
            result = self.api.query(query)
            
            for way in result.ways:
                water = {
                    'id': way.id,
                    'tags': way.tags,
                    'nodes': [(float(node.lat), float(node.lon)) for node in way.nodes]
                }
                self.water.append(water)
                
        except Exception as e:
            logger.warning(f"Error loading water features: {e}")
    
    def _load_landuse(self):
        """Load landuse data from OSM."""
        try:
            query = f"""
            [out:json];
            (
              way["landuse"]({self.bbox[0]},{self.bbox[1]},{self.bbox[2]},{self.bbox[3]});
            );
            out body;
            >;
            out skel qt;
            """
            result = self.api.query(query)
            
            for way in result.ways:
                landuse = {
                    'id': way.id,
                    'tags': way.tags,
                    'nodes': [(float(node.lat), float(node.lon)) for node in way.nodes]
                }
                self.landuse.append(landuse)
                
        except Exception as e:
            logger.warning(f"Error loading landuse: {e}")
    
    def get_buildings(self) -> List[Dict]:
        """
        Get loaded building data.
        
        Returns:
            List of building dictionaries
        """
        return self.buildings
    
    def get_roads(self) -> List[Dict]:
        """
        Get loaded road data.
        
        Returns:
            List of road dictionaries
        """
        return self.roads
    
    def get_water(self) -> List[Dict]:
        """
        Get loaded water feature data.
        
        Returns:
            List of water feature dictionaries
        """
        return self.water
    
    def get_landuse(self) -> List[Dict]:
        """
        Get loaded landuse data.
        
        Returns:
            List of landuse dictionaries
        """
        return self.landuse
