"""
File Upload Helper Script (Enhanced)

This script helps prepare your question folders for upload to NotJustExam

Now with automatic ZIP file creation and metadata.json support!
"""

import os
import shutil
from pathlib import Path
import zipfile
import json
from datetime import datetime

def get_folder_last_modified(folder_path: Path) -> str:
    """
    Get the last modified timestamp of the most recently modified file in a folder

    Args:
        folder_path: Path to the folder to check

    Returns:
        ISO formatted timestamp string or None if no files found
    """
    if not folder_path.exists():
        return None

    latest_time = 0

    # Check all files in this folder
    for file_path in folder_path.rglob('*'):
        if file_path.is_file():
            try:
                mtime = os.path.getmtime(file_path)
                if mtime > latest_time:
                    latest_time = mtime
            except OSError:
                continue

    if latest_time == 0:
        return None

    return datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M:%S')

def create_question_metadata(folderpath: Path) -> dict:
    """
    Create metadata for a question folder including last_update_date timestamp.
    
    Args:
        folderpath: Path to the question folder
        
    Returns:
        Dictionary with metadata including last_update_date
    """
    metadata = {
        "folder_name": folderpath.name,
        "last_update_date": get_folder_last_modified(folderpath) or datetime.now().strftime("%Y-%m-%d %H:%M:%S HKT")
    }
    
    # Check for HTML files
    has_question = (folderpath / "summary_question.html").exists()
    has_discussion = (folderpath / "summary_discussion_ai.html").exists()
    metadata["has_question"] = has_question
    metadata["has_discussion"] = has_discussion
    
    # Count images
    image_files = list(folderpath.glob("image*.png")) + list(folderpath.glob("image*.jpg"))
    metadata["image_count"] = len(image_files)
    
    return metadata

def create_upload_package(source_dir: str, output_dir: str = "upload_package", create_zip: bool = True):
    """
    Prepare question folders for upload to NotJustExam

    Args:
        source_dir: Directory containing your topic_X_question_Y folders
        output_dir: Directory to create the upload package
        create_zip: Automatically create ZIP file (default: True)
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
        return None

    print(f"📂 Found {len(topic_folders)} topic folders")
    print()

    total_questions = 0
    total_images = 0
    metadata_list = []
    folders_with_metadata = 0
    folders_without_metadata = 0

    # Process each folder
    for folder in topic_folders:
        folder_name = folder.name
        print(f"Processing: {folder_name}")

        # Create metadata for this question
        metadata = create_question_metadata(folder)
        metadata_list.append(metadata)

        # Create output folder
        output_folder = output_path / folder_name
        output_folder.mkdir(exist_ok=True)

        # Copy HTML files
        for html_file in ['summary_question.html', 'summary_discussion_ai.html']:
            source_file = folder / html_file
            if source_file.exists():
                shutil.copy2(source_file, output_folder / html_file)
                print(f"   ✓ Copied {html_file}")
            else:
                print(f"   ⚠ Missing {html_file}")

        # Copy metadata.json if exists
        metadata_json = folder / 'metadata.json'
        if metadata_json.exists():
            shutil.copy2(metadata_json, output_folder / 'metadata.json')
            print(f"   ✓ Copied metadata.json")
            folders_with_metadata += 1

            # Try to read and show timestamp from metadata.json
            try:
                with open(metadata_json, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    if 'last_update_date' in meta:
                        print(f"   📅 {meta['last_update_date']}")
            except:
                pass
        else:
            print(f"   ⚠ Missing metadata.json")
            folders_without_metadata += 1

        # Copy image files
        image_files = list(folder.glob('image_*.png')) + list(folder.glob('image_*.jpg'))
        for img_file in image_files:
            shutil.copy2(img_file, output_folder / img_file.name)
            total_images += 1

        if image_files:
            print(f"   ✓ Copied {len(image_files)} image(s)")

        total_questions += 1
        print()

    # Save metadata to JSON file in the output directory
    metadata_file = output_path / 'upload_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump({
            "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "total_questions": total_questions,
            "total_images": total_images,
            "questions": metadata_list
        }, f, indent=2)

    print(f"✅ Created root metadata file: upload_metadata.json")

    print("=" * 50)
    print("✅ Package created successfully!")
    print(f"📊 Summary:")
    print(f"   - Total questions: {total_questions}")
    print(f"   - With metadata.json: {folders_with_metadata}")
    print(f"   - Without metadata.json: {folders_without_metadata}")
    print(f"   - Total images: {total_images}")
    print(f"   - Output directory: {output_path.absolute()}")

    if folders_without_metadata > 0:
        print(f"\n⚠️  WARNING: {folders_without_metadata} folders missing metadata.json")
        print(f"   Run: python metadata_scanner.py {source_dir}")
        print(f"   This will generate metadata.json files with timestamps")

    print()

    # Create ZIP file
    zip_path = None
    if create_zip:
        zip_name = f"{output_dir}.zip"
        zip_path = create_zip_file(output_path, zip_name)

        if zip_path:
            print(f"✅ Created ZIP file: {zip_path}")
            print(f"   Size: {os.path.getsize(zip_path) / 1024:.1f} KB")

    print()
    print("📦 Next steps:")
    print("   1. Go to your NotJustExam app")
    print("   2. Click 'Create New Exam'")
    print("   3. Enter an exam name")
    if zip_path:
        print(f"   4. Upload ZIP file: {zip_path}")
    else:
        print(f"   4. Upload all files from: {output_path.absolute()}")
    print()

    return zip_path

def create_zip_file(source_dir: Path, zip_name: str) -> str:
    """
    Create a ZIP file from directory contents

    Args:
        source_dir: Directory to zip
        zip_name: Name of output ZIP file

    Returns:
        Path to created ZIP file
    """
    try:
        zip_path = Path(zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files maintaining folder structure
            for file_path in source_dir.rglob('*'):
                if file_path.is_file():
                    # Create archive name relative to parent of source_dir
                    arcname = file_path.relative_to(source_dir.parent)
                    zipf.write(file_path, arcname)

        return str(zip_path.absolute())

    except Exception as e:
        print(f"❌ Error creating ZIP file: {str(e)}")
        return None

def validate_folder_structure(folder_path: str) -> bool:
    """Validate a single topic folder structure"""
    folder = Path(folder_path)

    print(f"Validating: {folder.name}")
    print("-" * 40)

    errors = []
    warnings = []

    # Check folder name format
    if not folder.name.startswith('topic_'):
        errors.append("Folder name must start with 'topic_'")
    else:
        # Validate naming pattern
        import re
        if not re.match(r'topic_\d+_question_\d+', folder.name):
            errors.append("Folder name must follow pattern: topic_X_question_Y")

    # Check required files
    required_files = ['summary_question.html', 'summary_discussion_ai.html']

    for req_file in required_files:
        file_path = folder / req_file
        if not file_path.exists():
            errors.append(f"Missing required file: {req_file}")
        else:
            print(f"✓ Found: {req_file}")
            # Validate file is not empty
            if os.path.getsize(file_path) == 0:
                warnings.append(f"{req_file} is empty")

    # Check for metadata.json
    metadata_json = folder / 'metadata.json'
    if metadata_json.exists():
        print(f"✓ Found: metadata.json")
        try:
            with open(metadata_json, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            if 'last_update_date' in meta:
                print(f"  📅 {meta['last_update_date']}")
            else:
                warnings.append("metadata.json missing 'last_update_date' key")
        except:
            warnings.append("metadata.json is invalid/corrupted")
    else:
        warnings.append("metadata.json not found - timestamps may not work correctly")

    # Check for images
    image_files = list(folder.glob('image_*.*'))
    if image_files:
        print(f"✓ Found {len(image_files)} image(s)")
        # Validate image naming
        for img in image_files:
            if not (img.suffix.lower() in ['.png', '.jpg', '.jpeg']):
                warnings.append(f"Unsupported image format: {img.name}")
    else:
        warnings.append("No images found (optional)")

    # Get and display last_updated (fallback method)
    last_updated = get_folder_last_modified(folder)
    if last_updated and not metadata_json.exists():
        print(f"📅 Last modified: {last_updated}")

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

def validate_all_folders(source_dir: str) -> bool:
    """
    Validate all topic folders in a directory

    Args:
        source_dir: Directory containing topic folders

    Returns:
        True if all folders are valid, False otherwise
    """
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"❌ Directory not found: {source_dir}")
        return False

    # Find all topic folders
    topic_folders = sorted([d for d in source_path.iterdir() 
                           if d.is_dir() and d.name.startswith('topic_')])

    if not topic_folders:
        print(f"❌ No topic folders found in: {source_dir}")
        return False

    print(f"📂 Found {len(topic_folders)} topic folders to validate")
    print("=" * 50)
    print()

    all_valid = True
    for folder in topic_folders:
        if not validate_folder_structure(str(folder)):
            all_valid = False
        print()

    print("=" * 50)
    if all_valid:
        print("✅ All folders are valid!")
    else:
        print("❌ Some folders have errors. Please fix them before uploading.")

    return all_valid

def create_zip_from_existing(source_dir: str, zip_name: str = None) -> str:
    """
    Create a ZIP file directly from an existing directory structure

    Args:
        source_dir: Directory containing topic folders
        zip_name: Optional custom ZIP filename

    Returns:
        Path to created ZIP file
    """
    source_path = Path(source_dir)

    if not source_path.exists():
        print(f"❌ Directory not found: {source_dir}")
        return None

    # Validate first
    print("Validating folders...")
    if not validate_all_folders(source_dir):
        print()
        create_anyway = input("Validation failed. Create ZIP anyway? (y/n): ").lower()
        if create_anyway != 'y':
            print("❌ Cancelled")
            return None

    print()

    # Generate ZIP name if not provided
    if not zip_name:
        dir_name = source_path.name
        zip_name = f"{dir_name}_exam.zip"

    # Ensure .zip extension
    if not zip_name.endswith('.zip'):
        zip_name += '.zip'

    print(f"Creating ZIP file: {zip_name}")

    try:
        # Create metadata for all questions
        topic_folders = [d for d in source_path.iterdir() 
                        if d.is_dir() and d.name.startswith('topic_')]

        metadata_list = []
        folders_with_metadata = 0

        for folder in topic_folders:
            metadata = create_question_metadata(folder)
            metadata_list.append(metadata)

            # Check if metadata.json exists
            if (folder / 'metadata.json').exists():
                folders_with_metadata += 1

        # Create temporary metadata file at root
        temp_metadata = source_path / 'upload_metadata.json'
        with open(temp_metadata, 'w', encoding='utf-8') as f:
            json.dump({
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "total_questions": len(topic_folders),
                "questions": metadata_list
            }, f, indent=2)

        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            file_count = 0

            for folder in topic_folders:
                # Add all files from this folder (including metadata.json if present)
                for file_path in folder.rglob('*'):
                    if file_path.is_file():
                        # Create archive path: topic_X_question_Y/filename
                        arcname = file_path.relative_to(source_path)
                        zipf.write(file_path, arcname)
                        file_count += 1

            # Add root metadata file
            zipf.write(temp_metadata, 'upload_metadata.json')
            file_count += 1

        # Remove temporary metadata file
        temp_metadata.unlink()

        zip_path = Path(zip_name).absolute()

        print()
        print("=" * 50)
        print("✅ ZIP file created successfully!")
        print(f"   Path: {zip_path}")
        print(f"   Size: {os.path.getsize(zip_path) / 1024:.1f} KB")
        print(f"   Files: {file_count}")
        print(f"   Folders with metadata.json: {folders_with_metadata}/{len(topic_folders)}")

        if folders_with_metadata < len(topic_folders):
            print(f"\n⚠️  {len(topic_folders) - folders_with_metadata} folders missing metadata.json")
            print(f"   Run: python metadata_scanner.py {source_dir}")

        print()
        print("📦 Ready to upload to NotJustExam!")
        print("=" * 50)

        return str(zip_path)

    except Exception as e:
        print(f"❌ Error creating ZIP: {str(e)}")
        if temp_metadata.exists():
            temp_metadata.unlink()
        return None

def interactive_menu():
    """Interactive menu for all operations"""
    print("=" * 50)
    print("NotJustExam - File Upload Helper (Enhanced)")
    print("=" * 50)
    print()
    print("Choose an option:")
    print("1. Create ZIP file from existing folders (Quick)")
    print("2. Prepare upload package + create ZIP")
    print("3. Validate single folder")
    print("4. Validate all folders in directory")
    print("5. Exit")
    print()

    choice = input("Enter choice (1-5): ").strip()

    if choice == "1":
        print()
        source = input("Enter directory path containing topic folders: ").strip()
        if os.path.exists(source):
            zip_name = input("Enter ZIP filename (press Enter for default): ").strip()
            if not zip_name:
                zip_name = None
            create_zip_from_existing(source, zip_name)
        else:
            print(f"❌ Directory not found: {source}")

    elif choice == "2":
        print()
        source = input("Enter source directory path: ").strip()
        if os.path.exists(source):
            output = input("Enter output directory name (default: upload_package): ").strip()
            if not output:
                output = "upload_package"
            create_upload_package(source, output, create_zip=True)
        else:
            print(f"❌ Directory not found: {source}")

    elif choice == "3":
        print()
        folder = input("Enter folder path to validate: ").strip()
        if os.path.exists(folder):
            validate_folder_structure(folder)
        else:
            print(f"❌ Folder not found: {folder}")

    elif choice == "4":
        print()
        source = input("Enter directory path containing topic folders: ").strip()
        if os.path.exists(source):
            validate_all_folders(source)
        else:
            print(f"❌ Directory not found: {source}")

    elif choice == "5":
        print("Goodbye!")
        return False

    else:
        print("❌ Invalid choice")

    print()
    return True

if __name__ == "__main__":
    # Run interactive menu
    while interactive_menu():
        input("Press Enter to continue...")
        print("\n" * 2)
