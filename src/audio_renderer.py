import os
import io
import time
import shutil
import re
from pathlib import Path
from typing import List, Dict, Optional
from pydub import AudioSegment
from pydub.effects import normalize
from cartesia import Cartesia


def setup_local_ffmpeg():
    project_root = Path(__file__).parent.parent
    local_ffmpeg = project_root / "ffmpeg" / "bin" / "ffmpeg.exe"
    
    if local_ffmpeg.exists():
        AudioSegment.converter = str(local_ffmpeg)
        AudioSegment.ffmpeg = str(local_ffmpeg)
        AudioSegment.ffprobe = str(project_root / "ffmpeg" / "bin" / "ffprobe.exe")
        return True

    return shutil.which('ffmpeg') is not None


_ffmpeg_available = setup_local_ffmpeg()


class AudioRenderError(Exception):
    pass


def map_hosts_to_voices(personas: Dict) -> Dict[str, str]:

    voice_map = {}
    
    for host in personas.get('hosts', []):
        name = host.get('name')
        voice_id = host.get('voice_id', '').strip()
        
        if not name:
            raise AudioRenderError("Host missing 'name' field in personas")
        
        if not voice_id:
            raise AudioRenderError(f"Host '{name}' missing 'voice_id' in personas. Please add a Cartesia voice ID.")
        
        voice_map[name] = voice_id
    
    return voice_map


def generate_speech(
    text: str,
    voice_id: str,
    client: Cartesia,
    model: str = "sonic-english",
    output_format: Dict = None
) -> bytes:
    if output_format is None:
        output_format = {
            "container": "wav",
            "encoding": "pcm_s16le",
            "sample_rate": 44100
        }


    try:
        response = client.tts.bytes(
            model_id=model,
            transcript=text,
            voice={
                "mode": "id", 
                "id": voice_id,
                "__experimental_controls": {
                    "speed": "normal",
                    "emotion": ["positivity:high", "curiosity:high"]
                }
            },
            output_format=output_format
        )

        audio_data = b"".join(response)
        return audio_data
        
    except Exception as e:
        raise AudioRenderError(f"Failed to generate speech: {str(e)}")


def create_pause(duration_ms: int = 1000) -> AudioSegment:
    return AudioSegment.silent(duration=duration_ms)


def load_background_music(file_path: str, duration_ms: int) -> Optional[AudioSegment]:
    if not os.path.exists(file_path):
        return None
    
    try:
        music = AudioSegment.from_file(file_path)
        
        if len(music) > duration_ms:
            music = music[:duration_ms]
        elif len(music) < duration_ms:
            repeats = (duration_ms // len(music)) + 1
            music = music * repeats
            music = music[:duration_ms]

        music = music - 20

        return music
        
    except Exception as e:
        print(f"Warning: Could not load background music from {file_path}: {e}")
        return None


def render_audio(
    script: Dict,
    personas: Dict,
    cartesia_api_key: str,
    output_path: str = "output/newscast.mp3",
    pause_duration_ms: int = 1000,
    intro_music_path: Optional[str] = None,
    outro_music_path: Optional[str] = None,
    audio_format: str = "mp3"
) -> str:
    print("\n" + "="*50)
    print("AUDIO RENDERING")
    print("="*50 + "\n")
    
    if not script or 'dialogue' not in script:
        raise AudioRenderError("Invalid script: missing 'dialogue' field")
    
    if not script['dialogue']:
        raise AudioRenderError("Script contains no dialogue to render")
    
    client = Cartesia(api_key=cartesia_api_key)
    
    print("Mapping hosts to Cartesia voices...")
    voice_map = map_hosts_to_voices(personas)
    print(f"   Voice mappings: {voice_map}")
    
    output_format = {
        "container": "wav",
        "encoding": "pcm_s16le",
        "sample_rate": 44100
    }
    
    audio_segments = []
    
    for i, line in enumerate(script['dialogue'], 1):
        speaker = line.get('speaker')
        text = line.get('text', '').strip()
        
        if not text:
            print(f"   Line {i}: Skipping empty text")
            continue
        
        if speaker not in voice_map:
            raise AudioRenderError(f"Speaker '{speaker}' not found in voice mappings")
        
        voice_id = voice_map[speaker]
        
        # Remove source citations [src: N] from spoken text
        text_for_speech = re.sub(r'\[src:\s*\d+\]', '', text).strip()
        
        print(f"   Line {i}/{len(script['dialogue'])}: {speaker} - \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        
        try:
            audio_bytes = generate_speech(
                text=text_for_speech,
                voice_id=voice_id,
                client=client,
                output_format=output_format
            )

            audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
            audio_segments.append(audio)

            if i < len(script['dialogue']):
                pause = create_pause(pause_duration_ms)
                audio_segments.append(pause)

            time.sleep(0.1)

        except Exception as e:
            raise AudioRenderError(f"Failed to render line {i} ({speaker}): {str(e)}")
    
    print("\nStitching audio segments...")
    if not audio_segments:
        raise AudioRenderError("No audio segments were generated")
    
    final_audio = audio_segments[0]
    for segment in audio_segments[1:]:
        final_audio += segment
    
    print("Normalizing audio levels...")
    final_audio = normalize(final_audio)
    
    if intro_music_path:
        print(f"Adding intro background music from {intro_music_path}...")
        intro_music = load_background_music(intro_music_path, 5000)  # 5 seconds
        if intro_music:
            final_audio = intro_music.overlay(final_audio[:len(intro_music)]) + final_audio[len(intro_music):]
    
    if outro_music_path:
        print(f"Adding outro background music from {outro_music_path}...")
        outro_music = load_background_music(outro_music_path, 5000)  # 5 seconds
        if outro_music:
            outro_start = len(final_audio) - len(outro_music)
            final_audio = final_audio[:outro_start] + final_audio[outro_start:].overlay(outro_music)

    print(f"\nExporting to {audio_format.upper()} format...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    output_path = str(output_path)
    if not output_path.endswith(f".{audio_format}"):
        output_path = output_path.rsplit('.', 1)[0] + f".{audio_format}"

    try:
        if audio_format.lower() == "mp3":
            final_audio.export(output_path, format="mp3", bitrate="192k")
        elif audio_format.lower() == "wav":
            final_audio.export(output_path, format="wav")
        else:
            raise AudioRenderError(f"Unsupported audio format: {audio_format}")
    except FileNotFoundError as e:
        if audio_format.lower() == "mp3":
            raise AudioRenderError(
                "MP3 export requires ffmpeg. Please run the setup script:\n"
                "  python setup_ffmpeg.py\n\n"
                "Or install manually:\n"
                "  Windows: choco install ffmpeg (or download from ffmpeg.org)\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt-get install ffmpeg\n\n"
                "Alternatively, use --audio-format wav which works without ffmpeg."
            )
        else:
            raise AudioRenderError(f"Export failed: {str(e)}")

    duration_seconds = len(final_audio) / 1000.0
    print(f"\n✓ Audio rendering complete!")
    print(f"   Output: {output_path}")
    print(f"   Duration: {duration_seconds:.1f} seconds ({duration_seconds/60:.1f} minutes)")
    print(f"   Format: {audio_format.upper()}")

    return output_path


def validate_cartesia_credentials(api_key: str) -> bool:
    try:
        client = Cartesia(api_key=api_key)
        client.voices.list()
        return True
    except Exception as e:
        raise AudioRenderError(f"Invalid Cartesia credentials: {str(e)}")

