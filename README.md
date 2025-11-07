# Two-Host AI Newscast Generator

Generate engaging AI-powered podcast newscasts with two dynamic hosts debating and discussing today's top news stories.

## Features

- Two-Host Dynamic: Ben (tech-optimist) vs Jerry (skeptical journalist)
- Real-Time News: Fetches latest news from NewsAPI
- AI Script Generation: OpenAI GPT-4 generates natural dialogue
- Audio Rendering: Cartesia TTS converts scripts to audio
- Multiple Formats: JSON, TXT, MP3, JSONL, VTT, and Markdown outputs
- Easy Setup: Automatic ffmpeg installation for MP3 support

## Quick Start

### Prerequisites

- Python 3.8+
- API Keys:
  - [NewsAPI](https://newsapi.org/) - For fetching news
  - [OpenAI](https://platform.openai.com/) - For script generation
  - [Cartesia](https://cartesia.ai/) - For text-to-speech

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd two-host-ai-newscast
```

2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Setup ffmpeg for MP3 export** (one command!)

```bash
python setup_ffmpeg.py
```

This automatically downloads and configures ffmpeg (~100 MB, no admin rights needed).

4. **Configure API keys**

Create a `.env` file in the project root:

```env
NEWSAPI_KEY=your_newsapi_key_here
OPENAI_API_KEY=your_openai_key_here
CARTESIA_API_KEY=your_cartesia_key_here
```

### Generate Your First Newscast

```bash
python main.py --personas config/personas.json --minutes 5 --topics tech
```

This creates in the `out/` directory:
- `episode.mp3` - Audio podcast
- `episode_transcript.jsonl` - Timestamped transcript
- `episode.vtt` - WebVTT subtitles
- `episode_show_notes.md` - Markdown show notes with source links
- `script.json` / `script.txt` - Full script
- `stories.json` - Source articles

## Usage Examples

### Basic Newscast

```bash
python main.py --personas config/personas.json --minutes 5 --topics tech
```

### Multiple Topics

```bash
python main.py --personas config/personas.json --minutes 10 --topics tech,science,world
```

### Different Region

```bash
python main.py --personas config/personas.json --region gb --topics tech
```

### Custom Output Directory

```bash
python main.py --personas config/personas.json --output-dir out/episode_001
```

### With Background Music

```bash
python main.py --personas config/personas.json \
  --intro-music assets/intro.mp3 \
  --outro-music assets/outro.mp3
```

### Script Only (No Audio)

```bash
python main.py --personas config/personas.json --skip-audio
```

## Configuration

### Command-Line Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--personas` | path | **required** | Path to personas.json |
| `--minutes` | int | 5 | Target duration in minutes |
| `--topics` | string | general | Comma-separated topics |
| `--region` | string | us | Region code (us, gb, ca, etc.) |
| `--profanity-filter` | flag | False | Enable profanity filtering |
| `--output-dir` | path | out | Output directory |
| `--audio-format` | mp3\|wav | mp3 | Audio format |
| `--pause-duration` | int | 1000 | Pause between lines (ms) |
| `--intro-music` | path | None | Intro background music |
| `--outro-music` | path | None | Outro background music |
| `--skip-audio` | flag | False | Skip audio rendering |

### Customizing Voices

Edit `config/personas.json` to change Cartesia voices:

```json
{
  "hosts": [
    {
      "name": "Ben",
      "voice_id": "a0e99841-438c-4a64-b679-ae501e7d6091",
      "personality": "Tech-optimist futurist...",
      "style": "Energetic, interrupts with excitement..."
    },
    {
      "name": "Jerry",
      "voice_id": "694f9389-aac1-45b6-b726-9d9369183238",
      "personality": "Skeptical journalist...",
      "style": "Deliberate, pauses for effect..."
    }
  ]
}
```

**Find voices**: Browse the [Cartesia Voice Library](https://play.cartesia.ai/voices)

## Output Structure

After running the generator:

```
out/
├── episode.mp3                    # Final audio podcast
├── episode_transcript.jsonl       # Timestamped transcript (one JSON per line)
├── episode.vtt                    # WebVTT subtitles with timestamps
├── episode_show_notes.md          # Show notes with source links
├── script.json                    # Structured script data
├── script.txt                     # Human-readable script
└── stories.json                   # Fetched news stories
```

### Output Formats

**1. Audio (MP3/WAV)**
- High-quality audio with natural-sounding voices
- Configurable pauses between dialogue
- Optional intro/outro music

**2. Transcript (JSONL)**
```json
{"t": 0.0, "speaker": "Ben", "text": "Hey everyone, welcome back!", "src": [0]}
{"t": 5.2, "speaker": "Jerry", "text": "Trust me, it's a game-changer.", "src": []}
```

**3. Subtitles (VTT)**
```
WEBVTT

1
00:00:00.000 --> 00:00:05.200
<v Ben>Hey everyone, welcome back! You won't believe what DJI just dropped [src: 0].

2
00:00:06.200 --> 00:00:09.400
<v Jerry>Trust me, it's a game-changer for smartphone filmmakers.
```

**4. Show Notes (Markdown)**
- Episode description
- Topics covered with summaries
- Clickable source links
- Host information

## Testing

```bash
# Test audio rendering (MP3 & WAV)
python tests/test_audio_rendering.py

# Test output formats (JSONL, VTT, Markdown)
python tests/test_output_formats.py

# Full integration test
python tests/test_newscast.py
```

## Architecture

### Pipeline

```
1. News Fetching (NewsAPI)
   ↓
2. Script Generation (OpenAI GPT-4)
   ↓
3. Audio Rendering (Cartesia TTS)
   ↓
4. Output Generation (JSONL, VTT, Markdown)
```

### Modules

- **`src/news.py`** - Fetches and validates news from NewsAPI
- **`src/script_generator.py`** - Generates dialogue using OpenAI
- **`src/audio_renderer.py`** - Converts script to audio using Cartesia
- **`src/output_writer.py`** - Generates JSONL, VTT, and Markdown outputs
- **`src/main.py`** - Orchestrates the complete pipeline
- **`config/personas.json`** - Host personality and voice configuration
- **`setup_ffmpeg.py`** - Automatic ffmpeg setup for MP3 support

## Cost Estimation

Approximate cost per 5-minute newscast:

- **NewsAPI**: Free (up to 100 requests/day)
- **OpenAI GPT-4**: ~$0.10 - $0.30
- **Cartesia TTS**: ~$0.08 - $0.15

**Total**: ~$0.18 - $0.45 per episode

### Cost Optimization

1. Use `--skip-audio` during script development
2. Cache news stories for multiple script iterations
3. Use shorter durations (`--minutes 3`) for testing
4. Batch generate multiple episodes

## Background Music (Optional)

Add intro/outro music with proper licensing:

### Recommended Sources

- **[FreePD](https://freepd.com/)** - Public Domain (CC0)
- **[Incompetech](https://incompetech.com/)** - Creative Commons BY 3.0
- **[YouTube Audio Library](https://youtube.com/audiolibrary)** - Various licenses
- **[Bensound](https://bensound.com/)** - Creative Commons BY-ND
- **[Purple Planet](https://purple-planet.com/)** - Creative Commons BY 4.0

Always check licenses and provide proper attribution!

## Troubleshooting

### MP3 Export Not Working

```bash
# Run automatic setup
python setup_ffmpeg.py

# Or use WAV format
python main.py --personas config/personas.json --audio-format wav
```

### Missing API Keys

```
Error: Missing required API keys in .env file
```

**Solution**: Create `.env` file with all three API keys (see Installation section)

### Module Not Found

```bash
pip install -r requirements.txt
```

### Python 3.13 Audio Issues

The `audioop-lts` package is automatically installed for Python 3.13 compatibility.

## Acceptance Checklist

- Runs with `.env` keys for NEWSAPI_KEY, OPENAI_API_KEY, CARTESIA_API_KEY
- Produces MP3, transcript (JSONL + VTT), and show notes with source links
- Dialogue shows clear, consistent personalities and cites sources via `[src: i]`
- No obvious hallucinations; facts match links (requires manual verification)

## Credits

Powered by NewsAPI, OpenAI GPT-4, and Cartesia TTS.

