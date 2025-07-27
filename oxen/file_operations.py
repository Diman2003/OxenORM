#!/usr/bin/env python3
"""
File and Image Operations Module

This module provides high-level Python APIs for file and image operations
using the Rust backend for optimal performance.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import tempfile
import uuid

try:
    import oxen_engine
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class FileManager:
    """
    High-level file management with Rust backend support.
    """
    
    def __init__(self, base_path: str = "uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def read_file(self, path: str) -> bytes:
        """Read file contents."""
        if RUST_AVAILABLE:
            return oxen_engine.read_file(path)
        else:
            with open(path, 'rb') as f:
                return f.read()
    
    def write_file(self, path: str, data: bytes) -> None:
        """Write data to file."""
        # Ensure directory exists
        dirname = os.path.dirname(path)
        if dirname:  # Only create directory if there is a directory path
            os.makedirs(dirname, exist_ok=True)
        
        if RUST_AVAILABLE:
            oxen_engine.write_file(path, data)
        else:
            with open(path, 'wb') as f:
                f.write(data)
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        if RUST_AVAILABLE:
            return oxen_engine.file_exists(path)
        else:
            return os.path.exists(path)
    
    def delete_file(self, path: str) -> None:
        """Delete file."""
        if RUST_AVAILABLE:
            oxen_engine.delete_file(path)
        else:
            if os.path.exists(path):
                os.remove(path)
    
    def get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        if RUST_AVAILABLE:
            return oxen_engine.get_file_size(path)
        else:
            return os.path.getsize(path)
    
    def create_directory(self, path: str) -> None:
        """Create directory and parent directories."""
        if RUST_AVAILABLE:
            oxen_engine.create_directory(path)
        else:
            os.makedirs(path, exist_ok=True)
    
    def list_directory(self, path: str) -> List[str]:
        """List files in directory."""
        if RUST_AVAILABLE:
            return oxen_engine.list_directory(path)
        else:
            return [f.name for f in os.scandir(path) if f.is_file()]
    
    def save_upload(self, data: bytes, filename: str = None, subdirectory: str = None) -> str:
        """Save uploaded file with unique name."""
        if filename is None:
            filename = f"{uuid.uuid4()}.tmp"
        
        if subdirectory:
            save_path = self.base_path / subdirectory / filename
        else:
            save_path = self.base_path / filename
        
        self.write_file(str(save_path), data)
        return str(save_path)
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get comprehensive file information."""
        if not self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        return {
            'path': path,
            'size': self.get_file_size(path),
            'exists': True,
            'extension': Path(path).suffix.lower(),
            'filename': Path(path).name,
            'directory': str(Path(path).parent)
        }


class ImageProcessor:
    """
    High-level image processing with Rust backend support.
    """
    
    def __init__(self, base_path: str = "images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def load_image(self, path: str) -> bytes:
        """Load image from file."""
        if RUST_AVAILABLE:
            return oxen_engine.load_image(path)
        else:
            with open(path, 'rb') as f:
                return f.read()
    
    def save_image(self, path: str, data: bytes) -> None:
        """Save image to file."""
        if RUST_AVAILABLE:
            oxen_engine.save_image(path, data)
        else:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                f.write(data)
    
    def resize_image(self, data: bytes, width: int, height: int) -> bytes:
        """Resize image to specified dimensions."""
        if RUST_AVAILABLE:
            return oxen_engine.resize_image(data, width, height)
        else:
            # Fallback to PIL
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            resized.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def blur_image(self, data: bytes, sigma: float = 1.0) -> bytes:
        """Apply Gaussian blur to image."""
        if RUST_AVAILABLE:
            return oxen_engine.blur_image(data, sigma)
        else:
            # Fallback to PIL
            from PIL import Image, ImageFilter
            import io
            
            img = Image.open(io.BytesIO(data))
            blurred = img.filter(ImageFilter.GaussianBlur(radius=sigma))
            
            buffer = io.BytesIO()
            blurred.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def brighten_image(self, data: bytes, value: int = 10) -> bytes:
        """Brighten image by specified value."""
        if RUST_AVAILABLE:
            return oxen_engine.brighten_image(data, value)
        else:
            # Fallback to PIL
            from PIL import Image, ImageEnhance
            import io
            
            img = Image.open(io.BytesIO(data))
            enhancer = ImageEnhance.Brightness(img)
            brightened = enhancer.enhance(1.0 + value / 100.0)
            
            buffer = io.BytesIO()
            brightened.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def contrast_image(self, data: bytes, contrast: float = 1.2) -> bytes:
        """Adjust image contrast."""
        if RUST_AVAILABLE:
            return oxen_engine.contrast_image(data, contrast)
        else:
            # Fallback to PIL
            from PIL import Image, ImageEnhance
            import io
            
            img = Image.open(io.BytesIO(data))
            enhancer = ImageEnhance.Contrast(img)
            contrasted = enhancer.enhance(contrast)
            
            buffer = io.BytesIO()
            contrasted.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def get_image_info(self, data: bytes) -> Dict[str, Any]:
        """Get image information (width, height, format)."""
        if RUST_AVAILABLE:
            width, height, format = oxen_engine.get_image_info(data)
            return {
                'width': width,
                'height': height,
                'format': format,
                'size': len(data)
            }
        else:
            # Fallback to PIL
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'size': len(data)
            }
    
    def convert_format(self, data: bytes, format: str) -> bytes:
        """Convert image to different format."""
        if RUST_AVAILABLE:
            return oxen_engine.convert_image_format(data, format)
        else:
            # Fallback to PIL
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            buffer = io.BytesIO()
            img.save(buffer, format=format.upper())
            return buffer.getvalue()
    
    def create_thumbnail(self, data: bytes, max_size: int = 150) -> bytes:
        """Create thumbnail with maximum dimension."""
        if RUST_AVAILABLE:
            return oxen_engine.create_thumbnail(data, max_size)
        else:
            # Fallback to PIL
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(data))
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            return buffer.getvalue()
    
    def process_and_save(self, data: bytes, filename: str, 
                        resize_to: Optional[Tuple[int, int]] = None,
                        create_thumbnail: bool = False,
                        thumbnail_size: int = 150,
                        format: str = 'png') -> Dict[str, str]:
        """Process image and save with optional thumbnail."""
        # Process main image
        processed_data = data
        
        if resize_to:
            width, height = resize_to
            processed_data = self.resize_image(processed_data, width, height)
        
        if format.lower() != 'png':
            processed_data = self.convert_format(processed_data, format)
        
        # Save main image
        main_path = self.base_path / filename
        self.save_image(str(main_path), processed_data)
        
        result = {'main': str(main_path)}
        
        # Create thumbnail if requested
        if create_thumbnail:
            thumbnail_data = self.create_thumbnail(data, thumbnail_size)
            thumbnail_filename = f"thumb_{filename}"
            thumbnail_path = self.base_path / "thumbnails" / thumbnail_filename
            
            # Ensure thumbnail directory exists
            thumbnail_path.parent.mkdir(exist_ok=True)
            
            self.save_image(str(thumbnail_path), thumbnail_data)
            result['thumbnail'] = str(thumbnail_path)
        
        return result


class FileOperations:
    """
    Unified interface for file and image operations.
    """
    
    def __init__(self, base_path: str = "uploads"):
        self.file_manager = FileManager(base_path)
        self.image_processor = ImageProcessor(base_path)
    
    def upload_file(self, data: bytes, filename: str = None, 
                   subdirectory: str = None) -> str:
        """Upload and save file."""
        return self.file_manager.save_upload(data, filename, subdirectory)
    
    def upload_image(self, data: bytes, filename: str = None,
                    resize_to: Optional[Tuple[int, int]] = None,
                    create_thumbnail: bool = False,
                    thumbnail_size: int = 150) -> Dict[str, str]:
        """Upload and process image."""
        if filename is None:
            filename = f"{uuid.uuid4()}.png"
        
        return self.image_processor.process_and_save(
            data, filename, resize_to, create_thumbnail, thumbnail_size
        )
    
    def delete_file(self, path: str) -> None:
        """Delete file."""
        self.file_manager.delete_file(path)
    
    def get_file_info(self, path: str) -> Dict[str, Any]:
        """Get file information."""
        return self.file_manager.get_file_info(path)
    
    def get_image_info(self, path: str) -> Dict[str, Any]:
        """Get image information."""
        data = self.file_manager.read_file(path)
        return self.image_processor.get_image_info(data)
    
    def resize_image_file(self, path: str, width: int, height: int, 
                         output_path: str = None) -> str:
        """Resize image file."""
        data = self.file_manager.read_file(path)
        resized_data = self.image_processor.resize_image(data, width, height)
        
        if output_path is None:
            output_path = f"{Path(path).stem}_resized{Path(path).suffix}"
        
        self.file_manager.write_file(output_path, resized_data)
        return output_path
    
    def create_thumbnail_file(self, path: str, max_size: int = 150,
                            output_path: str = None) -> str:
        """Create thumbnail from image file."""
        data = self.file_manager.read_file(path)
        thumbnail_data = self.image_processor.create_thumbnail(data, max_size)
        
        if output_path is None:
            output_path = f"{Path(path).stem}_thumb{Path(path).suffix}"
        
        self.file_manager.write_file(output_path, thumbnail_data)
        return output_path


# Convenience functions
def read_file(path: str) -> bytes:
    """Read file contents."""
    if RUST_AVAILABLE:
        return oxen_engine.read_file(path)
    else:
        with open(path, 'rb') as f:
            return f.read()


def write_file(path: str, data: bytes) -> None:
    """Write data to file."""
    if RUST_AVAILABLE:
        oxen_engine.write_file(path, data)
    else:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data)


def resize_image(data: bytes, width: int, height: int) -> bytes:
    """Resize image data."""
    if RUST_AVAILABLE:
        return oxen_engine.resize_image(data, width, height)
    else:
        # Fallback to PIL
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(data))
        resized = img.resize((width, height), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        resized.save(buffer, format='PNG')
        return buffer.getvalue()


def create_thumbnail(data: bytes, max_size: int = 150) -> bytes:
    """Create thumbnail from image data."""
    if RUST_AVAILABLE:
        return oxen_engine.create_thumbnail(data, max_size)
    else:
        # Fallback to PIL
        from PIL import Image
        import io
        
        img = Image.open(io.BytesIO(data))
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue() 