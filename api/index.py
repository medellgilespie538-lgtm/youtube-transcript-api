from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re

app = Flask(__name__)

def extract_video_id(url_or_id):
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'^([0-9A-Za-z_-]{11})$'
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return url_or_id

@app.route('/')
def home():
    return jsonify({
        'service': 'YouTube Transcript API',
        'status': 'running',
        'usage': '/api/transcript?video_id=VIDEO_ID'
    })

@app.route('/api/transcript', methods=['GET', 'POST'])
def get_transcript():
    if request.method == 'POST':
        data = request.get_json()
        video_id = data.get('video_id') or data.get('url')
        languages = data.get('languages', ['zh-Hans', 'zh-Hant', 'zh', 'en'])
    else:
        video_id = request.args.get('video_id') or request.args.get('url')
        lang_str = request.args.get('lang', 'zh-Hans,zh-Hant,zh,en')
        languages = [l.strip() for l in lang_str.split(',')]
    
    if not video_id:
        return jsonify({'error': '缺少 video_id 参数'}), 400
    
    video_id = extract_video_id(video_id)
    
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=languages)
        text_only = ' '.join([entry['text'] for entry in transcript])
        formatted = '\n'.join([f"[{format_time(entry['start'])}] {entry['text']}" for entry in transcript])
        
        return jsonify({
            'success': True,
            'video_id': video_id,
            'transcript': transcript,
            'text': text_only,
            'formatted': formatted,
            'total_chars': len(text_only),
            'total_lines': len(transcript)
        })
        
    except TranscriptsDisabled:
        return jsonify({'error': '此视频已禁用字幕'}), 404
    except NoTranscriptFound:
        return jsonify({'error': '未找到字幕'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
