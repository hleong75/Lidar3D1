"""
Test utilities for creating sample data.
"""
import numpy as np
from pathlib import Path
import laspy


def create_sample_las_file(output_path: str, num_points: int = 1000) -> bool:
    """
    Create a sample LAS file for testing.
    
    Args:
        output_path: Path to save the LAS file
        num_points: Number of points to generate
        
    Returns:
        True if successful
    """
    try:
        # Create random points
        x = np.random.uniform(0, 100, num_points)
        y = np.random.uniform(0, 100, num_points)
        z = np.random.uniform(0, 50, num_points)
        
        # Create random colors
        red = np.random.randint(0, 65535, num_points, dtype=np.uint16)
        green = np.random.randint(0, 65535, num_points, dtype=np.uint16)
        blue = np.random.randint(0, 65535, num_points, dtype=np.uint16)
        
        # Create random classifications
        classification = np.random.choice([2, 6, 9], num_points)
        
        # Create LAS file
        header = laspy.LasHeader(point_format=3, version="1.2")
        header.offsets = [0, 0, 0]
        header.scales = [0.01, 0.01, 0.01]
        
        las = laspy.LasData(header)
        las.x = x
        las.y = y
        las.z = z
        las.red = red
        las.green = green
        las.blue = blue
        las.classification = classification
        
        las.write(output_path)
        return True
        
    except Exception as e:
        print(f"Error creating sample LAS file: {e}")
        return False


def create_sample_building_points(center: tuple = (50, 50), 
                                  size: tuple = (10, 10),
                                  height: float = 20,
                                  num_points: int = 500) -> np.ndarray:
    """
    Create sample building points.
    
    Args:
        center: (x, y) center of building
        size: (width, depth) of building
        height: Building height
        num_points: Number of points to generate
        
    Returns:
        Nx3 array of points
    """
    points = []
    
    # Walls
    for _ in range(num_points // 2):
        # Random point on walls
        face = np.random.randint(0, 4)
        if face == 0:  # Front
            x = center[0] - size[0] / 2
            y = np.random.uniform(center[1] - size[1] / 2, center[1] + size[1] / 2)
        elif face == 1:  # Back
            x = center[0] + size[0] / 2
            y = np.random.uniform(center[1] - size[1] / 2, center[1] + size[1] / 2)
        elif face == 2:  # Left
            x = np.random.uniform(center[0] - size[0] / 2, center[0] + size[0] / 2)
            y = center[1] - size[1] / 2
        else:  # Right
            x = np.random.uniform(center[0] - size[0] / 2, center[0] + size[0] / 2)
            y = center[1] + size[1] / 2
        
        z = np.random.uniform(0, height)
        points.append([x, y, z])
    
    # Roof
    for _ in range(num_points // 2):
        x = np.random.uniform(center[0] - size[0] / 2, center[0] + size[0] / 2)
        y = np.random.uniform(center[1] - size[1] / 2, center[1] + size[1] / 2)
        z = height
        points.append([x, y, z])
    
    return np.array(points)
