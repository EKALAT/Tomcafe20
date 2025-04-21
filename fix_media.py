import os
import shutil
import django

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafe_project.settings')
django.setup()

from menu.models import MenuItem
from django.conf import settings

def fix_media_paths():
    print("Starting media path fix...")
    
    # Ensure media directory exists
    media_dir = os.path.join(settings.BASE_DIR, 'media')
    menu_images_dir = os.path.join(media_dir, 'menu_images')
    
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
        print(f"Created media directory: {media_dir}")
    
    if not os.path.exists(menu_images_dir):
        os.makedirs(menu_images_dir)
        print(f"Created menu images directory: {menu_images_dir}")
    
    # Check for menu_images directory in project root
    root_menu_images = os.path.join(settings.BASE_DIR, 'menu_images')
    if os.path.exists(root_menu_images) and os.path.isdir(root_menu_images):
        print(f"Found menu_images directory at project root: {root_menu_images}")
        
        # Copy all files to the correct media location
        for filename in os.listdir(root_menu_images):
            src_path = os.path.join(root_menu_images, filename)
            dst_path = os.path.join(menu_images_dir, filename)
            
            if os.path.isfile(src_path):
                shutil.copy(src_path, dst_path)
                print(f"Copied {filename} to media directory")
    
    # Check and update all MenuItem objects
    menu_items = MenuItem.objects.all()
    print(f"Found {len(menu_items)} menu items")
    
    for item in menu_items:
        print(f"Processing: {item.name}")
        if item.image:
            # Get the image filename
            image_name = os.path.basename(item.image.name)
            print(f"  Image name: {image_name}")
            
            # Check if the image exists in media/menu_images
            expected_path = os.path.join(menu_images_dir, image_name)
            if not os.path.exists(expected_path):
                # Try to find the image elsewhere
                possible_paths = [
                    os.path.join(root_menu_images, image_name),  # Root menu_images dir
                    os.path.join(settings.BASE_DIR, item.image.name),  # Full path from model
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        print(f"  Found image at: {path}")
                        shutil.copy(path, expected_path)
                        print(f"  Copied to: {expected_path}")
                        break
                else:
                    print(f"  WARNING: Could not find image: {image_name}")
            else:
                print(f"  Image already exists at: {expected_path}")
    
    print("Media path fix completed!")

if __name__ == "__main__":
    fix_media_paths() 