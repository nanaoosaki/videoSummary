# YouTube Video Summary Tool

A Python-based tool for automatically extracting, analyzing, and summarizing YouTube video transcripts. The tool creates well-structured markdown files with key points extraction, perfect for knowledge management systems like Obsidian.

## Features

- Automatic transcript downloading from YouTube videos
- Intelligent key points extraction using weighted keyword analysis
- Clean text processing for speech patterns
- Obsidian-compatible markdown generation
- Google Drive sync functionality
- Proper file organization with sanitized video titles

## Directory Structure

```
output/
  video_title/
    - video_info.md      # Main markdown file with YAML frontmatter
    - transcript.txt     # Human-readable transcript
    - transcript.json    # Raw transcript data
    - key_points.txt     # Human-readable key points
    - key_points.json    # Structured key points data
scripts/
    - summarize_transcript.py    # Main processing script
    - sync_to_drive.py          # Google Drive sync utility
```

## Key Points Categories

The tool extracts key points in five categories:
1. Main Insights
2. Success Principles
3. Practical Tips
4. Challenges & Solutions
5. Key Takeaways

## Usage

1. Install dependencies:
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

2. Process a video:
```bash
python scripts/summarize_transcript.py "https://youtu.be/VIDEO_ID"
```

3. The script will:
   - Download the transcript
   - Extract key points
   - Generate markdown files
   - Sync to Google Drive (if configured)

## YAML Frontmatter

Each video_info.md file includes:
- title
- category
- type
- source
- videoId
- createdDate
- tags
- status

## Requirements

- Python 3.8+
- youtube_transcript_api
- requests

## License

MIT License - see LICENSE file for details
