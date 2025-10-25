
# Create a sample file upload script to help users prepare their files
upload_helper = '''"""
File Upload Helper Script
This script helps prepare your question folders for upload to NotJustExam
"""

import os
import shutil
from pathlib import Path
import zipfile

def create_upload_package(source_dir: str, output_dir: str = "upload_package"):
    """
    Prepare question folders for upload to NotJustExam
    
    Args:
        source_dir: Directory containing your topic_X_question_Y folders
        output_dir: Directory to create the upload package
    """
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    
    # Create output directory
    output_path.mkdir(exist_ok=True)
    
    # Find all topic folders
    topic_folders = sorted([d for d in source_path.iterdir() 
                           if d.is_dir() and d.name.startswith('topic_')])
    
    if not topic_folders:
        print("❌ No topic folders found!")
        print(f"   Looking for folders starting with 'topic_' in: {source_dir}")
        return
    
    print(f"📂 Found {len(topic_folders)} topic folders")
    print()
    
    total_questions = 0
    total_images = 0
    
    # Process each folder
    for folder in topic_folders:
        folder_name = folder.name
        print(f"Processing: {folder_name}")
        
        # Create output folder
        output_folder = output_path / folder_name
        output_folder.mkdir(exist_ok=True)
        
        # Copy HTML files
        for html_file in ['summary_question.html', 'summary_discussion_ai.html']:
            source_file = folder / html_file
            if source_file.exists():
                shutil.copy2(source_file, output_folder / html_file)
                print(f"  ✓ Copied {html_file}")
            else:
                print(f"  ⚠ Missing {html_file}")
        
        # Copy image files
        image_files = list(folder.glob('image_*.png')) + list(folder.glob('image_*.jpg'))
        for img_file in image_files:
            shutil.copy2(img_file, output_folder / img_file.name)
            total_images += 1
        
        if image_files:
            print(f"  ✓ Copied {len(image_files)} image(s)")
        
        total_questions += 1
        print()
    
    print("=" * 50)
    print("✅ Package created successfully!")
    print(f"📊 Summary:")
    print(f"   - Total questions: {total_questions}")
    print(f"   - Total images: {total_images}")
    print(f"   - Output directory: {output_path.absolute()}")
    print()
    print("📦 Next steps:")
    print("   1. Go to your NotJustExam app")
    print("   2. Click 'Create New Exam'")
    print("   3. Enter an exam name")
    print(f"   4. Upload all files from: {output_path.absolute()}")
    print()
    
    # Optionally create a ZIP file
    create_zip = input("Would you like to create a ZIP file? (y/n): ").lower()
    if create_zip == 'y':
        zip_name = f"{output_dir}.zip"
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in output_path.rglob('*'):
                if folder.is_file():
                    arcname = folder.relative_to(output_path.parent)
                    zipf.write(folder, arcname)
        print(f"✅ Created ZIP file: {zip_name}")

def validate_folder_structure(folder_path: str):
    """Validate a single topic folder structure"""
    folder = Path(folder_path)
    
    print(f"Validating: {folder.name}")
    print("-" * 40)
    
    errors = []
    warnings = []
    
    # Check folder name format
    if not folder.name.startswith('topic_'):
        errors.append("Folder name must start with 'topic_'")
    
    # Check required files
    required_files = ['summary_question.html', 'summary_discussion_ai.html']
    for req_file in required_files:
        file_path = folder / req_file
        if not file_path.exists():
            errors.append(f"Missing required file: {req_file}")
        else:
            print(f"✓ Found: {req_file}")
    
    # Check for images
    image_files = list(folder.glob('image_*.*'))
    if image_files:
        print(f"✓ Found {len(image_files)} image(s)")
    else:
        warnings.append("No images found (optional)")
    
    # Report results
    print()
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"   - {error}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"   - {warning}")
    
    if not errors:
        print("✅ Folder structure is valid!")
    
    print()
    return len(errors) == 0

if __name__ == "__main__":
    print("=" * 50)
    print("NotJustExam - File Upload Helper")
    print("=" * 50)
    print()
    
    print("Choose an option:")
    print("1. Prepare upload package from source directory")
    print("2. Validate single folder structure")
    print()
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    if choice == "1":
        source = input("Enter source directory path: ").strip()
        if os.path.exists(source):
            output = input("Enter output directory name (default: upload_package): ").strip()
            if not output:
                output = "upload_package"
            create_upload_package(source, output)
        else:
            print(f"❌ Directory not found: {source}")
    
    elif choice == "2":
        folder = input("Enter folder path to validate: ").strip()
        if os.path.exists(folder):
            validate_folder_structure(folder)
        else:
            print(f"❌ Folder not found: {folder}")
    
    else:
        print("❌ Invalid choice")
'''

with open('upload_helper.py', 'w', encoding='utf-8') as f:
    f.write(upload_helper)

print("✅ Created: upload_helper.py")
