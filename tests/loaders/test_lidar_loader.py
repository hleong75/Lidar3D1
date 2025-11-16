"""
Tests for LiDAR loader.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile

from lidar3d.loaders.lidar_loader import LidarLoader
from tests.test_utils import create_sample_las_file


class TestLidarLoader:
    """Test LiDAR loader functionality."""
    
    @pytest.fixture
    def sample_las_file(self):
        """Create a temporary sample LAS file."""
        with tempfile.NamedTemporaryFile(suffix='.las', delete=False) as f:
            las_path = f.name
        
        create_sample_las_file(las_path, num_points=100)
        yield las_path
        
        # Cleanup
        Path(las_path).unlink(missing_ok=True)
    
    def test_init_with_valid_file(self, sample_las_file):
        """Test initialization with valid LAS file."""
        loader = LidarLoader(sample_las_file)
        assert loader.file_path.exists()
        assert loader.file_path.suffix == '.las'
    
    def test_init_with_invalid_file(self):
        """Test initialization with non-existent file."""
        with pytest.raises(FileNotFoundError):
            LidarLoader('nonexistent.las')
    
    def test_init_with_invalid_format(self):
        """Test initialization with invalid file format."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            with pytest.raises(ValueError):
                LidarLoader(f.name)
    
    def test_load(self, sample_las_file):
        """Test loading LAS file."""
        loader = LidarLoader(sample_las_file)
        assert loader.load() is True
        assert loader.points is not None
        assert len(loader.points) == 100
        assert loader.points.shape[1] == 3
    
    def test_get_points(self, sample_las_file):
        """Test getting points."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        points = loader.get_points()
        assert points is not None
        assert isinstance(points, np.ndarray)
        assert points.shape == (100, 3)
    
    def test_get_colors(self, sample_las_file):
        """Test getting colors."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        colors = loader.get_colors()
        assert colors is not None
        assert isinstance(colors, np.ndarray)
        assert colors.shape == (100, 3)
        assert np.all(colors >= 0) and np.all(colors <= 1)
    
    def test_get_classifications(self, sample_las_file):
        """Test getting classifications."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        classifications = loader.get_classifications()
        assert classifications is not None
        assert isinstance(classifications, np.ndarray)
        assert len(classifications) == 100
    
    def test_get_bounds(self, sample_las_file):
        """Test getting bounding box."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        bounds = loader.get_bounds()
        assert bounds is not None
        min_bounds, max_bounds = bounds
        assert min_bounds.shape == (3,)
        assert max_bounds.shape == (3,)
        assert np.all(min_bounds <= max_bounds)
    
    def test_filter_by_classification(self, sample_las_file):
        """Test filtering by classification."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        mask = loader.filter_by_classification([2, 6])
        assert isinstance(mask, np.ndarray)
        assert len(mask) == 100
        assert mask.dtype == bool
    
    def test_get_ground_points(self, sample_las_file):
        """Test getting ground points."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        ground_points = loader.get_ground_points()
        if ground_points is not None:
            assert isinstance(ground_points, np.ndarray)
            assert ground_points.shape[1] == 3
    
    def test_get_building_points(self, sample_las_file):
        """Test getting building points."""
        loader = LidarLoader(sample_las_file)
        loader.load()
        building_points = loader.get_building_points()
        if building_points is not None:
            assert isinstance(building_points, np.ndarray)
            assert building_points.shape[1] == 3
