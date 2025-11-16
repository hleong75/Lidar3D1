"""
Point cloud processing and mesh generation.
"""
import logging
from typing import Optional, Tuple
import numpy as np

try:
    import open3d as o3d
except ImportError:
    raise ImportError("open3d is required. Install with: pip install open3d")

logger = logging.getLogger(__name__)


class PointCloudProcessor:
    """Process point clouds and generate meshes."""
    
    def __init__(self):
        """Initialize the point cloud processor."""
        self.point_cloud = None
        self.mesh = None
        
    def create_point_cloud(self, points: np.ndarray, colors: Optional[np.ndarray] = None) -> bool:
        """
        Create an Open3D point cloud from numpy arrays.
        
        Args:
            points: Nx3 array of [x, y, z] coordinates
            colors: Nx3 array of [r, g, b] colors in [0, 1] range (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if points is None or len(points) == 0:
                logger.error("No points provided")
                return False
            
            self.point_cloud = o3d.geometry.PointCloud()
            self.point_cloud.points = o3d.utility.Vector3dVector(points)
            
            if colors is not None:
                self.point_cloud.colors = o3d.utility.Vector3dVector(colors)
            
            logger.info(f"Created point cloud with {len(points)} points")
            return True
            
        except Exception as e:
            logger.error(f"Error creating point cloud: {e}")
            return False
    
    def downsample(self, voxel_size: float) -> bool:
        """
        Downsample the point cloud using voxel grid filtering.
        
        Args:
            voxel_size: Size of voxel for downsampling
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.point_cloud is None:
                logger.error("No point cloud to downsample")
                return False
            
            original_size = len(self.point_cloud.points)
            self.point_cloud = self.point_cloud.voxel_down_sample(voxel_size)
            new_size = len(self.point_cloud.points)
            
            logger.info(f"Downsampled from {original_size} to {new_size} points")
            return True
            
        except Exception as e:
            logger.error(f"Error downsampling: {e}")
            return False
    
    def remove_outliers(self, nb_neighbors: int = 20, std_ratio: float = 2.0) -> bool:
        """
        Remove statistical outliers from the point cloud.
        
        Args:
            nb_neighbors: Number of neighbors to analyze for each point
            std_ratio: Standard deviation ratio threshold
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.point_cloud is None:
                logger.error("No point cloud to filter")
                return False
            
            original_size = len(self.point_cloud.points)
            self.point_cloud, _ = self.point_cloud.remove_statistical_outlier(
                nb_neighbors=nb_neighbors,
                std_ratio=std_ratio
            )
            new_size = len(self.point_cloud.points)
            
            logger.info(f"Removed {original_size - new_size} outliers")
            return True
            
        except Exception as e:
            logger.error(f"Error removing outliers: {e}")
            return False
    
    def estimate_normals(self, search_radius: float = 1.0, max_nn: int = 30) -> bool:
        """
        Estimate normals for the point cloud.
        
        Args:
            search_radius: Search radius for normal estimation
            max_nn: Maximum number of neighbors to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.point_cloud is None:
                logger.error("No point cloud for normal estimation")
                return False
            
            self.point_cloud.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(
                    radius=search_radius,
                    max_nn=max_nn
                )
            )
            
            # Orient normals consistently
            self.point_cloud.orient_normals_consistent_tangent_plane(k=15)
            
            logger.info("Estimated normals for point cloud")
            return True
            
        except Exception as e:
            logger.error(f"Error estimating normals: {e}")
            return False
    
    def create_mesh_poisson(self, depth: int = 9) -> bool:
        """
        Create mesh using Poisson surface reconstruction.
        
        Args:
            depth: Depth of octree for reconstruction (higher = more detail)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.point_cloud is None:
                logger.error("No point cloud for meshing")
                return False
            
            if not self.point_cloud.has_normals():
                logger.info("Computing normals before meshing")
                self.estimate_normals()
            
            logger.info("Creating mesh using Poisson reconstruction...")
            self.mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
                self.point_cloud,
                depth=depth
            )
            
            # Remove low-density vertices
            vertices_to_remove = densities < np.quantile(densities, 0.01)
            self.mesh.remove_vertices_by_mask(vertices_to_remove)
            
            logger.info(f"Created mesh with {len(self.mesh.vertices)} vertices "
                       f"and {len(self.mesh.triangles)} triangles")
            return True
            
        except Exception as e:
            logger.error(f"Error creating mesh: {e}")
            return False
    
    def create_mesh_ball_pivoting(self, radii: list = None) -> bool:
        """
        Create mesh using Ball Pivoting Algorithm.
        
        Args:
            radii: List of radii for ball pivoting
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.point_cloud is None:
                logger.error("No point cloud for meshing")
                return False
            
            if not self.point_cloud.has_normals():
                logger.info("Computing normals before meshing")
                self.estimate_normals()
            
            if radii is None:
                # Estimate appropriate radii based on point cloud density
                distances = self.point_cloud.compute_nearest_neighbor_distance()
                avg_dist = np.mean(distances)
                radii = [avg_dist * r for r in [1, 2, 4]]
            
            logger.info("Creating mesh using Ball Pivoting...")
            self.mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_ball_pivoting(
                self.point_cloud,
                o3d.utility.DoubleVector(radii)
            )
            
            logger.info(f"Created mesh with {len(self.mesh.vertices)} vertices "
                       f"and {len(self.mesh.triangles)} triangles")
            return True
            
        except Exception as e:
            logger.error(f"Error creating mesh: {e}")
            return False
    
    def simplify_mesh(self, target_triangles: int) -> bool:
        """
        Simplify the mesh to reduce triangle count.
        
        Args:
            target_triangles: Target number of triangles
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mesh is None:
                logger.error("No mesh to simplify")
                return False
            
            original_triangles = len(self.mesh.triangles)
            self.mesh = self.mesh.simplify_quadric_decimation(target_triangles)
            new_triangles = len(self.mesh.triangles)
            
            logger.info(f"Simplified mesh from {original_triangles} to {new_triangles} triangles")
            return True
            
        except Exception as e:
            logger.error(f"Error simplifying mesh: {e}")
            return False
    
    def get_point_cloud(self) -> Optional[o3d.geometry.PointCloud]:
        """
        Get the current point cloud.
        
        Returns:
            Open3D point cloud or None
        """
        return self.point_cloud
    
    def get_mesh(self) -> Optional[o3d.geometry.TriangleMesh]:
        """
        Get the current mesh.
        
        Returns:
            Open3D triangle mesh or None
        """
        return self.mesh
    
    def get_mesh_data(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get mesh vertices and faces as numpy arrays.
        
        Returns:
            Tuple of (vertices, faces) or None if no mesh
        """
        if self.mesh is None:
            return None
        
        vertices = np.asarray(self.mesh.vertices)
        faces = np.asarray(self.mesh.triangles)
        return vertices, faces
