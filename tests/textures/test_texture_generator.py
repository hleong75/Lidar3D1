"""
Tests for texture generator.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path

from lidar3d.textures.texture_generator import TextureGenerator


class TestTextureGenerator:
    """Test texture generation functionality."""
    
    @pytest.fixture
    def sample_mesh_data(self):
        """Create sample mesh data."""
        # Simple triangle
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0.5, 1, 0],
            [0.5, 0.5, 1]
        ])
        
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 1, 3],
            [1, 2, 3]
        ])
        
        colors = np.array([
            [1, 0, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 1, 0]
        ])
        
        return vertices, faces, colors
    
    def test_init(self):
        """Test initialization."""
        gen = TextureGenerator(texture_size=512)
        assert gen.texture_size == 512
        assert gen.texture is None
        assert gen.uv_coords is None
    
    def test_create_default_texture(self):
        """Test creating default texture."""
        gen = TextureGenerator(texture_size=256)
        assert gen.create_default_texture() is True
        assert gen.texture is not None
        assert gen.texture.size == (256, 256)
    
    def test_create_default_texture_custom_color(self):
        """Test creating default texture with custom color."""
        gen = TextureGenerator(texture_size=256)
        assert gen.create_default_texture(color=(255, 0, 0)) is True
        assert gen.texture is not None
    
    def test_create_texture_from_colors(self, sample_mesh_data):
        """Test creating texture from colors."""
        vertices, faces, colors = sample_mesh_data
        gen = TextureGenerator(texture_size=256)
        
        result = gen.create_texture_from_colors(vertices, colors, faces)
        assert result is True
        assert gen.texture is not None
        assert gen.uv_coords is not None
        assert len(gen.uv_coords) == len(vertices)
    
    def test_create_procedural_texture(self, sample_mesh_data):
        """Test creating procedural texture."""
        vertices, faces, _ = sample_mesh_data
        gen = TextureGenerator(texture_size=256)
        
        result = gen.create_procedural_texture(vertices, faces)
        assert result is True
        assert gen.texture is not None
        assert gen.uv_coords is not None
    
    def test_get_texture(self):
        """Test getting texture."""
        gen = TextureGenerator()
        assert gen.get_texture() is None
        
        gen.create_default_texture()
        texture = gen.get_texture()
        assert texture is not None
    
    def test_get_uv_coords(self, sample_mesh_data):
        """Test getting UV coordinates."""
        vertices, faces, colors = sample_mesh_data
        gen = TextureGenerator(texture_size=256)
        
        assert gen.get_uv_coords() is None
        
        gen.create_texture_from_colors(vertices, colors, faces)
        uv_coords = gen.get_uv_coords()
        assert uv_coords is not None
        assert isinstance(uv_coords, np.ndarray)
        assert uv_coords.shape[1] == 2
    
    def test_save_texture(self):
        """Test saving texture."""
        gen = TextureGenerator(texture_size=256)
        gen.create_default_texture()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            texture_path = f.name
        
        try:
            assert gen.save_texture(texture_path) is True
            assert Path(texture_path).exists()
        finally:
            Path(texture_path).unlink(missing_ok=True)
    
    def test_save_texture_no_texture(self):
        """Test saving when no texture exists."""
        gen = TextureGenerator()
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            texture_path = f.name
        
        try:
            assert gen.save_texture(texture_path) is False
        finally:
            Path(texture_path).unlink(missing_ok=True)
