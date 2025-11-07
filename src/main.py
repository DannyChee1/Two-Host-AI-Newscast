import argparse
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from news import fetch_news, validate_news_data, NewsAPIError
from script_generator import generate_script, format_script_for_display, ScriptGenerationError
from audio_renderer import render_audio, AudioRenderError
from output_writer import write_all_outputs, OutputWriterError

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generate a two-host AI newscast podcast from today\'s top news.',
        epilog='''
        Examples:
            python main.py --personas config/personas.json --minutes 7 --topics tech,world
        '''
    )
    
    parser.add_argument(
        '--personas',
        type=str,
        required=True,
        help='Persona file defining characteristics for the two hosts'
    )
    
    # Other optional arguments
    parser.add_argument(
        '--minutes',
        type=int,
        default=5,
        help='Target duration in minutes (default: 5 minutes)'
    )
    
    parser.add_argument(
        '--topics',
        type=str,
        default='general',
        help='Comma-separated list of topics/categories (e.g., tech,world,science) (default: general)'
    )
    
    parser.add_argument(
        '--region',
        type=str,
        default='us',
        help='Region/country code for news sources (e.g., us, gb, ca) (default: us)'
    )
    
    parser.add_argument(
        '--profanity-filter',
        action='store_true',
        help='Enable profanity filtering in script generation'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='out',
        help='Directory for output files (default: out)'
    )
    
    parser.add_argument(
        '--audio-format',
        type=str,
        choices=['mp3', 'wav'],
        default='mp3',
        help='Audio output format (default: mp3)'
    )
    
    parser.add_argument(
        '--pause-duration',
        type=int,
        default=1000,
        help='Pause duration between dialogue lines in milliseconds (default: 1000)'
    )
    
    parser.add_argument(
        '--intro-music',
        type=str,
        default=None,
        help='Path to intro background music file (optional)'
    )
    
    parser.add_argument(
        '--outro-music',
        type=str,
        default=None,
        help='Path to outro background music file (optional)'
    )
    
    parser.add_argument(
        '--skip-audio',
        action='store_true',
        help='Skip audio rendering (script generation only)'
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.personas):
        parser.error(f"Personas file not found: {args.personas}")
    
    args.topics_list = [topic.strip() for topic in args.topics.split(',')]
    
    return args


def load_environment():
    load_dotenv()
    
    required_keys = ['NEWSAPI_KEY', 'OPENAI_API_KEY', 'CARTESIA_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Error: Missing required API keys in .env file:")
        for key in missing_keys:
            print(f"   - {key}")
        exit(1)
    
    return {
        'newsapi_key': os.getenv('NEWSAPI_KEY'),
        'openai_key': os.getenv('OPENAI_API_KEY'),
        'cartesia_key': os.getenv('CARTESIA_API_KEY')
    }


def main():
    """Main entry point for the newscast generator."""
    print("Two-Host AI Newscast (Podcast)\n" + "=" * 50 + "\n")
    
    args = parse_arguments()
    env = load_environment()
    
    print(f"Configuration:")
    print(f"   Personas: {args.personas}")
    print(f"   Duration: {args.minutes} minutes")
    print(f"   Topics: {', '.join(args.topics_list)}")
    print(f"   Region: {args.region}")
    print(f"   Profanity filter: {'ON' if args.profanity_filter else 'OFF'}")
    print(f"   Output directory: {args.output_dir}")
    print(f"   Audio format: {args.audio_format.upper()}")
    print(f"   Skip audio: {'YES' if args.skip_audio else 'NO'}")
    
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    with open(args.personas, 'r') as f:
        personas = json.load(f)
    
    try:
        stories = fetch_news(
            api_key=env['newsapi_key'],
            topics=args.topics_list,
            region=args.region,
            max_stories=5
        )
        
        validate_news_data(stories)
        
        # Save stories for later use
        stories_path = Path(args.output_dir) / 'stories.json'
        Path(args.output_dir).mkdir(parents=True, exist_ok=True)
        with open(stories_path, 'w', encoding='utf-8') as f:
            json.dump(stories, f, indent=2)
        
        script = generate_script(
            stories=stories,
            personas=personas,
            openai_api_key=env['openai_key'],
            target_duration=args.minutes,
            profanity_filter=args.profanity_filter
        )
        
        print("\n" + format_script_for_display(script))
        
        script_path = Path(args.output_dir) / 'script.json'
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2)
        
        script_txt_path = Path(args.output_dir) / 'script.txt'
        with open(script_txt_path, 'w', encoding='utf-8') as f:
            f.write(format_script_for_display(script))
        
        # Step 3 - Render audio
        audio_duration_ms = None
        if not args.skip_audio:
            audio_path = Path(args.output_dir) / f'episode.{args.audio_format}'
            audio_result = render_audio(
                script=script,
                personas=personas,
                cartesia_api_key=env['cartesia_key'],
                output_path=str(audio_path),
                pause_duration_ms=args.pause_duration,
                intro_music_path=args.intro_music,
                outro_music_path=args.outro_music,
                audio_format=args.audio_format
            )
            # Try to get audio duration for timestamps (optional)
            audio_duration_ms = None
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_result)
                audio_duration_ms = len(audio)
            except Exception:
                # If we can't read the audio file, timestamps will be estimated
                pass
        else:
            print("\n⊘ Skipping audio rendering (--skip-audio enabled)")
            audio_path = None
        
        # Step 4 - Write additional outputs (transcript, VTT, show notes)
        print(f"\n{'='*50}")
        print("GENERATING ADDITIONAL OUTPUTS")
        print(f"{'='*50}\n")
        
        output_files = write_all_outputs(
            script=script,
            stories=stories,
            output_dir=args.output_dir,
            episode_name="episode",
            pause_duration_ms=args.pause_duration,
            audio_duration_ms=audio_duration_ms
        )
        
        print(f"✓ Transcript (JSONL): {output_files['transcript_jsonl']}")
        print(f"✓ Subtitles (VTT): {output_files['vtt']}")
        print(f"✓ Show Notes (Markdown): {output_files['show_notes']}")
        
        # Step 5 - Output summary
        print(f"\n{'='*50}")
        print("OUTPUT SUMMARY")
        print(f"{'='*50}")
        print(f"\n✓ Stories JSON: {stories_path}")
        print(f"✓ Script JSON: {script_path}")
        print(f"✓ Script TXT: {script_txt_path}")
        if not args.skip_audio:
            print(f"✓ Audio: {audio_path}")
        print(f"✓ Transcript (JSONL): {output_files['transcript_jsonl']}")
        print(f"✓ Subtitles (VTT): {output_files['vtt']}")
        print(f"✓ Show Notes: {output_files['show_notes']}")
        print(f"\n✓ All outputs saved to: {args.output_dir}/")
        print(f"\n{'='*50}\n")
        
    except NewsAPIError as e:
        print(f"\nNewsAPI Error: {e}")
        exit(1)
    except ScriptGenerationError as e:
        print(f"\nScript Generation Error: {e}")
        exit(1)
    except AudioRenderError as e:
        print(f"\nAudio Rendering Error: {e}")
        exit(1)
    except OutputWriterError as e:
        print(f"\nOutput Writing Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()