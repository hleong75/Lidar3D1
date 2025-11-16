"""
Tests for IGN LiDAR HD downloader.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import json

from lidar3d.loaders.ign_downloader import IGNDownloader, download_ign_data


class TestIGNDownloader(unittest.TestCase):
    """Test cases for IGNDownloader class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.downloader = IGNDownloader(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        if Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
    
    def test_init(self):
        """Test downloader initialization."""
        self.assertIsNotNone(self.downloader)
        self.assertTrue(Path(self.temp_dir).exists())
    
    def test_init_with_no_dir(self):
        """Test initialization without output directory."""
        downloader = IGNDownloader()
        self.assertIsNotNone(downloader)
        self.assertTrue(downloader.output_dir.exists())
    
    def test_find_tiles_invalid_bbox(self):
        """Test find_tiles with invalid bounding box."""
        # Too few values
        with self.assertRaises(ValueError):
            self.downloader.find_tiles([1, 2, 3])
        
        # Invalid longitude
        with self.assertRaises(ValueError):
            self.downloader.find_tiles([200, 45, 210, 46])
        
        # Invalid latitude
        with self.assertRaises(ValueError):
            self.downloader.find_tiles([2, 100, 3, 101])
        
        # Min > Max
        with self.assertRaises(ValueError):
            self.downloader.find_tiles([3, 46, 2, 45])
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_find_tiles_success(self, mock_get):
        """Test successful tile finding."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'features': [
                {
                    'properties': {
                        'nom_dalle': 'TILE_001',
                        'url_telech': 'https://example.com/tile1.laz',
                        'date_vol': '2023-01-01',
                        'projet': 'LIDAR_HD'
                    }
                },
                {
                    'properties': {
                        'nom_dalle': 'TILE_002',
                        'url_telech': 'https://example.com/tile2.laz',
                        'date_vol': '2023-01-02',
                        'projet': 'LIDAR_HD'
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        tiles = self.downloader.find_tiles(bbox)
        
        self.assertEqual(len(tiles), 2)
        self.assertEqual(tiles[0]['name'], 'TILE_001')
        self.assertEqual(tiles[0]['url'], 'https://example.com/tile1.laz')
        self.assertEqual(tiles[1]['name'], 'TILE_002')
        
        # Verify that WFS 2.0.0 parameters are correct
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        params = call_args[1]['params']
        self.assertIn('typeNames', params, 'WFS 2.0.0 requires typeNames (plural) parameter')
        self.assertNotIn('typename', params, 'typename (singular) is for WFS 1.x only')
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_find_tiles_no_features(self, mock_get):
        """Test tile finding with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'features': []}
        mock_get.return_value = mock_response
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        tiles = self.downloader.find_tiles(bbox)
        
        self.assertEqual(len(tiles), 0)
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_find_tiles_request_error(self, mock_get):
        """Test tile finding with request error."""
        mock_get.side_effect = Exception("Network error")
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        
        with self.assertRaises(Exception):
            self.downloader.find_tiles(bbox)
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_download_tile_success(self, mock_get):
        """Test successful tile download."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '1024'}
        mock_response.iter_content = lambda chunk_size: [b'test data']
        mock_get.return_value = mock_response
        
        tile_info = {
            'name': 'test_tile',
            'url': 'https://example.com/test.laz'
        }
        
        result = self.downloader.download_tile(tile_info)
        
        self.assertIsNotNone(result)
        self.assertTrue(result.exists())
        self.assertEqual(result.name, 'test_tile.laz')
    
    def test_download_tile_no_url(self):
        """Test download with missing URL."""
        tile_info = {'name': 'test_tile'}
        
        result = self.downloader.download_tile(tile_info)
        
        self.assertIsNone(result)
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_download_tile_already_exists(self, mock_get):
        """Test download when file already exists."""
        # Create existing file
        existing_file = Path(self.temp_dir) / 'existing_tile.laz'
        existing_file.write_text('existing data')
        
        tile_info = {
            'name': 'existing_tile',
            'url': 'https://example.com/test.laz'
        }
        
        result = self.downloader.download_tile(tile_info)
        
        # Should return existing file without making request
        self.assertIsNotNone(result)
        self.assertEqual(result, existing_file)
        mock_get.assert_not_called()
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_download_tiles_in_bbox(self, mock_get):
        """Test downloading multiple tiles."""
        # Mock WFS response
        mock_wfs_response = Mock()
        mock_wfs_response.status_code = 200
        mock_wfs_response.json.return_value = {
            'features': [
                {
                    'properties': {
                        'nom_dalle': 'TILE_001',
                        'url_telech': 'https://example.com/tile1.laz',
                        'date_vol': '2023-01-01',
                        'projet': 'LIDAR_HD'
                    }
                },
                {
                    'properties': {
                        'nom_dalle': 'TILE_002',
                        'url_telech': 'https://example.com/tile2.laz',
                        'date_vol': '2023-01-02',
                        'projet': 'LIDAR_HD'
                    }
                }
            ]
        }
        
        # Mock download response
        mock_download_response = Mock()
        mock_download_response.status_code = 200
        mock_download_response.headers = {'content-length': '1024'}
        mock_download_response.iter_content = lambda chunk_size: [b'test data']
        
        # Configure mock to return different responses
        mock_get.side_effect = [mock_wfs_response, mock_download_response, mock_download_response]
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        files = self.downloader.download_tiles_in_bbox(bbox, max_tiles=5)
        
        self.assertEqual(len(files), 2)
        self.assertTrue(all(f.exists() for f in files))
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_download_tiles_in_bbox_no_tiles(self, mock_get):
        """Test download when no tiles are found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'features': []}
        mock_get.return_value = mock_response
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        files = self.downloader.download_tiles_in_bbox(bbox)
        
        self.assertEqual(len(files), 0)
    
    @patch('lidar3d.loaders.ign_downloader.requests.get')
    def test_download_tiles_max_limit(self, mock_get):
        """Test that max_tiles limit is respected."""
        # Create mock response with many tiles
        features = []
        for i in range(20):
            features.append({
                'properties': {
                    'nom_dalle': f'TILE_{i:03d}',
                    'url_telech': f'https://example.com/tile{i}.laz',
                    'date_vol': '2023-01-01',
                    'projet': 'LIDAR_HD'
                }
            })
        
        mock_wfs_response = Mock()
        mock_wfs_response.status_code = 200
        mock_wfs_response.json.return_value = {'features': features}
        
        mock_download_response = Mock()
        mock_download_response.status_code = 200
        mock_download_response.headers = {'content-length': '1024'}
        mock_download_response.iter_content = lambda chunk_size: [b'test data']
        
        # First call is WFS, rest are downloads
        mock_get.side_effect = [mock_wfs_response] + [mock_download_response] * 20
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        files = self.downloader.download_tiles_in_bbox(bbox, max_tiles=5)
        
        # Should only download 5 tiles
        self.assertEqual(len(files), 5)


class TestDownloadIGNData(unittest.TestCase):
    """Test cases for convenience function."""
    
    @patch('lidar3d.loaders.ign_downloader.IGNDownloader')
    def test_download_ign_data_single_file(self, mock_downloader_class):
        """Test convenience function with single file."""
        mock_downloader = Mock()
        mock_file = Path('/tmp/test.laz')
        mock_downloader.download_tiles_in_bbox.return_value = [mock_file]
        mock_downloader_class.return_value = mock_downloader
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        result = download_ign_data(bbox)
        
        self.assertEqual(result, mock_file)
    
    @patch('lidar3d.loaders.ign_downloader.IGNDownloader')
    def test_download_ign_data_no_files(self, mock_downloader_class):
        """Test convenience function with no files."""
        mock_downloader = Mock()
        mock_downloader.download_tiles_in_bbox.return_value = []
        mock_downloader_class.return_value = mock_downloader
        
        bbox = [2.35, 48.85, 2.36, 48.86]
        result = download_ign_data(bbox)
        
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
