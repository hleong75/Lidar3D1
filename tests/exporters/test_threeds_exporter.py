"""
Tests for 3DS exporter.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path

from lidar3d.exporters.threeds_exporter import ThreeDSExporter


class TestThreeDSExporter:
    """Test 3DS exporter functionality."""
    
    @pytest.fixture
    def sample_mesh_data(self):
        """Create sample mesh data."""
        vertices = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0.5, 1, 0],
            [0.5, 0.5, 1]
        ], dtype=np.float32)
        
        faces = np.array([
            [0, 1, 2],
            [0, 2, 3],
            [0, 1, 3],
            [1, 2, 3]
        ], dtype=np.int32)
        
        uv_coords = np.array([
            [0, 0],
            [1, 0],
            [0.5, 1],
            [0.5, 0.5]
        ], dtype=np.float32)
        
        return vertices, faces, uv_coords
    
    def test_init(self):
        """Test initialization."""
        exporter = ThreeDSExporter()
        assert exporter.vertices is None
        assert exporter.faces is None
        assert exporter.uv_coords is None
        assert exporter.texture_path is None
    
    def test_set_mesh_data(self, sample_mesh_data):
        """Test setting mesh data."""
        vertices, faces, uv_coords = sample_mesh_data
        exporter = ThreeDSExporter()
        
        exporter.set_mesh_data(vertices, faces, uv_coords)
        assert exporter.vertices is not None
        assert exporter.faces is not None
        assert exporter.uv_coords is not None
    
    def test_set_texture(self):
        """Test setting texture path."""
        exporter = ThreeDSExporter()
        exporter.set_texture('texture.png')
        assert exporter.texture_path == 'texture.png'
    
    def test_export(self, sample_mesh_data):
        """Test exporting to 3DS."""
        vertices, faces, uv_coords = sample_mesh_data
        exporter = ThreeDSExporter()
        exporter.set_mesh_data(vertices, faces, uv_coords)
        
        with tempfile.NamedTemporaryFile(suffix='.3ds', delete=False) as f:
            output_path = f.name
        
        try:
            assert exporter.export(output_path) is True
            assert Path(output_path).exists()
            assert Path(output_path).stat().st_size > 0
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_with_texture(self, sample_mesh_data):
        """Test exporting with texture."""
        vertices, faces, uv_coords = sample_mesh_data
        exporter = ThreeDSExporter()
        exporter.set_mesh_data(vertices, faces, uv_coords)
        exporter.set_texture('texture.png')
        
        with tempfile.NamedTemporaryFile(suffix='.3ds', delete=False) as f:
            output_path = f.name
        
        try:
            assert exporter.export(output_path) is True
            assert Path(output_path).exists()
            # File should be larger with texture info
            assert Path(output_path).stat().st_size > 100
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_no_mesh_data(self):
        """Test exporting without mesh data."""
        exporter = ThreeDSExporter()
        
        with tempfile.NamedTemporaryFile(suffix='.3ds', delete=False) as f:
            output_path = f.name
        
        try:
            assert exporter.export(output_path) is False
        finally:
            Path(output_path).unlink(missing_ok=True)
    
    def test_export_without_uv(self, sample_mesh_data):
        """Test exporting without UV coordinates."""
        vertices, faces, _ = sample_mesh_data
        exporter = ThreeDSExporter()
        exporter.set_mesh_data(vertices, faces, None)
        
        with tempfile.NamedTemporaryFile(suffix='.3ds', delete=False) as f:
            output_path = f.name
        
        try:
            assert exporter.export(output_path) is True
            assert Path(output_path).exists()
        finally:
            Path(output_path).unlink(missing_ok=True)
