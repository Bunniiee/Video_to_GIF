import os
import subprocess
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
import yt_dlp
import tempfile
import uuid
import openai
from dotenv import load_dotenv
import re
import requests
from urllib.parse import urlparse, parse_qs
import numpy as np
from datetime import timedelta
from moviepy.config import change_settings
import whisper
from pathlib import Path

# Load environment variables
load_dotenv()

# Configure ImageMagick path based on environment
if os.getenv('FLASK_ENV') == 'production':
    IMAGEMAGICK_PATH = '/usr/bin/magick'
    FFMPEG_PATH = '/usr/bin/ffmpeg'
else:
    IMAGEMAGICK_PATH = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    FFMPEG_PATH = r"C:\ffmpeg\bin\ffmpeg.exe"

# Configure ImageMagick path
change_settings({"IMAGEMAGICK_BINARY": IMAGEMAGICK_PATH})

# Set FFmpeg path for Whisper
os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + os.pathsep + os.environ["PATH"]

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# Initialize OpenAI client
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Whisper model
print("Initializing Whisper model...")
try:
    whisper_model = whisper.load_model("base")
    print("Whisper model loaded successfully")
except Exception as e:
    print(f"Error loading Whisper model: {str(e)}")
    print("Please ensure Whisper is installed correctly: pip install openai-whisper")
    whisper_model = None

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        # Try multiple possible FFmpeg paths
        ffmpeg_paths = [
            'ffmpeg',  # System PATH
            'C:\\ffmpeg\\bin\\ffmpeg.exe',  # Windows default installation
            'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
            'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe'
        ]
        
        for path in ffmpeg_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                     capture_output=True, 
                                     text=True, 
                                     check=True)
                if result.returncode == 0:
                    print(f"FFmpeg found at: {path}")
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
                
        print("FFmpeg not found in any of the expected locations")
        return False
        
    except Exception as e:
        print(f"Error checking FFmpeg: {str(e)}")
        return False

def check_imagemagick():
    """Check if ImageMagick is installed and accessible."""
    try:
        # Try multiple possible ImageMagick paths
        imagemagick_paths = [
            'magick',  # System PATH
            r'C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe',
            r'C:\Program Files (x86)\ImageMagick-7.1.1-Q16-HDRI\magick.exe'
        ]
        
        for path in imagemagick_paths:
            try:
                result = subprocess.run([path, '-version'], 
                                     capture_output=True, 
                                     text=True, 
                                     check=True)
                if result.returncode == 0:
                    print(f"ImageMagick found at: {path}")
                    return True
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
                
        print("ImageMagick not found in any of the expected locations")
        return False
        
    except Exception as e:
        print(f"Error checking ImageMagick: {str(e)}")
        return False

def download_youtube_video(url):
    try:
        print(f"Attempting to download YouTube video from: {url}")
        
        # Store the original URL for caption extraction
        original_url = url
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'best[ext=mp4]',  # Best quality MP4
            'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], f'{uuid.uuid4()}.mp4'),
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [lambda d: print(f"Download progress: {d.get('_percent_str', '0%')}")],
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_color': True,
            'extract_flat': False,
            'force_generic_extractor': False,
        }
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Starting download...")
            try:
                info = ydl.extract_info(url, download=True)
                if info is None:
                    raise ValueError("Failed to extract video information")
                video_path = ydl.prepare_filename(info)
                if not os.path.exists(video_path):
                    raise ValueError("Video file was not created")
                print(f"Video downloaded successfully to: {video_path}")
                # Return both the video path and original URL
                return video_path, original_url
            except Exception as e:
                print(f"Error during download: {str(e)}")
                print("Trying alternative format...")
                # Try alternative format if best quality fails
                ydl_opts['format'] = 'mp4'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=True)
                    if info is None:
                        raise ValueError("Failed to extract video information with alternative format")
                    video_path = ydl2.prepare_filename(info)
                    if not os.path.exists(video_path):
                        raise ValueError("Video file was not created with alternative format")
                    print(f"Video downloaded successfully with alternative format to: {video_path}")
                    return video_path, original_url
            
    except Exception as e:
        print(f"Error downloading YouTube video: {str(e)}")
        raise ValueError(f"Failed to download YouTube video: {str(e)}")

def transcribe_video(video_path, youtube_url=None):
    """Step 1: Generate full transcript using Whisper or YouTube captions."""
    print(f"\n=== Step 1: Generating Transcript ===")
    print(f"Video path: {video_path}")
    print(f"YouTube URL: {youtube_url}")
    
    # Get video duration
    print("Getting video duration...")
    try:
        result = subprocess.run(
            [FFMPEG_PATH, "-i", video_path],
            capture_output=True,
            text=True
        )
        duration_match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})", result.stderr)
        if duration_match:
            hours, minutes, seconds = map(int, duration_match.groups())
            duration = hours * 3600 + minutes * 60 + seconds
            print(f"Video duration: {duration:.2f} seconds")
        else:
            print("Could not determine video duration")
            duration = 0
    except Exception as e:
        print(f"Error getting video duration: {str(e)}")
        duration = 0

    # Try to get YouTube captions first
    if youtube_url:
        print("\nAttempting to get YouTube captions...")
        try:
            ydl_opts = {
                'writesubtitles': True,
                'writeautomaticsub': True,
                'subtitleslangs': ['en'],
                'skip_download': True,
                'quiet': True,
                'verbose': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                print("Video info extracted successfully")
                
                if 'subtitles' in info:
                    print("Found manual captions")
                    available_langs = list(info['subtitles'].keys())
                    print(f"Available caption languages: {available_langs}")
                    
                    if 'en' in available_langs:
                        print("Using captions in language: en")
                        caption_data = info['subtitles']['en']
                        if caption_data:
                            segments = []
                            for entry in caption_data:
                                if 'data' in entry:
                                    segments.append({
                                        'start': entry.get('start', 0),
                                        'end': entry.get('end', 0),
                                        'text': entry['data']
                                    })
                            if segments:
                                print(f"Extracted {len(segments)} caption segments")
                                return segments, duration
                
                print("No caption data found in selected language")
        except Exception as e:
            print(f"Error getting YouTube captions: {str(e)}")
    
    # Fallback to Whisper
    print("\nUsing Whisper for transcription...")
    if not whisper_model:
        print("Whisper model not initialized")
        return None, duration
    
    try:
        print("Loading video into Whisper...")
        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"Error: Video file not found at {video_path}")
            return None, duration
            
        # Get file size
        file_size = os.path.getsize(video_path) / (1024 * 1024)  # Convert to MB
        print(f"Video file size: {file_size:.2f} MB")
        
        # Try with default parameters first
        try:
            result = whisper_model.transcribe(video_path)
        except Exception as e:
            print(f"Whisper transcription error: {str(e)}")
            print("Trying to transcribe with different parameters...")
            # Try with different parameters
            result = whisper_model.transcribe(
                video_path,
                language="en",
                fp16=False,  # Force CPU mode
                verbose=True
            )
        
        if result and 'segments' in result:
            segments = []
            for segment in result['segments']:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip()
                })
            print(f"Successfully transcribed {len(segments)} segments")
            return segments, duration
        else:
            print("No segments found in transcription result")
            return None, duration
            
    except Exception as e:
        print(f"Whisper transcription failed: {str(e)}")
        print("Full error traceback:")
        import traceback
        traceback.print_exc()
        return None, duration

def find_relevant_segments(transcript, theme_prompt, num_segments=3):
    """Step 2: Analyze transcript to find key caption-worthy lines."""
    print(f"\n=== Step 2: Finding Key Segments ===")
    print(f"Theme prompt: {theme_prompt}")
    
    if not transcript:
        print("No transcript available")
        return None
        
    print(f"Total segments in transcript: {len(transcript)}")
    
    try:
        # Use OpenAI to analyze segments and find relevant ones
        prompt = f"""Given these video transcript segments and the theme '{theme_prompt}', 
        identify the {num_segments} most engaging and caption-worthy moments.
        For each segment, provide:
        1. The segment number (0-based index)
        2. The complete caption text that captures the essence
        Format each line as: segment_index,caption_text
        
        Segments:
        {[f"{i}: {s['text']}" for i, s in enumerate(transcript)]}
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that identifies engaging moments in video transcripts."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse response to get segment indices and captions
        lines = response.choices[0].message.content.strip().split('\n')
        selected_segments = []
        
        for line in lines:
            if ',' in line:
                idx, caption = line.split(',', 1)
                try:
                    idx = int(idx.strip())
                    if 0 <= idx < len(transcript):
                        segment = transcript[idx].copy()
                        segment['text'] = caption.strip()
                        selected_segments.append(segment)
                except ValueError:
                    continue
        
        if selected_segments:
            print(f"Found {len(selected_segments)} relevant segments")
            return selected_segments
            
    except Exception as e:
        print(f"Error finding relevant segments: {str(e)}")
    
    # Fallback: Select segments with the most text content
    print("Falling back to text-based selection...")
    segments_with_text = [s for s in transcript if len(s['text'].strip()) > 0]
    if not segments_with_text:
        return None
        
    # Sort by text length and take top segments
    segments_with_text.sort(key=lambda x: len(x['text']), reverse=True)
    selected_segments = segments_with_text[:num_segments]
    
    # Keep the complete text for each segment
    for segment in selected_segments:
        # Clean up the text but keep it complete
        text = segment['text'].strip()
        # Remove any trailing punctuation that might make it look incomplete
        text = text.rstrip('.,!?')
        segment['text'] = text
    
    return selected_segments

def create_gif_with_captions(video_path, segments, duration=3):
    """Step 3 & 4: Clip video segments and overlay captions."""
    print(f"\n=== Step 3 & 4: Creating GIFs with Captions ===")
    
    if not segments:
        print("No segments provided")
        return []
        
    try:
        # Check required tools
        if not check_ffmpeg():
            raise ValueError("FFmpeg is not installed")
        if not check_imagemagick():
            raise ValueError("ImageMagick is not installed")
            
        gif_paths = []
        print("Loading video file...")
        video = VideoFileClip(video_path)
        
        for i, segment in enumerate(segments, 1):
            print(f"\nProcessing segment {i} of {len(segments)}...")
            
            # Get segment timing
            start_time = segment['start']
            end_time = min(start_time + duration, segment['end'])
            
            print(f"Extracting segment from {start_time:.2f}s to {end_time:.2f}s...")
            # Extract video segment
            video_segment = video.subclip(start_time, end_time)
            
            print("Creating caption...")
            # Get the full caption text
            text = segment['text']
            
            # Calculate font size based on text length
            base_font_size = 30
            if len(text) > 50:
                font_size = base_font_size - 5
            elif len(text) > 30:
                font_size = base_font_size - 3
            else:
                font_size = base_font_size
            
            # Create text clip with the caption
            txt_clip = TextClip(text, 
                              fontsize=font_size,
                              color='white',
                              stroke_color='black',
                              stroke_width=2,
                              method='caption',
                              size=(video_segment.w * 0.7, None),  # Reduce width to 70% of video
                              font='Arial-Bold',
                              align='center',
                              interline=-1)
            
            # Position text at bottom with padding
            txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(end_time - start_time)
            
            # Add a semi-transparent background
            bg_clip = ColorClip(size=(txt_clip.w + 40, txt_clip.h + 20),  # Add padding around text
                              color=(0, 0, 0))
            bg_clip = bg_clip.set_opacity(0.6).set_position(('center', 'bottom')).set_duration(end_time - start_time)
            
            print("Combining video and caption...")
            final_clip = CompositeVideoClip([video_segment, bg_clip, txt_clip])
            
            # Generate unique filename
            output_filename = f"{uuid.uuid4()}.gif"
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            
            print("Creating temporary video file...")
            temp_video = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{uuid.uuid4()}.mp4")
            
            try:
                final_clip.write_videofile(temp_video, codec='libx264', audio=False)
                print("Converting to GIF...")
                
                # Convert to GIF using FFmpeg
                ffmpeg_cmd = [
                    FFMPEG_PATH, '-y',
                    '-i', temp_video,
                    '-vf', 'fps=15,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse',
                    '-loop', '0',
                    output_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
                
                if os.path.exists(output_path):
                    print(f"GIF created successfully at: {output_path}")
                    gif_paths.append(output_path)
                
                # Clean up temporary file
                if os.path.exists(temp_video):
                    os.remove(temp_video)
                
            except Exception as e:
                print(f"Error creating GIF: {str(e)}")
                continue
            
            # Clean up clips
            final_clip.close()
            txt_clip.close()
            bg_clip.close()
        
        video.close()
        print("\nAll GIFs created successfully!")
        return gif_paths
        
    except Exception as e:
        print(f"Error creating GIFs: {str(e)}")
        return []

@app.route('/')
def index():
    return render_template('index.html', 
                         ffmpeg_installed=check_ffmpeg(),
                         imagemagick_installed=check_imagemagick())

@app.route('/process', methods=['POST'])
def process_video():
    try:
        print("\n=== Starting video processing ===")
        
        # Check required tools
        if not check_ffmpeg():
            return jsonify({'error': 'FFmpeg is not installed'}), 400
        if not check_imagemagick():
            return jsonify({'error': 'ImageMagick is not installed'}), 400
            
        # Get input parameters
        theme_prompt = request.form.get('theme_prompt')
        youtube_url = request.form.get('youtube_url')
        
        if not theme_prompt:
            return jsonify({'error': 'Theme prompt is required'}), 400
            
        # Download or get video file
        video_path = None
        original_url = None
        
        if youtube_url:
            try:
                video_path, original_url = download_youtube_video(youtube_url)
            except Exception as e:
                return jsonify({'error': str(e)}), 400
        elif 'video' in request.files:
            video_file = request.files['video']
            if video_file.filename == '':
                return jsonify({'error': 'No video file selected'}), 400
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)
        else:
            return jsonify({'error': 'No video source provided'}), 400
            
        if not os.path.exists(video_path):
            return jsonify({'error': 'Video file not found'}), 400
            
        # Step 1: Generate transcript
        transcript, duration = transcribe_video(video_path, original_url)
        if not transcript:
            return jsonify({'error': 'Failed to generate transcript'}), 400
            
        # Step 2: Find relevant segments
        segments = find_relevant_segments(transcript, theme_prompt)
        if not segments:
            return jsonify({'error': 'Failed to find relevant segments'}), 400
            
        # Step 3 & 4: Create GIFs with captions
        gif_paths = create_gif_with_captions(video_path, segments)
        if not gif_paths:
            return jsonify({'error': 'Failed to create GIFs'}), 400
            
        # Clean up
        if os.path.exists(video_path):
            os.remove(video_path)
            
        return jsonify({
            'success': True,
            'gif_paths': [os.path.basename(path) for path in gif_paths],
            'duration': duration
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/gif/<filename>')
def get_gif(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename))

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 10000))
    # Only run in debug mode if not in production
    debug = os.getenv('FLASK_ENV') != 'production'
    # Bind to all interfaces
    app.run(host='0.0.0.0', port=port, debug=debug) 