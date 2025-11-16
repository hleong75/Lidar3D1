# Lidar3D - LiDAR to 3DS Converter

A robust Python application that processes LiDAR HD data from IGN and OpenStreetMap data to generate high-quality 3DS files with textures.

## Features

- **LiDAR Processing**: Reads and processes LiDAR HD data in LAS/LAZ format from IGN
- **OSM Integration**: Fetches and integrates OpenStreetMap building and terrain data
- **Mesh Generation**: Creates optimized 3D meshes from point cloud data
- **Texture Mapping**: Generates and applies realistic textures to 3D models
- **3DS Export**: Outputs standard 3DS files compatible with major 3D software
- **Robust Error Handling**: Comprehensive validation and error recovery

## Quick Start

```bash
# Clone and setup
git clone https://github.com/hleong75/Lidar3D1.git
cd Lidar3D1

# Install dependencies
pip install -r requirements.txt

# Run demo
python3 demo.py

# Or use the quick start script
./quickstart.sh
```

## Installation

### Requirements
- Python 3.8+
- See requirements.txt for dependencies

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Automatic IGN Data Download (NEW!)

The program can now automatically download LiDAR HD data from IGN:

```bash
# Automatic download mode - downloads data for the specified bounding box
python -m lidar3d.main \
  --ign-auto-download \
  --ign-bbox "2.35,48.85,2.36,48.86" \
  --output paris_model.3ds

# Specify max number of tiles to download (default: 10)
python -m lidar3d.main \
  --ign-auto-download \
  --ign-bbox "2.35,48.85,2.36,48.86" \
  --max-tiles 5 \
  --output output.3ds
```

**Note**: The `--ign-bbox` format is `lon_min,lat_min,lon_max,lat_max` (longitude first, unlike OSM bbox).

**Recent Fix**: The IGN downloader now includes robust fallback mechanisms to handle API changes. It automatically tries multiple WFS versions and layer name variations. See [docs/IGN_API_FIXES.md](docs/IGN_API_FIXES.md) for details.

### Basic Usage (Manual File)

```bash
python -m lidar3d.main --input lidar_data.laz --osm-bbox "lat_min,lon_min,lat_max,lon_max" --output output.3ds
```

### With Configuration File

```bash
# Generate example configuration
python -m lidar3d.main --generate-config config.yaml

# Edit config.yaml to your needs, then run:
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

## Testing

Run the complete test suite:

```bash
pytest tests/ -v --cov=lidar3d
```

Run specific tests:

```bash
# Test LiDAR loader
pytest tests/loaders/test_lidar_loader.py -v

# Test mesh generation
pytest tests/processors/test_point_cloud.py -v

# Integration tests
pytest tests/test_integration.py -v
```

## Demo

The included demo script demonstrates the complete workflow:

```bash
python3 demo.py
```

This creates a sample 3D model from synthetic LiDAR data and shows all processing steps.

## Data Sources

### LiDAR Data (IGN)
- Format: LAS/LAZ (ASPRS standard)
- Source: IGN (Institut national de l'information géographique et forestière)
- **Automatic Download**: Use `--ign-auto-download` flag to download data automatically
- Manual Download: https://geoservices.ign.fr/lidarhd

### OpenStreetMap Data
- Automatically fetched via Overpass API
- Bounding box required (lat_min, lon_min, lat_max, lon_max)
- Used for building heights, roads, and land use

## Output Format

### 3DS File
- Standard Autodesk 3DS format
- Compatible with:
  - Autodesk 3ds Max
  - Blender
  - Maya
  - Cinema 4D
  - And many other 3D applications

### Texture
- PNG format
- Configurable resolution (default: 2048x2048)
- Generated from LiDAR colors or procedurally

## Command-Line Options

```
--input, -i              Path to LiDAR file (LAS/LAZ)
--ign-auto-download      Automatically download LiDAR data from IGN
--ign-bbox               Geographic bbox for IGN download (lon_min,lat_min,lon_max,lat_max)
--max-tiles              Maximum number of tiles to download (default: 10)
--osm-bbox               OSM bounding box (lat_min,lon_min,lat_max,lon_max)
--output, -o             Output 3DS file path
--texture-size           Texture resolution (default: 2048)
--downsample             Voxel size for downsampling (default: 0.5)
--mesh-method            Meshing algorithm: poisson or ball_pivoting
--log-level              Logging level: DEBUG, INFO, WARNING, ERROR
--config, -c             Path to YAML configuration file
--generate-config        Generate example configuration and exit
```

## Processing Pipeline

1. **Load LiDAR Data**: Read LAS/LAZ files and extract points, colors, classifications
2. **Load OSM Data**: Fetch building and terrain data from OpenStreetMap
3. **Process Point Cloud**: Downsample, remove outliers, estimate normals
4. **Generate Mesh**: Create surface mesh using Poisson or Ball Pivoting
5. **Create Textures**: Generate texture maps from colors or procedurally
6. **Export 3DS**: Write mesh and textures to 3DS format

## Troubleshooting

### IGN Download Issues (400 Bad Request)

If you encounter 400 errors when downloading from IGN:
- The downloader now automatically tries multiple WFS configurations
- Enable debug logging to see which configuration works: `--log-level DEBUG`
- See detailed troubleshooting guide: [docs/IGN_API_FIXES.md](docs/IGN_API_FIXES.md)
- Ensure your bounding box is within France (lon: -5 to 10, lat: 41 to 51)
- Check IGN service status at https://geoservices.ign.fr/

### OSM Data Loading Fails
- This is normal if network is unavailable or bbox is too large
- Pipeline will continue without OSM data
- Textures will be generated procedurally from LiDAR data

### Memory Issues
- Increase `point_cloud_downsample` value to reduce memory usage
- Enable `simplify_mesh` to reduce triangle count
- Reduce `texture_size`

### Mesh Quality Issues
- Try different `mesh_method` (poisson vs ball_pivoting)
- Adjust `point_cloud_downsample` for more detail
- Enable `remove_outliers` to clean noisy data

## Examples

### Automatic Download from IGN (NEW!)
```bash
# Download and process data for a small area in Paris
python -m lidar3d.main \
  --ign-auto-download \
  --ign-bbox "2.352,48.856,2.353,48.857" \
  --output paris_small.3ds \
  --downsample 0.3

# Download limited tiles for faster processing
python -m lidar3d.main \
  --ign-auto-download \
  --ign-bbox "2.35,48.85,2.36,48.86" \
  --max-tiles 3 \
  --output quick_test.3ds
```

### Process Small Area (Manual File)
```bash
python -m lidar3d.main \
  --input small_area.laz \
  --osm-bbox "48.856,2.352,48.857,2.353" \
  --output small_model.3ds \
  --downsample 0.3
```

### High Quality Model (Manual File)
```bash
python -m lidar3d.main \
  --input data.laz \
  --osm-bbox "48.8566,2.3522,48.8606,2.3562" \
  --output high_quality.3ds \
  --texture-size 4096 \
  --downsample 0.2 \
  --mesh-method poisson
```

### Fast Preview
```bash
python -m lidar3d.main \
  --input data.laz \
  --osm-bbox "48.8566,2.3522,48.8606,2.3562" \
  --output preview.3ds \
  --texture-size 512 \
  --downsample 2.0
```

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting:

```bash
pytest tests/ -v
```

## License

MIT License

## Acknowledgments

- IGN for LiDAR HD data
- OpenStreetMap contributors
- Open3D, laspy, and other open-source libraries