# SpeakSense

An on-premise voice interaction system for FAQ retrieval, designed for environments like libraries. The system converts speech to text, matches questions using hybrid retrieval (BM25 + vector search), and responds with pre-generated audio answers.

## Features

- **On-Premise Deployment**: All processing happens locally, no cloud dependencies
- **No LLMs**: Uses classical IR methods and small embedding models only
- **Multilingual Support**: Chinese and English
- **Hybrid Retrieval**: Combines BM25 keyword search with BGE semantic embeddings
- **Pre-generated Audio**: TTS generation during FAQ upload, instant playback during queries
- **Modular Architecture**: Three independent services that can scale separately
- **Model Switching**: Easy configuration to swap ASR, embedding, or TTS models

## Architecture

```
┌──────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ ASR Service  │   │Retrieval Service│   │  Admin Service  │
│   (8001)     │   │    (8002)       │   │    (8003)       │
│              │   │                 │   │                 │
│  - Whisper   │   │ - BM25 search   │   │ - Upload FAQ    │
│              │   │ - BGE embedding │   │ - TTS generate  │
│              │   │ - ChromaDB      │   │ - CRUD ops      │
└──────────────┘   └─────────────────┘   └─────────────────┘
                            │                      │
                            └──────┬───────────────┘
                                   │
                            ┌──────▼──────┐
                            │  ChromaDB   │
                            │  + SQLite   │
                            └─────────────┘
```

### Services

1. **ASR Service (Port 8001)**: Converts audio (MP3) to text using Whisper
2. **Retrieval Service (Port 8002)**: Finds matching FAQs using hybrid search
3. **Admin Service (Port 8003)**: Manages FAQ entries with TTS generation

## Installation

### Prerequisites

- Python 3.8+
- FFmpeg (for audio processing)

### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Install Python Dependencies

```bash
# Clone or navigate to the project directory
cd SpeakSense

# Install dependencies
pip install -r requirements.txt
```

**Note**: The first time you run the services, models will be downloaded automatically:
- Whisper model (~1.5GB for medium)
- BGE-m3 embedding model (~2GB)
- PaddleSpeech TTS models (~500MB)

### GPU Support (Optional)

For faster inference, install GPU versions:

```bash
# For CUDA 11.8
pip install torch==2.1.0+cu118 -f https://download.pytorch.org/whl/torch_stable.html
pip install paddlepaddle-gpu==2.5.2
```

Then update `config/config.yaml` to use `device: "cuda"`.

## Configuration

Edit `config/config.yaml` to customize settings:

```yaml
# ASR model selection
asr:
  model_name: "medium"  # Options: tiny, base, small, medium, large
  device: "cpu"         # cpu or cuda

# Embedding model
embedding:
  model_name: "BAAI/bge-m3"  # Supports Chinese + English

# TTS model
tts:
  model_type: "paddlespeech"  # or "edge-tts"

# Retrieval weights
retrieval:
  bm25_weight: 0.3
  vector_weight: 0.7
```

## Usage

### 1. Start All Services

Open three terminal windows:

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

### 2. Add FAQ Entries

Use the Admin Service API to add FAQs:

```bash
# Add a single FAQ
curl -X POST "http://localhost:8003/admin/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What time does the library close today?",
    "answer": "The library closes at 9 PM today.",
    "alternative_questions": [
      "When does the library shut down?",
      "Library closing time?"
    ],
    "language": "en",
    "category": "hours"
  }'
```

The Admin Service will:
1. Store the FAQ in SQLite
2. Generate audio using TTS (PaddleSpeech)
3. Save audio to `data/audio_files/`

### 3. Rebuild Search Indices

After adding FAQs, rebuild the search indices:

```bash
curl -X POST "http://localhost:8002/retrieval/rebuild_indices"
```

### 4. Query the System

**Step 1: Convert speech to text (ASR)**

```bash
curl -X POST "http://localhost:8001/asr/transcribe" \
  -F "file=@user_question.mp3" \
  -F "language=auto"
```

Response:
```json
{
  "text": "What time does the library close today?",
  "language": "en"
}
```

**Step 2: Get matching answer (Retrieval)**

```bash
curl -X POST "http://localhost:8002/retrieval/best_answer" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What time does the library close today?",
    "language": "en"
  }'
```

Response:
```json
{
  "answer_id": "abc-123",
  "question": "What time does the library close today?",
  "answer": "The library closes at 9 PM today.",
  "audio_path": "audio_files/abc-123.wav",
  "confidence": 0.95,
  "matched_by": "hybrid"
}
```

**Step 3: Play the audio**

The robot client can now play the audio file at `data/audio_files/abc-123.wav`.

## API Documentation

Once services are running, access interactive API docs:

- ASR Service: http://localhost:8001/docs
- Retrieval Service: http://localhost:8002/docs
- Admin Service: http://localhost:8003/docs

## Example: Complete Workflow

See `tests/example_workflow.py` for a complete example including:
- Adding multiple FAQs (Chinese and English)
- Uploading audio files
- Querying the system
- Full pipeline from speech to audio playback

```bash
python tests/example_workflow.py
```

## Testing

Run the test suite:

```bash
pytest tests/
```

## Model Switching

### Change ASR Model

Edit `config/config.yaml`:
```yaml
asr:
  model_name: "large"  # Switch to Whisper large model
```

Or use API:
```bash
curl -X POST "http://localhost:8001/asr/switch_model" \
  -H "Content-Type: application/json" \
  -d '{"model_name": "large"}'
```

### Change Embedding Model

Edit `config/config.yaml`:
```yaml
embedding:
  model_name: "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
```

Then rebuild indices:
```bash
curl -X POST "http://localhost:8002/retrieval/rebuild_indices"
```

### Change TTS Model

Edit `config/config.yaml`:
```yaml
tts:
  model_type: "edge-tts"  # Switch to Edge TTS
```

Note: Edge TTS requires internet connection.

## Deployment

### Production Deployment

For production, consider:

1. **Use systemd services** (Linux):
   - Create service files for each service
   - Enable auto-restart on failure

2. **Use Docker** (recommended):
   ```bash
   # TODO: Add Dockerfile
   docker-compose up -d
   ```

3. **Use a process manager**:
   ```bash
   # Using PM2
   pm2 start services/asr_service/main.py --name asr
   pm2 start services/retrieval_service/main.py --name retrieval
   pm2 start services/admin_service/main.py --name admin
   ```

4. **Add reverse proxy** (nginx/traefik) for load balancing

5. **Enable HTTPS** for secure communication

### Scaling

- **High user load**: Scale Retrieval Service horizontally (multiple instances)
- **Heavy ASR load**: Use GPU, or deploy multiple ASR service instances
- **Large FAQ database**: Switch ChromaDB to Milvus (configured in `config.yaml`)

## Troubleshooting

### Common Issues

**1. "No module named 'whisper'"**
- Solution: `pip install openai-whisper`

**2. "ffmpeg not found"**
- Solution: Install FFmpeg (see Installation section)

**3. "PaddleSpeech TTS failed"**
- Solution: PaddleSpeech can be temperamental. Alternative:
  - Switch to Edge TTS: `tts.model_type: "edge-tts"` in config
  - Or upload pre-recorded audio files via `/admin/faq_with_audio`

**4. "ChromaDB collection not found"**
- Solution: Run rebuild indices: `POST /retrieval/rebuild_indices`

**5. Models downloading slowly**
- Solution: Models are cached after first download. For Whisper, you can manually download models and place them in `~/.cache/whisper/`

### Performance Optimization

- Use Whisper `small` or `base` model for faster ASR (trade-off: less accurate)
- Reduce `top_k_bm25` and `top_k_vector` in config for faster retrieval
- Use GPU if available (`device: "cuda"` in config)
- For large FAQ datasets (>10,000), consider switching to Milvus

## Project Structure

```
SpeakSense/
├── config/
│   ├── config.yaml          # Main configuration
│   └── synonyms.json        # Synonym dictionary
├── services/
│   ├── asr_service/         # ASR Service
│   ├── retrieval_service/   # Retrieval Service
│   └── admin_service/       # Admin Service
├── shared/
│   ├── config_loader.py     # Config utilities
│   ├── database.py          # SQLite operations
│   └── models.py            # Pydantic models
├── data/
│   ├── faq.db              # SQLite database
│   ├── audio_files/        # Generated/uploaded audio
│   └── chromadb/           # Vector database
├── tests/                   # Test scripts
├── requirements.txt
└── README.md
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines]

## Support

For issues or questions, please [create an issue](https://github.com/yourrepo/speaksense/issues).
