#!/usr/bin/env python3
"""
File and Image Field Example

This example demonstrates how to use FileField and ImageField
with Rust backend operations for high-performance file and image handling.
"""

import asyncio
import os
from oxen import Model, CharField, IntegerField, FileField, ImageField, connect
from oxen.file_operations import FileOperations, resize_image, create_thumbnail


class Document(Model):
    """Model for storing documents with file uploads."""
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    description = CharField(max_length=500, null=True)
    file = FileField(
        upload_to="documents/",
        max_size=50 * 1024 * 1024,  # 50MB
        allowed_extensions=['.pdf', '.doc', '.docx', '.txt', '.md']
    )
    file_size = IntegerField(null=True)
    created_at = CharField(max_length=50)  # Simplified for example


class Photo(Model):
    """Model for storing photos with image processing."""
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    description = CharField(max_length=500, null=True)
    image = ImageField(
        upload_to="photos/",
        max_size=10 * 1024 * 1024,  # 10MB
        allowed_formats=['.jpg', '.jpeg', '.png', '.webp'],
        resize_to=(1920, 1080),  # Resize to HD
        create_thumbnail=True,
        thumbnail_size=300
    )
    thumbnail_path = CharField(max_length=500, null=True)
    width = IntegerField(null=True)
    height = IntegerField(null=True)
    file_size = IntegerField(null=True)
    created_at = CharField(max_length=50)  # Simplified for example


async def create_sample_files():
    """Create sample files for testing."""
    # Create sample text file
    sample_text = "This is a sample document content.\n" * 100
    with open("sample_document.txt", "w") as f:
        f.write(sample_text)
    
    # Create sample image (simple colored rectangle)
    from PIL import Image, ImageDraw
    
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='red')
    draw = ImageDraw.Draw(img)
    draw.rectangle([100, 100, 700, 500], fill='blue')
    draw.text((400, 300), "Sample Image", fill='white')
    img.save("sample_image.png")
    
    return "sample_document.txt", "sample_image.png"


async def file_operations_example():
    """Demonstrate file operations."""
    print("=== File Operations Example ===")
    
    # Initialize file operations
    file_ops = FileOperations("uploads")
    
    # Create sample file
    sample_content = b"This is sample file content for testing file operations."
    
    # Upload file
    file_path = file_ops.upload_file(sample_content, "test_file.txt", "documents")
    print(f"Uploaded file: {file_path}")
    
    # Get file info
    file_info = file_ops.get_file_info(file_path)
    print(f"File info: {file_info}")
    
    # Read file
    content = file_ops.file_manager.read_file(file_path)
    print(f"File content: {content[:50]}...")
    
    # List directory
    files = file_ops.file_manager.list_directory("uploads/documents")
    print(f"Files in directory: {files}")
    
    # Clean up
    file_ops.delete_file(file_path)
    print("File deleted")


async def image_operations_example():
    """Demonstrate image operations."""
    print("\n=== Image Operations Example ===")
    
    # Initialize image processor
    from oxen.file_operations import ImageProcessor
    img_processor = ImageProcessor("images")
    
    # Create sample image data
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (400, 300), color='green')
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 100, 300, 200], fill='yellow')
    
    # Convert to bytes
    import io
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_data = buffer.getvalue()
    
    # Process and save image
    result = img_processor.process_and_save(
        image_data, 
        "test_image.png",
        resize_to=(200, 150),
        create_thumbnail=True,
        thumbnail_size=100
    )
    
    print(f"Image saved: {result}")
    
    # Get image info
    info = img_processor.get_image_info(image_data)
    print(f"Image info: {info}")
    
    # Apply effects
    blurred = img_processor.blur_image(image_data, sigma=2.0)
    brightened = img_processor.brighten_image(image_data, value=20)
    
    # Save processed images
    img_processor.save_image("images/blurred.png", blurred)
    img_processor.save_image("images/brightened.png", brightened)
    
    print("Image processing completed")


async def model_example():
    """Demonstrate FileField and ImageField in models."""
    print("\n=== Model Example ===")
    
    # Connect to database
    await connect("sqlite://:memory:")
    
    # Create tables
    await Document.create_table()
    await Photo.create_table()
    
    # Create sample files
    doc_file, img_file = await create_sample_files()
    
    # Create document with file
    with open(doc_file, 'rb') as f:
        doc_data = f.read()
    
    doc = await Document.create(
        title="Sample Document",
        description="A test document with file upload",
        file=doc_data,
        file_size=len(doc_data),
        created_at="2024-01-01 12:00:00"
    )
    
    print(f"Created document: {doc.title}")
    print(f"File path: {doc.file}")
    print(f"File size: {doc.file_size} bytes")
    
    # Create photo with image
    with open(img_file, 'rb') as f:
        img_data = f.read()
    
    photo = await Photo.create(
        title="Sample Photo",
        description="A test photo with image processing",
        image=img_data,
        file_size=len(img_data),
        created_at="2024-01-01 12:00:00"
    )
    
    print(f"Created photo: {photo.title}")
    print(f"Image path: {photo.image}")
    print(f"Image size: {photo.file_size} bytes")
    
    # Query and process
    documents = await Document.all()
    photos = await Photo.all()
    
    print(f"Total documents: {len(documents)}")
    print(f"Total photos: {len(photos)}")
    
    # Clean up sample files
    os.remove(doc_file)
    os.remove(img_file)


async def advanced_image_processing():
    """Demonstrate advanced image processing features."""
    print("\n=== Advanced Image Processing ===")
    
    # Create a more complex test image
    from PIL import Image, ImageDraw, ImageFont
    import io
    
    # Create gradient image
    width, height = 800, 600
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Create gradient
    for y in range(height):
        r = int(255 * y / height)
        g = int(255 * (height - y) / height)
        b = 128
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add text
    try:
        font = ImageFont.load_default()
        draw.text((width//2, height//2), "OxenORM", fill='white', font=font, anchor='mm')
    except:
        draw.text((width//2, height//2), "OxenORM", fill='white')
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    image_data = buffer.getvalue()
    
    # Demonstrate various operations
    file_ops = FileOperations("advanced_images")
    
    # 1. Resize
    resized = resize_image(image_data, 400, 300)
    file_ops.file_manager.write_file("advanced_images/resized.png", resized)
    
    # 2. Create thumbnail
    thumbnail = create_thumbnail(image_data, 150)
    file_ops.file_manager.write_file("advanced_images/thumbnail.png", thumbnail)
    
    # 3. Convert format
    from oxen.file_operations import ImageProcessor
    img_processor = ImageProcessor()
    jpeg_data = img_processor.convert_format(image_data, "jpeg")
    file_ops.file_manager.write_file("advanced_images/converted.jpg", jpeg_data)
    
    # 4. Apply effects
    blurred = img_processor.blur_image(image_data, sigma=3.0)
    brightened = img_processor.brighten_image(image_data, value=30)
    contrasted = img_processor.contrast_image(image_data, contrast=1.5)
    
    file_ops.file_manager.write_file("advanced_images/blurred.png", blurred)
    file_ops.file_manager.write_file("advanced_images/brightened.png", brightened)
    file_ops.file_manager.write_file("advanced_images/contrasted.png", contrasted)
    
    print("Advanced image processing completed")
    print("Generated files:")
    for file in file_ops.file_manager.list_directory("advanced_images"):
        file_path = f"advanced_images/{file}"
        size = file_ops.file_manager.get_file_size(file_path)
        print(f"  - {file} ({size} bytes)")


async def main():
    """Run all examples."""
    print("🚀 OxenORM File and Image Operations Demo")
    print("=" * 50)
    
    try:
        # Basic file operations
        await file_operations_example()
        
        # Basic image operations
        await image_operations_example()
        
        # Model usage
        await model_example()
        
        # Advanced image processing
        await advanced_image_processing()
        
        print("\n✅ All examples completed successfully!")
        print("\n📁 Generated files are in the 'uploads' and 'images' directories")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 