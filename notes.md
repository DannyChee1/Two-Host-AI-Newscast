# Design Notes: Two-Host AI Newscast

## Design Choices

**Modular Architecture**: The system is split into distinct modules (`news.py`, `script_generator.py`, `audio_renderer.py`, `output_writer.py`) for maintainability and testability. Each module handles a single responsibility, making it easy to swap components or debug issues.

**Two-Phase Script Generation**: The prompt strategy creates a rundown first (structure with duration estimates), then generates dialogue within that structure. This ensures better pacing control and helps hit target durations.

**Local FFmpeg Strategy**: Rather than requiring system-wide installation, the app automatically downloads and configures ffmpeg in the project directory. This eliminates setup friction while meeting the MP3 requirement.

## Prompt Strategy

**Personality Enforcement**: Detailed persona descriptions in `personas.json` are reinforced through explicit system prompts. Each host has distinct vocabulary patterns, energy levels, and perspectives. Examples of catchphrases and reaction styles are provided to guide GPT-4.

**Source Grounding**: Stories are passed with full context (title, URL, summary, source). The prompt explicitly forbids inventing facts and requires `[src: i]` citations for all factual claims. Sources are tracked both inline and in the dialogue structure.

**Conversational Flow**: The prompt emphasizes natural conversation over Q&A. It instructs mixing very short reactions (1-5 words) with longer explanations (80-150 words), building momentum through callbacks and disagreements.

**Duration Control**: Target word count is calculated based on speaking rate (150 WPM) minus pause time. The prompt explicitly requires minimum word counts and dialogue line counts, with validation warnings if targets aren't met.

## Trade-offs

**Duration Accuracy**: Word-count estimation (150 WPM) doesn't account for voice speed variations or emotional emphasis. Perfect accuracy would require pre-rendering all audio, which is impractical. Current approach is within 10-15% accuracy.

**Voice Expressiveness**: Cartesia's experimental controls are limited. The current implementation uses dynamic speed adjustment based on text length, but more sophisticated emotion control would require API updates or post-processing.

**Determinism**: No seed control is exposed by default. Each run generates unique dialogue while maintaining personality consistency. This prioritizes freshness over reproducibility, though a `--seed` flag could be added.

**Error Handling**: NewsAPI failures gracefully fall back to top headlines. Script generation errors are caught with clear messages. Audio rendering failures provide helpful diagnostics. The system prioritizes user-friendly error messages over silent failures.

## What I'd Do Next

**Short-term**: Add iterative script refinement to hit exact duration targets. Implement better voice differentiation through text preprocessing (e.g., adding emphasis markers for energetic host). Add fact-checking validation against source articles.

**Medium-term**: Support multi-episode generation with consistent branding. Add voice selection UI and per-host emotion controls. Implement topic clustering and importance ranking for better story selection.

**Long-term**: Real-time streaming generation to reduce latency. Multi-language support with localized voices. Platform integration for direct podcast platform uploads.

