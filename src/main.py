import argparse
import os
from pathlib import Path
from dotenv import load_dotenv
from news import fetch_news, validate_news_data, NewsAPIError

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
    
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        stories = fetch_news(
            api_key=env['NEWSAPI_KEY'],
            topics=args.topics_list,
            region=args.region,
            max_stories=5
        )
        
        validate_news_data(stories)
        
        # TODO: Step 2 - Generate script
        # TODO: Step 3 - Render audio
        
        # TODO: Step 4 - Write outputs
        
    except NewsAPIError as e:
        print(f"\nNewsAPI Error: {e}")
        exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()