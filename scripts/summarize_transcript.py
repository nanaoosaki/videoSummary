import os
import re
import sys
from typing import List, Dict, Optional
import json
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
import requests

def get_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    # Try to find video ID in various URL formats
    patterns = [
        r'(?:v=|/v/|youtu\.be/|/embed/)([^&?/]+)',
        r'(?:si=)([^&?/]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match and 'si=' not in pattern:  # Ignore 'si' parameter
            return match.group(1)
    
    return url  # Return as is if no pattern matches

def get_video_title(video_id: str) -> str:
    """Get video title from YouTube using oEmbed endpoint."""
    try:
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()['title']
    except Exception as e:
        print(f"Error getting video title: {str(e)}")
    return f"YouTube Video {video_id}"

def sanitize_filename(title: str) -> str:
    """Convert title to a valid directory name."""
    # Replace special characters with underscores
    sanitized = re.sub(r'[^\w\s-]', '_', title)
    # Replace spaces with underscores and convert to lowercase
    sanitized = re.sub(r'[-\s]+', '_', sanitized).strip('-_').lower()
    return sanitized

def clean_sentence(text: str) -> str:
    """Clean a sentence by removing filler words and repetitions."""
    # Remove filler words and patterns
    text = re.sub(r'\b(um|uh|like|you know|sort of|kind of)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(right|okay|well|so)\b', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(I mean|I think|I guess|I don\'t know)\b', '', text, flags=re.IGNORECASE)
    
    # Clean up repetitive words and stuttering
    text = re.sub(r'\b(\w+)(\s+\1)+\b', r'\1', text, flags=re.IGNORECASE)
    
    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing punctuation except period
    text = text.strip(',.!?:;')
    
    return text.strip()

def extract_key_points(transcript_text: str) -> Dict[str, List[str]]:
    """Extract key points from transcript text using rule-based analysis."""
    # Initialize key points structure
    key_points = {
        "Main Insights": [],
        "Success Principles": [],
        "Practical Tips": [],
        "Challenges & Solutions": [],
        "Key Takeaways": []
    }
    
    # Clean and prepare text
    # Remove timestamps if present
    text = re.sub(r'\[\d+:\d+\]', '', transcript_text)
    
    # Add sentence boundaries
    text = re.sub(r'(?<=[a-z])\s+(?=[A-Z])', '. ', text)
    text = re.sub(r'(?<=[a-z])\s+(?=I\s)', '. ', text)
    
    # Clean up multiple periods and spaces
    text = re.sub(r'\.+', '.', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Split into sentences, handling multiple cases
    sentences = []
    for s in text.split('.'):
        s = clean_sentence(s)
        if len(s) > 30:  # Only consider substantial sentences
            # Further split on common speech patterns
            parts = re.split(r'(?<=[a-z])\s+(?:but|and|or|so|because|however|therefore)\s+', s)
            for part in parts:
                clean_part = clean_sentence(part)
                if len(clean_part) > 30:  # Recheck length after cleaning
                    sentences.append(clean_part + '.')
    
    # Keywords for each category with weights
    keywords = {
        "Main Insights": {
            'important': 2, 'key': 2, 'main': 2, 'essential': 2, 'crucial': 2,
            'fundamental': 2, 'critical': 2, 'true': 2, 'reality': 2, 'fact': 2,
            'truth': 2, 'real': 2
        },
        "Success Principles": {
            'success': 2, 'achieve': 1, 'accomplish': 1, 'win': 1, 'excel': 2,
            'thrive': 2, 'grow': 1, 'wealth': 2, 'power': 2, 'rich': 2,
            'money': 1, 'wealthy': 2, 'successful': 2, 'top': 2, 'best': 2
        },
        "Practical Tips": {
            'should': 1, 'must': 2, 'need to': 2, 'have to': 2, 'tip': 2,
            'advice': 2, 'recommend': 1, 'suggest': 1, 'way to': 2, 'how to': 2,
            'can': 1, 'do this': 2
        },
        "Challenges & Solutions": {
            'problem': 1, 'challenge': 2, 'obstacle': 2, 'difficult': 1,
            'solution': 2, 'overcome': 2, 'handle': 1, 'deal with': 1,
            'solve': 2, 'fix': 1
        },
        "Key Takeaways": {
            'remember': 2, 'takeaway': 2, 'learn': 1, 'understand': 1,
            'realize': 2, 'conclusion': 2, 'point is': 2, 'truth is': 2,
            'bottom line': 2, 'end of day': 2
        }
    }
    
    # Process each sentence
    sentence_scores = {category: [] for category in key_points}
    
    for sentence in sentences:
        sentence_lower = sentence.lower()
        
        # Skip sentences that are too short or seem like transitions
        if len(sentence.split()) < 10:  # Increased minimum length
            continue
            
        # Score each sentence for each category
        for category, word_weights in keywords.items():
            score = 0
            for word, weight in word_weights.items():
                if word in sentence_lower:
                    score += weight
            
            if score > 0:
                # Bonus points for sentences that seem more complete/meaningful
                if re.search(r'\b(is|are|was|were|have|has|do|does|should|must|can|will)\b', sentence_lower):
                    score += 1
                if len(sentence.split()) >= 15:  # Bonus for longer, more complete thoughts
                    score += 1
                if not any(x in sentence_lower for x in ['example', 'instance', 'case']):  # Prefer general statements
                    score += 1
                sentence_scores[category].append((score, sentence))
    
    # Select top sentences for each category based on scores
    for category in key_points:
        scored_sentences = sentence_scores[category]
        if scored_sentences:
            # Sort by score (highest first) and then by length (shorter first if same score)
            sorted_sentences = sorted(scored_sentences, key=lambda x: (-x[0], len(x[1])))
            key_points[category] = [s[1] for s in sorted_sentences[:3]]
    
    return key_points

def create_obsidian_frontmatter(title: str, video_id: str) -> str:
    """Create YAML frontmatter for Obsidian compatibility."""
    current_date = datetime.now().strftime("%Y/%m/%d")
    
    # Escape special characters in title for YAML
    yaml_title = title.replace(":", " -")  # Replace colon with dash
    
    # Create YAML frontmatter
    frontmatter = f"""---
title: "{yaml_title}"
category: career
type: video-notes
source: youtube
videoId: {video_id}
createdDate: {current_date}
tags:
  - career-advice
  - corporate-life
  - professional-development
status: completed
---
"""
    return frontmatter

def update_markdown_with_summary(video_info_path: str, key_points: Dict[str, List[str]]):
    """Update the video_info.md file with extracted key points and Obsidian frontmatter."""
    with open(video_info_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title and video ID from existing content
    title_match = re.search(r'## Title\n(.*?)\n', content)
    video_id_match = re.search(r'## Video ID\n(.*?)\n', content)
    
    if title_match and video_id_match:
        title = title_match.group(1).strip()
        video_id = video_id_match.group(1).strip()
        
        # Create frontmatter
        frontmatter = create_obsidian_frontmatter(title, video_id)
        
        # Remove any existing frontmatter
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # Add new frontmatter at the top
        content = frontmatter + content
    
    # Update processing status
    content = re.sub(r'- \[ \] Key points extracted', '- [x] Key points extracted', content)
    content = re.sub(r'- \[ \] Summary generated', '- [x] Summary generated', content)
    
    # Remove existing Summary and Key Points sections if they exist
    content = re.sub(r'\n## Summary\n.*?(?=\n## |$)', '', content, flags=re.DOTALL)
    content = re.sub(r'\n## Key Points\n.*?(?=\n## |$)', '', content, flags=re.DOTALL)
    
    # Create new Key Points section
    key_points_section = "\n## Key Points\n"
    for category, points in key_points.items():
        if points:  # Only add categories that have points
            key_points_section += f"\n### {category}\n"
            for point in points:
                key_points_section += f"- {point}\n"
    
    # Add the key points section before the Notes section
    if "## Notes" in content:
        content = content.replace("## Notes", f"{key_points_section}\n## Notes")
    else:
        content += f"\n{key_points_section}"
    
    with open(video_info_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_initial_video_info(video_id: str, video_url: str) -> str:
    """Create initial video info markdown file."""
    # Get video title from YouTube
    video_title = get_video_title(video_id)
    
    content = f"""---
title: "{video_title}"
category: career
type: video-notes
source: youtube
videoId: {video_id}
createdDate: {datetime.now().strftime("%Y/%m/%d")}
tags:
  - career-advice
  - professional-development
status: in-progress
---
# Video Information

## Title
{video_title}

## Video URL
{video_url}

## Video ID
{video_id}

## Directory Name
{sanitize_filename(video_title)}

## Files
- `transcript.txt`: Human-readable transcript with timestamps
- `transcript.json`: Raw transcript data in JSON format
- `key_points.txt`: Extracted key points in human-readable format
- `key_points.json`: Structured key points data

## Processing Status
- [x] Transcript downloaded
- [ ] Key points extracted
- [ ] Summary generated
"""
    return content

def main():
    """Process transcripts and update markdown files."""
    # Get video URL from command line if provided
    if len(sys.argv) > 1:
        video_url = sys.argv[1]
        video_id = get_video_id(video_url)
        
        try:
            # Get transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = ' '.join([entry['text'] for entry in transcript])
            
            # Get video title and create sanitized directory name
            video_title = get_video_title(video_id)
            dir_name = sanitize_filename(video_title)
            
            # Create output directory using sanitized title
            video_dir = f"output/{dir_name}"
            os.makedirs(video_dir, exist_ok=True)
            
            # Save transcript
            with open(f"{video_dir}/transcript.txt", 'w', encoding='utf-8') as f:
                f.write(transcript_text)
            
            # Save raw transcript data
            with open(f"{video_dir}/transcript.json", 'w', encoding='utf-8') as f:
                json.dump(transcript, f, indent=2)
            
            # Create initial video info file if it doesn't exist
            video_info_path = f"{video_dir}/video_info.md"
            if not os.path.exists(video_info_path):
                initial_content = create_initial_video_info(video_id, video_url)
                with open(video_info_path, 'w', encoding='utf-8') as f:
                    f.write(initial_content)
            
            # Extract and save key points
            key_points = extract_key_points(transcript_text)
            
            # Save key points to separate files
            with open(f"{video_dir}/key_points.json", 'w', encoding='utf-8') as f:
                json.dump(key_points, f, indent=2)
            
            # Save human-readable key points
            with open(f"{video_dir}/key_points.txt", 'w', encoding='utf-8') as f:
                for category, points in key_points.items():
                    if points:
                        f.write(f"\n{category}\n{'=' * len(category)}\n")
                        for point in points:
                            f.write(f"- {point}\n")
            
            # Update markdown
            update_markdown_with_summary(video_info_path, key_points)
            
            print(f"Processed video: {video_title}")
            print(f"Output directory: {video_dir}")
            print("Files created:")
            print(f"- {video_dir}/transcript.txt")
            print(f"- {video_dir}/transcript.json")
            print(f"- {video_dir}/key_points.txt")
            print(f"- {video_dir}/key_points.json")
            print(f"- {video_dir}/video_info.md")
            
        except Exception as e:
            print(f"Error processing video {video_id}: {str(e)}")
            return
    
    # Process existing directories
    output_dir = "output"
    for video_dir in os.listdir(output_dir):
        video_dir_path = os.path.join(output_dir, video_dir)
        if not os.path.isdir(video_dir_path):
            continue
        
        # Check for required files
        transcript_path = os.path.join(video_dir_path, "transcript.txt")
        video_info_path = os.path.join(video_dir_path, "video_info.md")
        
        if not (os.path.exists(transcript_path) and os.path.exists(video_info_path)):
            continue
        
        print(f"Processing {video_dir}...")
        
        # Read transcript
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_text = f.read()
        
        # Extract key points
        key_points = extract_key_points(transcript_text)
        
        # Save key points to separate files
        with open(os.path.join(video_dir_path, "key_points.json"), 'w', encoding='utf-8') as f:
            json.dump(key_points, f, indent=2)
        
        # Save human-readable key points
        with open(os.path.join(video_dir_path, "key_points.txt"), 'w', encoding='utf-8') as f:
            for category, points in key_points.items():
                if points:
                    f.write(f"\n{category}\n{'=' * len(category)}\n")
                    for point in points:
                        f.write(f"- {point}\n")
        
        # Update markdown
        update_markdown_with_summary(video_info_path, key_points)
        
        print(f"Updated summary for {video_dir}")
        print("Files updated:")
        print(f"- {video_dir_path}/key_points.txt")
        print(f"- {video_dir_path}/key_points.json")
        print(f"- {video_dir_path}/video_info.md")

if __name__ == "__main__":
    main() 