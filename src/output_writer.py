import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import timedelta


class OutputWriterError(Exception):
    pass


def format_timestamp_vtt(seconds: float) -> str:
    td = timedelta(seconds=seconds)
    hours = int(td.total_seconds() // 3600)
    minutes = int((td.total_seconds() % 3600) // 60)
    secs = td.total_seconds() % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def calculate_line_timestamps(
    script: Dict,
    audio_duration_ms: int,
    pause_duration_ms: int = 1000
) -> List[Dict]:
    if not script or 'dialogue' not in script:
        raise OutputWriterError("Invalid script: missing 'dialogue' field")
    
    dialogue = script['dialogue']
    if not dialogue:
        return []

    WORDS_PER_MINUTE = 150
    WORDS_PER_SECOND = WORDS_PER_MINUTE / 60.0

    timestamped_dialogue = []
    current_time = 0.0
    
    for i, line in enumerate(dialogue):
        text = line.get('text', '').strip()
        if not text:
            continue

        word_count = len(text.split())
        estimated_duration = word_count / WORDS_PER_SECOND

        timestamped_line = {
            **line,
            'start_time': current_time,
            'end_time': current_time + estimated_duration
        }
        timestamped_dialogue.append(timestamped_line)

        current_time += estimated_duration
        if i < len(dialogue) - 1:
            current_time += pause_duration_ms / 1000.0

    return timestamped_dialogue


def write_transcript_jsonl(
    script: Dict,
    stories: List[Dict],
    output_path: str,
    pause_duration_ms: int = 1000,
    audio_duration_ms: Optional[int] = None
) -> str:
    timestamped_dialogue = calculate_line_timestamps(
        script,
        audio_duration_ms or 300000,
        pause_duration_ms
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        for line in timestamped_dialogue:
            jsonl_entry = {
                't': round(line['start_time'], 3),
                'speaker': line.get('speaker', 'Unknown'),
                'text': line.get('text', ''),
                'src': line.get('sources', [])
            }
            f.write(json.dumps(jsonl_entry, ensure_ascii=False) + '\n')

    return output_path


def write_vtt_subtitles(
    script: Dict,
    output_path: str,
    pause_duration_ms: int = 1000,
    audio_duration_ms: Optional[int] = None
) -> str:
    timestamped_dialogue = calculate_line_timestamps(
        script,
        audio_duration_ms or 300000,
        pause_duration_ms
    )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")

        for i, line in enumerate(timestamped_dialogue, 1):
            speaker = line.get('speaker', 'Unknown')
            text = line.get('text', '')
            start_time = format_timestamp_vtt(line['start_time'])
            end_time = format_timestamp_vtt(line['end_time'])

            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"<v {speaker}>{text}\n\n")

    return output_path


def write_show_notes(
    script: Dict,
    stories: List[Dict],
    output_path: str,
    episode_title: Optional[str] = None
) -> str:
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    referenced_sources = set()
    for line in script.get('dialogue', []):
        referenced_sources.update(line.get('sources', []))

    segments = {}
    for line in script.get('dialogue', []):
        segment = line.get('segment', 'unknown')
        if segment not in segments:
            segments[segment] = []
        segments[segment].append(line)

    with open(output_path, 'w', encoding='utf-8') as f:
        if episode_title:
            f.write(f"# {episode_title}\n\n")
        else:
            f.write("# Newscast Episode\n\n")

        f.write("## Episode Description\n\n")
        f.write("Join Ben and Jerry as they discuss today's top stories in technology, ")
        f.write("science, and current events. Ben brings the tech-optimist perspective ")
        f.write("while Jerry provides thoughtful analysis and questions the implications.\n\n")

        f.write("## Topics Covered\n\n")

        story_segments = {}
        for line in script.get('dialogue', []):
            for src_id in line.get('sources', []):
                segment = line.get('segment', 'unknown')
                if src_id not in story_segments:
                    story_segments[src_id] = segment

        for src_id in sorted(story_segments.keys()):
            if src_id < len(stories):
                story = stories[src_id]
                f.write(f"### {story.get('title', 'Untitled')}\n\n")
                f.write(f"**Source**: {story.get('source', 'Unknown')}\n\n")

                summary = story.get('summary', '').strip()
                if summary:
                    if len(summary) > 300:
                        summary = summary[:297] + "..."
                    f.write(f"{summary}\n\n")

                f.write(f"**Read more**: [{story.get('url', '#')}]({story.get('url', '#')})\n\n")

        f.write("## All Sources\n\n")
        for i, story in enumerate(stories):
            if i in referenced_sources:
                f.write(f"{i + 1}. [{story.get('title', 'Untitled')}]({story.get('url', '#')}) - {story.get('source', 'Unknown')}\n")

        f.write("\n")

        f.write("## Hosts\n\n")
        f.write("- **Ben**: Tech-optimist futurist. Enthusiastic, fast-paced, sees opportunities in everything.\n")
        f.write("- **Jerry**: Skeptical journalist. Analytical, measured, questions implications.\n\n")

        f.write("---\n\n")
        f.write("## Disclaimer\n\n")
        f.write("This episode was generated using AI technology for informational and entertainment purposes. ")
        f.write("The AI-generated voices are synthetic and do not represent real individuals. ")
        f.write("This content is transformative and created for educational purposes.\n\n")
        f.write("**Important Notes:**\n")
        f.write("- All facts are sourced from cited news articles above\n")
        f.write("- This is not professional advice (financial, medical, or legal)\n")
        f.write("- Host personalities are fictional characters\n")
        f.write("- Sources are provided for fact-checking and attribution\n\n")
        f.write("*Generated with NewsAPI, OpenAI GPT-4, and Cartesia TTS*\n")

    return output_path


def write_all_outputs(
    script: Dict,
    stories: List[Dict],
    output_dir: str = "out",
    episode_name: str = "episode",
    pause_duration_ms: int = 1000,
    audio_duration_ms: Optional[int] = None
) -> Dict[str, str]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {}

    transcript_path = output_dir / "transcript.jsonl"
    outputs['transcript_jsonl'] = write_transcript_jsonl(
        script,
        stories,
        str(transcript_path),
        pause_duration_ms,
        audio_duration_ms
    )

    vtt_path = output_dir / f"{episode_name}.vtt"
    outputs['vtt'] = write_vtt_subtitles(
        script,
        str(vtt_path),
        pause_duration_ms,
        audio_duration_ms
    )

    show_notes_path = output_dir / "show_notes.md"
    outputs['show_notes'] = write_show_notes(
        script,
        stories,
        str(show_notes_path)
    )

    return outputs

