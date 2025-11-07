# Two-Host AI Newscast Generator

Generate engaging AI-powered podcast newscasts with two dynamic hosts debating and discussing today's top news stories.

## Features

- Two-Host Dynamic: Ben (tech-optimist) vs Jerry (skeptical journalist)
- Real-Time News: Fetches latest news from NewsAPI
- AI Script Generation: OpenAI GPT-4 generates natural dialogue
- Audio Rendering: Cartesia TTS converts scripts to audio
- Multiple Formats: JSON, TXT, MP3, JSONL, VTT, and Markdown outputs

## Quick Start

### Prerequisites

- Python 3.8+
- API Keys:
  - [NewsAPI](https://newsapi.org/)
  - [OpenAI](https://platform.openai.com/)
  - [Cartesia](https://cartesia.ai/)

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd two-host-ai-newscast
```

2. **Create and activate a virtual environment (recommended)**

```bash
python -m venv venv

# Activate on Windows:
venv\Scripts\activate

# Activate on Linux/Mac:
source venv/bin/activate
```

3. **Install dependencies and setup ffmpeg**

```bash
pip install -r requirements.txt
python setup_ffmpeg.py
```

4. **Configure API keys**

Copy `env.example` to `.env` and add your API keys:

```bash
cp env.example .env
```

Then edit `.env` with your keys:
```env
NEWSAPI_KEY=your_newsapi_key_here
OPENAI_API_KEY=your_openai_key_here
CARTESIA_API_KEY=your_cartesia_key_here
```

### Generate Your First Newscast

**Make sure your virtual environment is activated**, then:

```bash
python main.py --personas config/personas.json --minutes 5 --topics tech
```

This creates in the `out/` directory:
- `episode.mp3` - Audio podcast
- `episode_transcript.jsonl` - Timestamped transcript  
- `episode.vtt` - WebVTT subtitles
- `episode_show_notes.md` - Show notes with source links and summaries
- `script.json` / `script.txt` - Full script
- `stories.json` - Fetched news stories with summaries

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
python main.py --personas config/personas.json --intro-music assets/intro.mp3 --outro-music assets/outro.mp3
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

Edit `config/personas.json` to change host personalities and voices:

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

Find more voices at [Cartesia Voice Library](https://play.cartesia.ai/voices)

## Output Structure

```
out/
├── episode.mp3                    # Final audio podcast
├── episode_transcript.jsonl       # Timestamped transcript
├── episode.vtt                    # WebVTT subtitles
├── episode_show_notes.md          # Show notes with source links
├── script.json                    # Structured script data
├── script.txt                     # Human-readable script
└── stories.json                   # Fetched news stories
```

## Testing

```bash
# Test audio rendering
python tests/test_audio_rendering.py

# Test output formats
python tests/test_output_formats.py

# Full integration test
python tests/test_newscast.py
```

## Project Structure

```
two-host-ai-newscast/
├── main.py                        # Entry point
├── src/
│   ├── news.py                    # News fetching and validation
│   ├── script_generator.py        # AI script generation
│   ├── audio_renderer.py          # Text-to-speech rendering
│   ├── output_writer.py           # Generate outputs (JSONL, VTT, MD)
│   └── main.py                    # Main orchestration
├── config/
│   ├── personas.json              # Host personalities and voices
│   └── config.json                # Default configuration
├── tests/                         # Test files
├── requirements.txt               # Python dependencies
└── setup_ffmpeg.py               # Automatic ffmpeg setup

```

## License & Credits

This project uses:
- [NewsAPI](https://newsapi.org/) for news fetching
- [OpenAI GPT-4](https://openai.com/) for script generation
- [Cartesia](https://cartesia.ai/) for text-to-speech

**Disclaimer**: This tool generates AI content for informational and entertainment purposes. The voices are synthetic and do not represent real individuals. Always verify facts from original sources.
