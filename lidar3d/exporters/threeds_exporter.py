"""
3DS file format exporter.
"""
import logging
from pathlib import Path
from typing import Optional
import numpy as np
import struct

logger = logging.getLogger(__name__)


class ThreeDSExporter:
    """Export 3D models to 3DS file format."""
    
    # 3DS file format chunk IDs
    MAIN3DS = 0x4D4D
    EDIT3DS = 0x3D3D
    EDIT_OBJECT = 0x4000
    OBJ_TRIMESH = 0x4100
    TRI_VERTEXL = 0x4110
    TRI_FACEL1 = 0x4120
    TRI_MAPPINGCOORS = 0x4140
    TRI_MATERIAL = 0x4130
    EDIT_MATERIAL = 0xAFFF
    MAT_NAME = 0xA000
    MAT_DIFFUSE = 0xA020
    MAT_TEXMAP = 0xA200
    MAT_MAPNAME = 0xA300
    
    def __init__(self):
        """Initialize the 3DS exporter."""
        self.vertices = None
        self.faces = None
        self.uv_coords = None
        self.texture_path = None
        
    def set_mesh_data(self, vertices: np.ndarray, faces: np.ndarray,
                     uv_coords: Optional[np.ndarray] = None):
        """
        Set the mesh data to export.
        
        Args:
            vertices: Nx3 array of vertex positions
            faces: Mx3 array of face indices
            uv_coords: Nx2 array of UV coordinates (optional)
        """
        self.vertices = vertices
        self.faces = faces
        self.uv_coords = uv_coords
        
    def set_texture(self, texture_path: str):
        """
        Set the texture file path.
        
        Args:
            texture_path: Path to the texture image file
        """
        self.texture_path = texture_path
        
    def export(self, output_path: str) -> bool:
        """
        Export the mesh to a 3DS file.
        
        Args:
            output_path: Path for the output 3DS file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.vertices is None or self.faces is None:
                logger.error("No mesh data to export")
                return False
            
            logger.info(f"Exporting to 3DS: {output_path}")
            
            with open(output_path, 'wb') as f:
                # Write main chunk
                self._write_chunk_header(f, self.MAIN3DS, 0)
                main_start = f.tell()
                
                # Write editor chunk
                self._write_chunk_header(f, self.EDIT3DS, 0)
                edit_start = f.tell()
                
                # Write material if texture is available
                if self.texture_path:
                    self._write_material(f)
                
                # Write object
                self._write_object(f, "mesh_object")
                
                # Update editor chunk size
                edit_end = f.tell()
                f.seek(edit_start - 4)
                f.write(struct.pack('<I', edit_end - edit_start + 6))
                f.seek(edit_end)
                
                # Update main chunk size
                main_end = f.tell()
                f.seek(main_start - 4)
                f.write(struct.pack('<I', main_end - main_start + 6))
            
            logger.info(f"Successfully exported to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to 3DS: {e}")
            return False
    
    def _write_chunk_header(self, f, chunk_id: int, size: int):
        """Write a chunk header."""
        f.write(struct.pack('<H', chunk_id))
        f.write(struct.pack('<I', size))
    
    def _write_string(self, f, s: str):
        """Write a null-terminated string."""
        f.write(s.encode('ascii') + b'\x00')
    
    def _write_material(self, f):
        """Write material chunk."""
        # Material chunk
        self._write_chunk_header(f, self.EDIT_MATERIAL, 0)
        mat_start = f.tell()
        
        # Material name
        self._write_chunk_header(f, self.MAT_NAME, 0)
        name_start = f.tell()
        self._write_string(f, "material1")
        name_end = f.tell()
        f.seek(name_start - 4)
        f.write(struct.pack('<I', name_end - name_start + 6))
        f.seek(name_end)
        
        # Diffuse color
        self._write_chunk_header(f, self.MAT_DIFFUSE, 0)
        color_start = f.tell()
        # Color chunk
        f.write(struct.pack('<H', 0x0011))
        f.write(struct.pack('<I', 9))
        f.write(struct.pack('<BBB', 255, 255, 255))
        color_end = f.tell()
        f.seek(color_start - 4)
        f.write(struct.pack('<I', color_end - color_start + 6))
        f.seek(color_end)
        
        # Texture map
        if self.texture_path:
            self._write_chunk_header(f, self.MAT_TEXMAP, 0)
            texmap_start = f.tell()
            
            # Texture filename
            self._write_chunk_header(f, self.MAT_MAPNAME, 0)
            texname_start = f.tell()
            texture_name = Path(self.texture_path).name
            self._write_string(f, texture_name)
            texname_end = f.tell()
            f.seek(texname_start - 4)
            f.write(struct.pack('<I', texname_end - texname_start + 6))
            f.seek(texname_end)
            
            texmap_end = f.tell()
            f.seek(texmap_start - 4)
            f.write(struct.pack('<I', texmap_end - texmap_start + 6))
            f.seek(texmap_end)
        
        # Update material chunk size
        mat_end = f.tell()
        f.seek(mat_start - 4)
        f.write(struct.pack('<I', mat_end - mat_start + 6))
        f.seek(mat_end)
    
    def _write_object(self, f, name: str):
        """Write object chunk."""
        self._write_chunk_header(f, self.EDIT_OBJECT, 0)
        obj_start = f.tell()
        
        # Object name
        self._write_string(f, name)
        
        # Trimesh chunk
        self._write_chunk_header(f, self.OBJ_TRIMESH, 0)
        mesh_start = f.tell()
        
        # Vertices
        self._write_vertices(f)
        
        # Faces
        self._write_faces(f)
        
        # UV coordinates
        if self.uv_coords is not None:
            self._write_uv_coords(f)
        
        # Material assignment
        if self.texture_path:
            self._write_chunk_header(f, self.TRI_MATERIAL, 0)
            mat_start = f.tell()
            self._write_string(f, "material1")
            # Number of faces using this material
            f.write(struct.pack('<H', len(self.faces)))
            # Face indices
            for i in range(len(self.faces)):
                f.write(struct.pack('<H', i))
            mat_end = f.tell()
            f.seek(mat_start - 4)
            f.write(struct.pack('<I', mat_end - mat_start + 6))
            f.seek(mat_end)
        
        # Update trimesh chunk size
        mesh_end = f.tell()
        f.seek(mesh_start - 4)
        f.write(struct.pack('<I', mesh_end - mesh_start + 6))
        f.seek(mesh_end)
        
        # Update object chunk size
        obj_end = f.tell()
        f.seek(obj_start - 4)
        f.write(struct.pack('<I', obj_end - obj_start + 6))
        f.seek(obj_end)
    
    def _write_vertices(self, f):
        """Write vertex list chunk."""
        self._write_chunk_header(f, self.TRI_VERTEXL, 0)
        vert_start = f.tell()
        
        # Number of vertices
        f.write(struct.pack('<H', len(self.vertices)))
        
        # Vertex coordinates
        for v in self.vertices:
            f.write(struct.pack('<fff', float(v[0]), float(v[1]), float(v[2])))
        
        vert_end = f.tell()
        f.seek(vert_start - 4)
        f.write(struct.pack('<I', vert_end - vert_start + 6))
        f.seek(vert_end)
    
    def _write_faces(self, f):
        """Write face list chunk."""
        self._write_chunk_header(f, self.TRI_FACEL1, 0)
        face_start = f.tell()
        
        # Number of faces
        f.write(struct.pack('<H', len(self.faces)))
        
        # Face indices (with flags)
        for face in self.faces:
            f.write(struct.pack('<HHH', int(face[0]), int(face[1]), int(face[2])))
            f.write(struct.pack('<H', 0))  # Face flags
        
        face_end = f.tell()
        f.seek(face_start - 4)
        f.write(struct.pack('<I', face_end - face_start + 6))
        f.seek(face_end)
    
    def _write_uv_coords(self, f):
        """Write UV coordinates chunk."""
        self._write_chunk_header(f, self.TRI_MAPPINGCOORS, 0)
        uv_start = f.tell()
        
        # Number of UV coordinates
        f.write(struct.pack('<H', len(self.uv_coords)))
        
        # UV coordinates
        for uv in self.uv_coords:
            f.write(struct.pack('<ff', float(uv[0]), float(uv[1])))
        
        uv_end = f.tell()
        f.seek(uv_start - 4)
        f.write(struct.pack('<I', uv_end - uv_start + 6))
        f.seek(uv_end)
