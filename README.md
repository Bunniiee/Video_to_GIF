# Video to GIF Converter

A web application that converts videos to GIFs with custom captions. You can either upload a video file or provide a YouTube URL, along with a theme prompt to generate a captioned GIF.

## Features

- Upload video files or use YouTube URLs
- Add custom theme prompts/captions to GIFs
- Modern, responsive UI built with React and Material-UI
- Automatic video processing and GIF generation
- Download generated GIFs
- Real-time progress feedback

## Requirements

### Backend
- Python 3.7+
- Flask
- MoviePy
- Pillow
- yt-dlp
- FFmpeg
- ImageMagick
- Other Python dependencies listed in requirements.txt

### Frontend
- Node.js 14+
- npm or yarn
- React 18+
- Material-UI
- Axios

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd video-to-gif
```

2. Set up the Python backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

3. Set up the React frontend:
```bash
cd frontend
npm install
```

4. Install required system dependencies:
   - FFmpeg: Download from [official FFmpeg builds](https://github.com/BtbN/FFmpeg-Builds/releases)
   - ImageMagick: Download from [ImageMagick website](https://imagemagick.org/script/download.php)

## Usage

1. Start the Flask backend:
```bash
# From the project root
python app.py
```

2. Start the React frontend:
```bash
# From the frontend directory
npm run dev
```

3. Open your web browser and navigate to `http://localhost:5173`

4. Use the web interface to:
   - Enter a theme prompt/caption
   - Either upload a video file or provide a YouTube URL
   - Click "Generate GIF" to process the video
   - Download the generated GIFs

## Development

The application consists of two main parts:

### Backend (Flask)
- Handles video processing
- Manages file uploads
- Generates GIFs
- Provides API endpoints

### Frontend (React)
- Provides user interface
- Handles form submissions
- Displays generated GIFs
- Manages file uploads

## Notes

- The application supports video files up to 500MB
- GIFs are generated with a 3-second duration
- The theme prompt is displayed at the bottom of the GIF
- Generated GIFs are stored in the `uploads` directory
- The frontend runs on port 5173 by default
- The backend runs on port 5000 by default

## License

MIT License

## How to Improve

1. Implement parallel video downloading with consistent speeds and limit initial quality to reduce the 11MB file size, while adding proper progress tracking.

2. Switch to a smaller Whisper model for faster processing of 135 segments, implement transcription caching, and prioritize YouTube captions as the primary source.

3. Process multiple GIFs in parallel instead of sequentially, reduce temporary file creation, and optimize FFmpeg parameters for faster conversion.

4. Switch from development to production WSGI server, implement proper logging levels, and add request rate limiting for better API performance.

5. Implement caching for successful video processing results, add multiple fallback options for each step, and add automatic cleanup of temporary files. 