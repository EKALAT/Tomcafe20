import os
import django
import shutil
from decimal import Decimal

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cafe_project.settings')
django.setup()

from menu.models import MenuItem
from django.conf import settings
from django.core.files import File

def create_sample_menu_items():
    print("Creating sample menu items...")
    
    # Ensure media directory exists
    media_dir = os.path.join(settings.BASE_DIR, 'media')
    menu_images_dir = os.path.join(media_dir, 'menu_images')
    
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
        print(f"Created media directory: {media_dir}")
    
    if not os.path.exists(menu_images_dir):
        os.makedirs(menu_images_dir)
        print(f"Created menu images directory: {menu_images_dir}")
    
    # Define sample menu items
    menu_items = [
        {
            'name': 'Trà tắc',
            'price': Decimal('15.00'),
            'category': 'Trà',
            'image_path': os.path.join(settings.BASE_DIR, 'menu_images', 'tra_tac.jpg'),
            'image_name': 'tra_tac.jpg'
        },
        {
            'name': 'Trà sữa',
            'price': Decimal('25.00'),
            'category': 'Trà',
            'image_path': os.path.join(settings.BASE_DIR, 'menu_images', 'tra_sua.jpg'),
            'image_name': 'tra_sua.jpg'
        },
        {
            'name': 'Cà phê đen',
            'price': Decimal('18.00'),
            'category': 'Cà phê',
            'image_path': os.path.join(settings.BASE_DIR, 'menu_images', 'ca_phe_den.jpg'),
            'image_name': 'ca_phe_den.jpg'
        },
        {
            'name': 'Cà phê sữa',
            'price': Decimal('20.00'),
            'category': 'Cà phê',
            'image_path': os.path.join(settings.BASE_DIR, 'menu_images', 'ca_phe_sua.jpg'),
            'image_name': 'ca_phe_sua.jpg'
        }
    ]
    
    # Copy default images if they don't exist
    root_menu_images = os.path.join(settings.BASE_DIR, 'menu_images')
    if os.path.exists(root_menu_images) and os.path.isdir(root_menu_images):
        print(f"Found menu_images directory at project root: {root_menu_images}")
        
        # List all image files in the root menu_images directory
        image_files = [f for f in os.listdir(root_menu_images) if os.path.isfile(os.path.join(root_menu_images, f))]
        print(f"Available images: {', '.join(image_files)}")
        
        # If there are at least some images, use them for our sample items
        if image_files:
            # Use existing images for our menu items
            for i, item in enumerate(menu_items):
                # Use modulo to cycle through available images
                img_file = image_files[i % len(image_files)]
                item['image_path'] = os.path.join(root_menu_images, img_file)
                item['image_name'] = img_file
                print(f"Using image {img_file} for {item['name']}")
    
    # Create menu items in database
    for item_data in menu_items:
        # Check if item with this name already exists
        existing_item = MenuItem.objects.filter(name=item_data['name']).first()
        
        if existing_item:
            print(f"Menu item '{item_data['name']}' already exists, updating...")
            menu_item = existing_item
            menu_item.price = item_data['price']
            menu_item.category = item_data['category']
        else:
            print(f"Creating new menu item: {item_data['name']}")
            menu_item = MenuItem(
                name=item_data['name'],
                price=item_data['price'],
                category=item_data['category']
            )
        
        # Add image if it exists
        image_path = item_data['image_path']
        if os.path.exists(image_path):
            # Copy the image to media directory
            dest_path = os.path.join(menu_images_dir, item_data['image_name'])
            shutil.copy(image_path, dest_path)
            print(f"Copied image from {image_path} to {dest_path}")
            
            # Update the model's image field
            with open(dest_path, 'rb') as f:
                menu_item.image.save(
                    item_data['image_name'],
                    File(f),
                    save=False
                )
        
        # Save the menu item
        menu_item.save()
        print(f"Saved menu item: {menu_item.name} (id: {menu_item.id})")
    
    # Print all menu items
    all_items = MenuItem.objects.all()
    print("\nAll menu items in database:")
    for item in all_items:
        print(f"- {item.name} ({item.category}): {item.price} บาท")
        if item.image:
            print(f"  Image: {item.image.url}")
        else:
            print("  No image")
    
    print("\nSample menu items created successfully!")

if __name__ == "__main__":
    create_sample_menu_items() 