"""
Texture generation and mapping for 3D models.
"""
import logging
from typing import Optional, Tuple
import numpy as np

try:
    from PIL import Image
except ImportError:
    raise ImportError("Pillow is required. Install with: pip install Pillow")

logger = logging.getLogger(__name__)


class TextureGenerator:
    """Generate and apply textures to 3D models."""
    
    def __init__(self, texture_size: int = 2048):
        """
        Initialize the texture generator.
        
        Args:
            texture_size: Size of the texture in pixels (width and height)
        """
        self.texture_size = texture_size
        self.texture = None
        self.uv_coords = None
        
    def create_texture_from_colors(self, vertices: np.ndarray, colors: np.ndarray,
                                   faces: np.ndarray) -> bool:
        """
        Create a texture from vertex colors.
        
        Args:
            vertices: Nx3 array of vertex positions
            colors: Nx3 array of RGB colors in [0, 1] range
            faces: Mx3 array of face indices
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if colors is None or len(colors) == 0:
                logger.warning("No colors provided, creating default texture")
                return self.create_default_texture()
            
            # Create UV coordinates using planar projection
            self.uv_coords = self._planar_uv_mapping(vertices)
            
            # Create texture by sampling colors
            self.texture = self._sample_colors_to_texture(
                vertices, colors, faces, self.uv_coords
            )
            
            logger.info(f"Created texture from colors: {self.texture.size}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating texture from colors: {e}")
            return False
    
    def create_default_texture(self, color: Tuple[int, int, int] = (200, 200, 200)) -> bool:
        """
        Create a default solid color texture.
        
        Args:
            color: RGB color tuple (0-255)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.texture = Image.new('RGB', (self.texture_size, self.texture_size), color)
            logger.info(f"Created default texture: {self.texture.size}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating default texture: {e}")
            return False
    
    def create_procedural_texture(self, vertices: np.ndarray, faces: np.ndarray,
                                 osm_data: dict = None) -> bool:
        """
        Create a procedural texture based on geometry and OSM data.
        
        Args:
            vertices: Nx3 array of vertex positions
            faces: Mx3 array of face indices
            osm_data: Dictionary of OSM data (buildings, roads, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create UV coordinates
            self.uv_coords = self._planar_uv_mapping(vertices)
            
            # Create base texture
            texture_array = np.ones((self.texture_size, self.texture_size, 3), dtype=np.uint8) * 200
            
            # Add variation based on height
            heights = vertices[:, 2]
            height_normalized = (heights - heights.min()) / (heights.max() - heights.min() + 1e-6)
            
            # Apply height-based coloring
            for i, (u, v) in enumerate(self.uv_coords):
                u_idx = int(u * (self.texture_size - 1))
                v_idx = int(v * (self.texture_size - 1))
                
                # Color based on height (darker for lower, lighter for higher)
                intensity = int(150 + height_normalized[i] * 100)
                texture_array[v_idx, u_idx] = [intensity, intensity, intensity]
            
            self.texture = Image.fromarray(texture_array)
            logger.info(f"Created procedural texture: {self.texture.size}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating procedural texture: {e}")
            return False
    
    def _planar_uv_mapping(self, vertices: np.ndarray) -> np.ndarray:
        """
        Create UV coordinates using planar projection.
        
        Args:
            vertices: Nx3 array of vertex positions
            
        Returns:
            Nx2 array of UV coordinates in [0, 1] range
        """
        # Use XY plane for projection
        x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()
        y_min, y_max = vertices[:, 1].min(), vertices[:, 1].max()
        
        u = (vertices[:, 0] - x_min) / (x_max - x_min + 1e-6)
        v = (vertices[:, 1] - y_min) / (y_max - y_min + 1e-6)
        
        return np.column_stack([u, v])
    
    def _sample_colors_to_texture(self, vertices: np.ndarray, colors: np.ndarray,
                                  faces: np.ndarray, uv_coords: np.ndarray) -> Image.Image:
        """
        Sample vertex colors to create a texture image.
        
        Args:
            vertices: Nx3 array of vertex positions
            colors: Nx3 array of RGB colors in [0, 1] range
            faces: Mx3 array of face indices
            uv_coords: Nx2 array of UV coordinates
            
        Returns:
            PIL Image with the texture
        """
        texture_array = np.zeros((self.texture_size, self.texture_size, 3), dtype=np.float32)
        counts = np.zeros((self.texture_size, self.texture_size), dtype=np.float32)
        
        # Sample each vertex's color to its UV location
        for i, (u, v) in enumerate(uv_coords):
            u_idx = int(u * (self.texture_size - 1))
            v_idx = int(v * (self.texture_size - 1))
            
            # Accumulate colors
            texture_array[v_idx, u_idx] += colors[i]
            counts[v_idx, u_idx] += 1
        
        # Average accumulated colors
        mask = counts > 0
        texture_array[mask] /= counts[mask, np.newaxis]
        
        # Fill empty pixels with nearest neighbor
        self._fill_empty_pixels(texture_array, mask)
        
        # Convert to 8-bit RGB
        texture_array = (texture_array * 255).astype(np.uint8)
        
        return Image.fromarray(texture_array)
    
    def _fill_empty_pixels(self, texture_array: np.ndarray, filled_mask: np.ndarray):
        """
        Fill empty pixels in the texture using nearest neighbor interpolation.
        
        Args:
            texture_array: HxWx3 texture array
            filled_mask: HxW boolean mask of filled pixels
        """
        from scipy.ndimage import distance_transform_edt
        
        # Find nearest filled pixel for each empty pixel
        empty_mask = ~filled_mask
        if not np.any(empty_mask):
            return
        
        indices = distance_transform_edt(empty_mask, return_distances=False, return_indices=True)
        
        # Fill empty pixels with nearest neighbor
        texture_array[empty_mask] = texture_array[tuple(indices[:, empty_mask])]
    
    def get_texture(self) -> Optional[Image.Image]:
        """
        Get the generated texture.
        
        Returns:
            PIL Image or None
        """
        return self.texture
    
    def get_uv_coords(self) -> Optional[np.ndarray]:
        """
        Get UV coordinates.
        
        Returns:
            Nx2 array of UV coordinates or None
        """
        return self.uv_coords
    
    def save_texture(self, file_path: str) -> bool:
        """
        Save the texture to a file.
        
        Args:
            file_path: Path to save the texture
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.texture is None:
                logger.error("No texture to save")
                return False
            
            self.texture.save(file_path)
            logger.info(f"Saved texture to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving texture: {e}")
            return False
