from youtube_transcript_api import YouTubeTranscriptApi
import sys
import json
import os
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests

def get_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Try different URL patterns
    patterns = [
        r'(?:v=|/)([a-zA-Z0-9_-]{11})(?:\?|&|/|$)',  # Standard and shortened URLs
        r'^([a-zA-Z0-9_-]{11})$'  # Direct video ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_id: str) -> Tuple[str, str]:
    """Get video title using YouTube's oEmbed endpoint."""
    try:
        # Use YouTube's oEmbed endpoint (no API key required)
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(oembed_url)
        response.raise_for_status()
        data = response.json()
        return data['title'], 'en'  # Assuming English for now
    except Exception as e:
        print(f"Warning: Could not fetch video title: {str(e)}")
        return f"YouTube Video {video_id}", 'en'

def sanitize_filename(title: str) -> str:
    """Convert title to a valid filename."""
    # Remove invalid characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces with underscores
    title = title.replace(' ', '_').lower()
    # Ensure filename doesn't exceed max length
    return title[:100]

def ensure_output_dir(video_id: str, title: str) -> str:
    """Create output directory if it doesn't exist."""
    # Create main output directory
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create video-specific directory with title
    sanitized_title = sanitize_filename(title)
    new_dir_name = f"{sanitized_title}_{video_id}"
    new_dir_path = os.path.join(output_dir, new_dir_name)
    
    # Check for existing directories with this video ID
    for dir_name in os.listdir(output_dir):
        dir_path = os.path.join(output_dir, dir_name)
        if os.path.isdir(dir_path) and video_id in dir_name:
            if dir_name != new_dir_name:  # Only remove if it's a different name
                print(f"Removing old directory: {dir_path}")
                import shutil
                shutil.rmtree(dir_path)
    
    # Create the new directory
    os.makedirs(new_dir_path, exist_ok=True)
    return new_dir_path

def get_transcript(video_url: str, language: str = 'en') -> Optional[List[Dict]]:
    """
    Get the transcript for a YouTube video.
    
    Args:
        video_url: The URL or ID of the YouTube video
        language: The language code for the transcript (default: 'en')
    
    Returns:
        A list of dictionaries containing transcript segments with text and timestamps,
        or None if no transcript is available
    """
    try:
        video_id = get_video_id(video_url)
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        return transcript
    except Exception as e:
        print(f"Error getting transcript: {str(e)}", file=sys.stderr)
        return None

def format_transcript(transcript: List[Dict]) -> str:
    """
    Format the transcript into a readable text.
    
    Args:
        transcript: List of transcript segments
    
    Returns:
        Formatted transcript text with timestamps
    """
    if not transcript:
        return "No transcript available."
    
    formatted_text = []
    for segment in transcript:
        timestamp = int(segment['start'])
        minutes = timestamp // 60
        seconds = timestamp % 60
        formatted_text.append(f"[{minutes:02d}:{seconds:02d}] {segment['text']}")
    
    return "\n".join(formatted_text)

def save_transcript(transcript_list: list, output_dir: str):
    """Save transcript in both JSON and formatted text."""
    # Save raw JSON
    json_path = os.path.join(output_dir, "transcript.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_list, f, indent=2, ensure_ascii=False)
    print(f"Raw transcript saved to {json_path}")
    
    # Save formatted text
    txt_path = os.path.join(output_dir, "transcript.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        for entry in transcript_list:
            timestamp = int(entry['start'])
            minutes = timestamp // 60
            seconds = timestamp % 60
            f.write(f"[{minutes:02d}:{seconds:02d}] {entry['text']}\n")
    
    print(f"Formatted transcript saved to {txt_path}")
    
    # Print first few lines
    print("\nFirst few lines of formatted transcript:")
    print("-" * 50)
    with open(txt_path, 'r', encoding='utf-8') as f:
        print("".join(f.readlines()[:5]))
    print("-" * 50)

def update_video_info(output_dir: str, video_id: str, url: str, title: str):
    """Create or update video_info.md file."""
    md_path = os.path.join(output_dir, "video_info.md")
    content = f"""# Video Information

## Title
{title}

## Video URL
{url}

## Video ID
{video_id}

## Directory Name
{os.path.basename(output_dir)}

## Files
- `transcript.txt`: Human-readable transcript with timestamps
- `transcript.json`: Raw transcript data in JSON format
- `key_points.txt`: Extracted key points in human-readable format (to be generated)
- `key_points.json`: Structured key points data (to be generated)

## Processing Status
- [x] Transcript downloaded
- [ ] Key points extracted
- [ ] Summary generated

## Notes
- Transcript downloaded on: {os.path.basename(output_dir)}
"""
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """Main function to extract transcript."""
    if len(sys.argv) != 2:
        print("Usage: python transcript_extractor.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    video_id = get_video_id(url)
    if not video_id:
        print(f"Error: Could not extract video ID from URL: {url}")
        sys.exit(1)
    
    print(f"Extracting transcript from: {url}")
    
    try:
        # Get video info
        title, language = get_video_info(video_id)
        print(f"Video title: {title}")
        
        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Create output directory
        output_dir = ensure_output_dir(video_id, title)
        
        # Save transcript
        save_transcript(transcript_list, output_dir)
        
        # Update video info
        update_video_info(output_dir, video_id, url, title)
        
    except Exception as e:
        print(f"Error extracting transcript: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 