# Lidar3D - LiDAR to 3DS Converter

A robust Python application that processes LiDAR HD data from IGN and OpenStreetMap data to generate high-quality 3DS files with textures.

## Features

- **LiDAR Processing**: Reads and processes LiDAR HD data in LAS/LAZ format from IGN
- **OSM Integration**: Fetches and integrates OpenStreetMap building and terrain data
- **Mesh Generation**: Creates optimized 3D meshes from point cloud data
- **Texture Mapping**: Generates and applies realistic textures to 3D models
- **3DS Export**: Outputs standard 3DS files compatible with major 3D software
- **Robust Error Handling**: Comprehensive validation and error recovery

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m lidar3d.main --input lidar_data.laz --osm-bbox "lat_min,lon_min,lat_max,lon_max" --output output.3ds
```

### With Configuration File

```bash
python -m lidar3d.main --config config.yaml
```

### Example Configuration

```yaml
input:
  lidar_file: "path/to/lidar_data.laz"
  osm_bbox: [48.8566, 2.3522, 48.8606, 2.3562]  # Paris example

output:
  file: "output.3ds"
  texture_size: 2048

processing:
  point_cloud_downsample: 0.5
  mesh_resolution: 1.0
  texture_quality: "high"
```

## Architecture

- `lidar3d/loaders/`: Data loading modules (LiDAR, OSM)
- `lidar3d/processors/`: Point cloud and mesh processing
- `lidar3d/textures/`: Texture generation and mapping
- `lidar3d/exporters/`: 3DS file export
- `tests/`: Comprehensive test suite

## Requirements

- Python 3.8+
- See requirements.txt for dependencies

## Testing

```bash
pytest tests/ -v --cov=lidar3d
```

## License

MIT License