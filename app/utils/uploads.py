import os
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename
import uuid

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (1200, 1200)  # Maximum dimensions for uploaded images

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_images(images):
    """Save multiple images and return their paths."""
    saved_paths = []
    
    for image in images:
        if image and allowed_file(image.filename):
            # Generate unique filename
            ext = image.filename.rsplit('.', 1)[1].lower()
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.root_path, 'static/uploads')
            os.makedirs(upload_dir, exist_ok=True)
            
            filepath = os.path.join(upload_dir, filename)
            
            # Open and process image with Pillow
            img = Image.open(image)
            
            # Convert RGBA to RGB if necessary
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize if larger than maximum size while maintaining aspect ratio
            if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
                img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save the processed image
            img.save(filepath, quality=85, optimize=True)
            
            # Store relative path for database
            saved_paths.append(f"uploads/{filename}")
    
    return saved_paths

def delete_image(filepath):
    """Delete an image file."""
    try:
        full_path = os.path.join(current_app.root_path, 'static', filepath)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Error deleting image {filepath}: {str(e)}")
    return False 