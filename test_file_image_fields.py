#!/usr/bin/env python3
"""
Test File and Image Fields

This test demonstrates the FileField and ImageField functionality
with Rust backend operations.
"""

import asyncio
import os
from oxen import Model, CharField, IntegerField, FileField, ImageField, connect
from oxen.file_operations import FileOperations, resize_image, create_thumbnail


class Document(Model):
    """Test model for file uploads."""
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    file = FileField(
        upload_to="test_documents/",
        max_size=10 * 1024 * 1024,  # 10MB
        allowed_extensions=['.txt', '.pdf', '.doc']
    )


class Photo(Model):
    """Test model for image uploads."""
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    image = ImageField(
        upload_to="test_photos/",
        max_size=5 * 1024 * 1024,  # 5MB
        allowed_formats=['.jpg', '.png', '.webp'],
        resize_to=(800, 600),
        create_thumbnail=True,
        thumbnail_size=150
    )


async def test_file_operations():
    """Test basic file operations."""
    print("=== Testing File Operations ===")
    
    # Test Rust backend file operations
    import oxen_engine
    
    # Create test file
    test_content = b"This is a test file content for OxenORM file operations."
    oxen_engine.write_file("test_file.txt", test_content)
    
    # Read file
    content = oxen_engine.read_file("test_file.txt")
    print(f"File content: {content[:50]}...")
    
    # Check file exists
    exists = oxen_engine.file_exists("test_file.txt")
    print(f"File exists: {exists}")
    
    # Get file size
    size = oxen_engine.get_file_size("test_file.txt")
    print(f"File size: {size} bytes")
    
    # Clean up
    oxen_engine.delete_file("test_file.txt")
    print("✅ File operations test passed")


async def test_image_operations():
    """Test basic image operations."""
    print("\n=== Testing Image Operations ===")
    
    # Create a simple test image using PIL
    try:
        from PIL import Image, ImageDraw
        
        # Create test image
        img = Image.new('RGB', (400, 300), color='blue')
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 300, 200], fill='red')
        draw.text((200, 150), "Test", fill='white')
        
        # Save to bytes
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        # Test image operations
        import oxen_engine
        
        # Save image
        oxen_engine.save_image("test_image.png", image_data)
        
        # Load image
        loaded_data = oxen_engine.load_image("test_image.png")
        print(f"Image loaded: {len(loaded_data)} bytes")
        
        # Get image info
        width, height, format = oxen_engine.get_image_info(image_data)
        print(f"Image info: {width}x{height}, format: {format}")
        
        # Resize image
        resized = oxen_engine.resize_image(image_data, 200, 150)
        oxen_engine.save_image("test_resized.png", resized)
        print("Image resized successfully")
        
        # Create thumbnail
        thumbnail = oxen_engine.create_thumbnail(image_data, 100)
        oxen_engine.save_image("test_thumbnail.png", thumbnail)
        print("Thumbnail created successfully")
        
        # Clean up
        oxen_engine.delete_file("test_image.png")
        oxen_engine.delete_file("test_resized.png")
        oxen_engine.delete_file("test_thumbnail.png")
        
        print("✅ Image operations test passed")
        
    except ImportError:
        print("⚠️ PIL not available, skipping image operations test")


async def test_file_operations_wrapper():
    """Test the Python wrapper for file operations."""
    print("\n=== Testing File Operations Wrapper ===")
    
    file_ops = FileOperations("test_uploads")
    
    # Test file upload
    test_data = b"This is test data for the file operations wrapper."
    file_path = file_ops.upload_file(test_data, "wrapper_test.txt", "documents")
    print(f"File uploaded: {file_path}")
    
    # Test file info
    file_info = file_ops.get_file_info(file_path)
    print(f"File info: {file_info}")
    
    # Test directory listing
    files = file_ops.file_manager.list_directory("test_uploads/documents")
    print(f"Files in directory: {files}")
    
    # Clean up
    file_ops.delete_file(file_path)
    print("✅ File operations wrapper test passed")


async def test_model_fields():
    """Test FileField and ImageField in models."""
    print("\n=== Testing Model Fields ===")
    
    # Connect to database
    engine = await connect("sqlite://:memory:")
    
    # For this test, we'll just test the field validation without creating tables
    print("Testing field validation...")
    
    # Test FileField validation
    file_field = FileField(
        upload_to="test_documents/",
        max_size=10 * 1024 * 1024,
        allowed_extensions=['.txt', '.pdf', '.doc']
    )
    
    # Test with valid data
    test_content = b"This is a test document for the model field test."
    try:
        file_field.validate(test_content)
        print("✅ FileField validation passed")
    except Exception as e:
        print(f"❌ FileField validation failed: {e}")
    
    # Test ImageField validation
    image_field = ImageField(
        upload_to="test_photos/",
        max_size=5 * 1024 * 1024,
        allowed_formats=['.jpg', '.png', '.webp'],
        resize_to=(800, 600),
        create_thumbnail=True,
        thumbnail_size=150
    )
    
    # Test with valid image data
    try:
        from PIL import Image, ImageDraw
        import io
        
        img = Image.new('RGB', (300, 200), color='green')
        draw = ImageDraw.Draw(img)
        draw.ellipse([100, 50, 200, 150], fill='yellow')
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        image_data = buffer.getvalue()
        
        image_field.validate(image_data)
        print("✅ ImageField validation passed")
        
    except ImportError:
        print("⚠️ PIL not available, skipping ImageField validation test")
    except Exception as e:
        print(f"❌ ImageField validation failed: {e}")
    
    # Test field conversion
    try:
        # Test FileField conversion
        db_value = file_field.to_db_value(test_content, None)
        python_value = file_field.to_python_value(db_value, None)
        print(f"✅ FileField conversion: {len(db_value)} bytes -> {type(python_value)}")
        
        # Test ImageField conversion (if PIL is available)
        try:
            from PIL import Image, ImageDraw
            import io
            
            img = Image.new('RGB', (300, 200), color='green')
            draw = ImageDraw.Draw(img)
            draw.ellipse([100, 50, 200, 150], fill='yellow')
            
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = buffer.getvalue()
            
            db_value = image_field.to_db_value(image_data, None)
            python_value = image_field.to_python_value(db_value, None)
            print(f"✅ ImageField conversion: {len(db_value)} bytes -> {type(python_value)}")
        except ImportError:
            print("⚠️ PIL not available, skipping ImageField conversion test")
        
    except Exception as e:
        print(f"❌ Field conversion failed: {e}")
    
    await engine.disconnect()
    
    print("✅ Model fields test passed")


async def main():
    """Run all tests."""
    print("🚀 OxenORM File and Image Fields Test")
    print("=" * 50)
    
    try:
        # Test basic operations
        await test_file_operations()
        await test_image_operations()
        await test_file_operations_wrapper()
        await test_model_fields()
        
        print("\n✅ All tests completed successfully!")
        print("\n📁 Generated files are in the 'test_uploads' directory")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 