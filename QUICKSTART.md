# SpeakSense - Quick Start Guide

Get SpeakSense up and running in 5 minutes!

## Prerequisites

1. **Python 3.8+**
   ```bash
   python --version
   ```

2. **FFmpeg** (for audio processing)
   ```bash
   # macOS
   brew install ffmpeg

   # Ubuntu/Debian
   sudo apt install ffmpeg
   ```

## Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   This will install all required packages. First run will download models (~4GB total):
   - Whisper ASR model
   - BGE embedding model
   - PaddleSpeech TTS model

## Quick Start

### Option 1: Automatic (Recommended)

**Start all services:**
```bash
./run_all_services.sh
```

**Run example workflow:**
```bash
python examples/example_workflow.py
```

This will:
- Upload 10 sample FAQs (Chinese + English)
- Generate TTS audio for each FAQ
- Build search indices
- Test retrieval with sample queries

**Stop all services:**
```bash
./stop_all_services.sh
```

### Option 2: Manual

**Terminal 1 - ASR Service:**
```bash
cd services/asr_service
python main.py
```

**Terminal 2 - Retrieval Service:**
```bash
cd services/retrieval_service
python main.py
```

**Terminal 3 - Admin Service:**
```bash
cd services/admin_service
python main.py
```

## Using the System

### 1. Add a FAQ

```bash
curl -X POST "http://localhost:8003/admin/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What time does the library open?",
    "answer": "The library opens at 9 AM on weekdays.",
    "alternative_questions": ["When does the library open?", "Opening hours?"],
    "language": "en",
    "category": "hours"
  }'
```

### 2. Rebuild Search Indices

After adding FAQs:
```bash
curl -X POST "http://localhost:8002/retrieval/rebuild_indices"
```

### 3. Query the System

**Convert audio to text (ASR):**
```bash
curl -X POST "http://localhost:8001/asr/transcribe" \
  -F "file=@question.mp3" \
  -F "language=auto"
```

**Get matching answer:**
```bash
curl -X POST "http://localhost:8002/retrieval/best_answer" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What time does the library open?",
    "language": "en"
  }'
```

**Response includes:**
- Answer text
- Audio file path (for playback)
- Confidence score

## API Documentation

Interactive API docs (Swagger UI):
- ASR Service: http://localhost:8001/docs
- Retrieval Service: http://localhost:8002/docs
- Admin Service: http://localhost:8003/docs

## Testing

View the example workflow:
```bash
python examples/example_workflow.py
```

Check service logs:
```bash
tail -f logs/asr_service.log
tail -f logs/retrieval_service.log
tail -f logs/admin_service.log
```

## Common Commands

**List all FAQs:**
```bash
curl http://localhost:8003/admin/faqs
```

**Get system stats:**
```bash
curl http://localhost:8003/admin/stats
curl http://localhost:8002/retrieval/stats
```

**Check service health:**
```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

## Configuration

Edit `config/config.yaml` to customize:
- ASR model (tiny/base/small/medium/large)
- Embedding model
- TTS model
- Retrieval weights (BM25 vs vector)
- Service ports

## Troubleshooting

**Services won't start:**
- Check if ports 8001, 8002, 8003 are available
- Check logs in `logs/` directory

**TTS generation fails:**
- PaddleSpeech can be slow on first run (downloading models)
- Alternative: Use edge-tts (requires internet) in config

**No search results:**
- Make sure you rebuilt indices after adding FAQs
- Check if FAQs were added successfully: `curl http://localhost:8003/admin/faqs`

**Models downloading slowly:**
- Models are cached after first download
- Check internet connection

## Next Steps

1. Add your own FAQ data
2. Test with real audio files
3. Integrate with your robot/client application
4. Deploy to production server

See [README.md](README.md) for detailed documentation.
