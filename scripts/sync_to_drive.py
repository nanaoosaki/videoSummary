import os
import shutil
import re

def get_video_title_from_md(md_path: str) -> str:
    """Extract video title from markdown file."""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find title line
    match = re.search(r'## Title\s*\n+([^\n]+)', content)
    if match:
        return match.group(1).strip()
    return None

def sanitize_filename(title: str) -> str:
    """Convert title to a valid filename."""
    # Remove invalid characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores
    title = title.replace(' ', '_')
    # Ensure filename doesn't exceed max length (255 chars)
    return title[:255] + '.md'

def sync_to_drive(source_dir: str, drive_path: str):
    """Sync markdown files to Google Drive."""
    # Ensure drive directory exists
    if not os.path.exists(drive_path):
        print(f"Error: Drive path {drive_path} does not exist")
        return
    
    # Process each video directory
    for video_dir in os.listdir(source_dir):
        video_dir_path = os.path.join(source_dir, video_dir)
        if not os.path.isdir(video_dir_path):
            continue
        
        # Check for video_info.md
        md_path = os.path.join(video_dir_path, "video_info.md")
        if not os.path.exists(md_path):
            continue
        
        # Get video title
        title = get_video_title_from_md(md_path)
        if not title:
            print(f"Warning: Could not extract title from {md_path}")
            continue
        
        # Create destination filename
        dest_filename = sanitize_filename(title)
        dest_path = os.path.join(drive_path, dest_filename)
        
        # Copy file
        try:
            shutil.copy2(md_path, dest_path)
            print(f"Copied {md_path} to {dest_path}")
        except Exception as e:
            print(f"Error copying {md_path}: {str(e)}")

def main():
    """Main function to sync files to Google Drive."""
    output_dir = "output"
    drive_path = r"G:\My Drive\AI"
    
    if not os.path.exists(drive_path):
        print(f"Error: Drive path {drive_path} does not exist")
        return
    
    print(f"Syncing files to {drive_path}...")
    sync_to_drive(output_dir, drive_path)
    print("Sync complete!")

if __name__ == "__main__":
    main() 