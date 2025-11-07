"""
Comprehensive test suite for the Two-Host AI Newscast system.

Tests:
1. News fetching (news.py)
2. Script generation (script_generator.py)
3. Full integration test

Run with: python test_newscast.py
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from news import fetch_news, validate_news_data, deduplicate_articles, NewsAPIError
from script_generator import (
    generate_script, 
    format_script_for_display, 
    ScriptGenerationError,
    _build_system_prompt,
    _build_user_prompt,
    _validate_script
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, description):
    """Print a test step."""
    print(f"\n[STEP {step_num}] {description}")
    print("-" * 70)


def print_success(message):
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message):
    """Print an error message."""
    print(f"✗ {message}")


def print_info(message, indent=1):
    """Print an info message."""
    prefix = "  " * indent
    print(f"{prefix}• {message}")


# =============================================================================
# TEST 1: NEWS FETCHING MODULE
# =============================================================================

def test_news_module():
    """Test the news fetching module."""
    print_section("TEST 1: NEWS FETCHING MODULE")
    
    try:
        # Load API key
        print_step(1, "Loading environment variables")
        load_dotenv()
        api_key = os.getenv('NEWSAPI_KEY')
        
        if not api_key:
            print_error("NEWSAPI_KEY not found in .env file")
            print_info("Create a .env file with: NEWSAPI_KEY=your_key_here", indent=1)
            return False, None
        
        print_success(f"NEWSAPI_KEY loaded (length: {len(api_key)})")
        
        # Test 1.1: Fetch news with specific topics
        print_step(2, "Fetching news stories with topics: ['AI', 'Machine Learning']")
        stories = fetch_news(
            api_key=api_key,
            topics=['AI', 'Machine Learning'],
            region='us',
            max_stories=3,
            hours_back=48  # Look back 48 hours for better results
        )
        
        print_success(f"Fetched {len(stories)} stories")
        
        # Display story details
        for idx, story in enumerate(stories):
            print_info(f"Story {idx}:", indent=1)
            print_info(f"Title: {story['title'][:80]}...", indent=2)
            print_info(f"Source: {story['source']}", indent=2)
            print_info(f"URL: {story['url'][:60]}...", indent=2)
            print_info(f"Summary: {story['summary']}", indent=2)
            print_info(f"Summary length: {len(story['summary'])} chars", indent=2)
            if story.get('publishedAt'):
                print_info(f"Published: {story['publishedAt']}", indent=2)
        
        # Test 1.2: Validate news data
        print_step(3, "Validating news data structure")
        validate_news_data(stories)
        print_success("All stories have required fields and valid data")
        
        # Test 1.3: Check data quality
        print_step(4, "Checking data quality")
        for idx, story in enumerate(stories):
            if len(story['summary']) < 20:
                print_error(f"Story {idx} has very short summary: {len(story['summary'])} chars")
            else:
                print_info(f"Story {idx} summary length OK: {len(story['summary'])} chars", indent=1)
        
        # Test 1.4: Test deduplication
        print_step(5, "Testing deduplication functionality")
        
        # Create some duplicate articles for testing
        test_articles = [
            {
                'url': 'https://example.com/1',
                'title': 'AI Breakthrough in Machine Learning',
                'description': 'Test article 1'
            },
            {
                'url': 'https://example.com/1',  # Same URL
                'title': 'AI Breakthrough in Machine Learning',
                'description': 'Test article 1 duplicate'
            },
            {
                'url': 'https://example.com/2',
                'title': 'AI Breakthrough in Machine Learning Technology',  # Similar title
                'description': 'Test article 2'
            },
            {
                'url': 'https://example.com/3',
                'title': 'Completely Different Story About Weather',
                'description': 'Test article 3'
            }
        ]
        
        unique = deduplicate_articles(test_articles)
        print_info(f"Input articles: {len(test_articles)}", indent=1)
        print_info(f"After deduplication: {len(unique)}", indent=1)
        print_info(f"Duplicates removed: {len(test_articles) - len(unique)}", indent=1)
        
        if len(unique) < len(test_articles):
            print_success("Deduplication working correctly")
        else:
            print_error("Deduplication may not be working")
        
        print_section("TEST 1 COMPLETE: NEWS MODULE ✓")
        return True, stories
        
    except NewsAPIError as e:
        print_error(f"NewsAPI Error: {e}")
        return False, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


# =============================================================================
# TEST 2: SCRIPT GENERATION MODULE
# =============================================================================

def test_script_generation_module(sample_stories=None):
    """Test the script generation module."""
    print_section("TEST 2: SCRIPT GENERATION MODULE")
    
    try:
        # Load API key and personas
        print_step(1, "Loading environment and personas")
        load_dotenv()
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not openai_key:
            print_error("OPENAI_API_KEY not found in .env file")
            return False
        
        print_success(f"OPENAI_API_KEY loaded (length: {len(openai_key)})")
        
        # Load personas
        personas_path = Path('config/personas.json')
        if not personas_path.exists():
            print_error(f"Personas file not found: {personas_path}")
            return False
        
        with open(personas_path, 'r') as f:
            personas = json.load(f)
        
        print_success(f"Loaded {len(personas['hosts'])} host personas")
        for host in personas['hosts']:
            print_info(f"{host['name']}: {host['personality'][:60]}...", indent=1)
        
        # Use sample stories or create mock ones
        if sample_stories:
            print_step(2, "Using real news stories from previous test")
            stories = sample_stories
        else:
            print_step(2, "Creating mock news stories for testing")
            stories = [
                {
                    'id': 0,
                    'title': 'Major AI Breakthrough in Natural Language Processing',
                    'source': 'Tech News Daily',
                    'summary': 'Researchers have developed a new model that achieves state-of-the-art results in language understanding tasks.',
                    'url': 'https://example.com/ai-breakthrough',
                    'publishedAt': '2025-11-06T10:00:00Z'
                },
                {
                    'id': 1,
                    'title': 'New Study Reveals Impact of AI on Job Market',
                    'source': 'Business Insider',
                    'summary': 'A comprehensive study shows that AI is creating more jobs than it eliminates, particularly in tech sectors.',
                    'url': 'https://example.com/ai-jobs',
                    'publishedAt': '2025-11-06T09:30:00Z'
                },
                {
                    'id': 2,
                    'title': 'Tech Giants Announce Collaboration on AI Safety',
                    'source': 'Reuters',
                    'summary': 'Leading technology companies form alliance to develop safety standards for artificial intelligence systems.',
                    'url': 'https://example.com/ai-safety',
                    'publishedAt': '2025-11-06T08:00:00Z'
                }
            ]
        
        print_success(f"Using {len(stories)} stories for script generation")
        
        # Test 2.1: Test prompt building
        print_step(3, "Testing prompt generation")
        
        system_prompt = _build_system_prompt(personas, target_duration=5, profanity_filter=True)
        print_success(f"System prompt generated ({len(system_prompt)} characters)")
        print_info("System prompt includes:", indent=1)
        print_info("- Host personalities and styles", indent=2)
        print_info("- Structure requirements (cold open, stories, kicker)", indent=2)
        print_info("- Sourcing rules ([src: i] annotations)", indent=2)
        print_info("- Tone and quality guidelines", indent=2)
        print_info("- JSON output format specification", indent=2)
        
        user_prompt = _build_user_prompt(stories)
        print_success(f"User prompt generated ({len(user_prompt)} characters)")
        print_info(f"Contains {len(stories)} news stories with full details", indent=1)
        
        # Test 2.2: Generate actual script
        print_step(4, "Generating script with ChatGPT (this may take 10-30 seconds)")
        print_info("Calling OpenAI API...", indent=1)
        
        script = generate_script(
            stories=stories,
            personas=personas,
            openai_api_key=openai_key,
            target_duration=5,
            profanity_filter=True
        )
        
        print_success("Script generated successfully!")
        
        # Test 2.3: Validate script structure
        print_step(5, "Analyzing generated script")
        
        print_info(f"Rundown segments: {len(script['rundown'])}", indent=1)
        for seg in script['rundown']:
            print_info(f"- {seg['segment']}: ~{seg.get('duration_estimate', 0)}s", indent=2)
        
        print_info(f"Dialogue lines: {len(script['dialogue'])}", indent=1)
        
        # Count lines per speaker
        speaker_counts = {}
        for line in script['dialogue']:
            speaker = line['speaker']
            speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
        
        print_info("Lines per speaker:", indent=1)
        for speaker, count in speaker_counts.items():
            print_info(f"- {speaker}: {count} lines ({count/len(script['dialogue'])*100:.1f}%)", indent=2)
        
        # Check for source annotations
        all_text = ' '.join([line['text'] for line in script['dialogue']])
        src_count = all_text.count('[src:')
        print_info(f"Source annotations: {src_count} total", indent=1)
        
        # Check for disclaimer
        if script.get('disclaimer'):
            print_info(f"Disclaimer included: {script['disclaimer'][:80]}...", indent=1)
        else:
            print_info("No disclaimer (topics may not be sensitive)", indent=1)
        
        # Test 2.4: Validate script
        print_step(6, "Running script validation")
        _validate_script(script, stories)
        print_success("Script passes all validation checks")
        
        # Test 2.5: Test formatting
        print_step(7, "Testing script formatting for display")
        formatted = format_script_for_display(script)
        print_success(f"Formatted script ({len(formatted)} characters)")
        print_info("Preview (first 500 chars):", indent=1)
        print("\n" + "-" * 70)
        print(formatted[:500] + "...")
        print("-" * 70)
        
        print_section("TEST 2 COMPLETE: SCRIPT GENERATION MODULE ✓")
        return True, script
        
    except ScriptGenerationError as e:
        print_error(f"Script Generation Error: {e}")
        return False, None
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


# =============================================================================
# TEST 3: FULL INTEGRATION TEST
# =============================================================================

def test_full_integration():
    """Test the complete workflow from news fetching to script generation."""
    print_section("TEST 3: FULL INTEGRATION TEST")
    
    try:
        # Setup
        print_step(1, "Setting up integration test environment")
        load_dotenv()
        
        newsapi_key = os.getenv('NEWSAPI_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if not newsapi_key or not openai_key:
            print_error("Missing required API keys")
            return False
        
        print_success("All API keys loaded")
        
        # Load personas
        with open('config/personas.json', 'r') as f:
            personas = json.load(f)
        print_success("Personas loaded")
        
        # Step 1: Fetch news
        print_step(2, "Fetching real news stories")
        stories = fetch_news(
            api_key=newsapi_key,
            topics=['Artificial Intelligence', 'Technology'],
            region='us',
            max_stories=4,
            hours_back=72
        )
        
        validate_news_data(stories)
        print_success(f"Fetched and validated {len(stories)} stories")
        
        print_info("Story titles:", indent=1)
        for story in stories:
            print_info(f"- {story['title'][:70]}...", indent=2)
        
        # Step 2: Generate script
        print_step(3, "Generating complete newscast script")
        print_info("This will take 10-30 seconds...", indent=1)
        
        script = generate_script(
            stories=stories,
            personas=personas,
            openai_api_key=openai_key,
            target_duration=5,
            profanity_filter=True
        )
        
        print_success("Script generated!")
        
        # Step 3: Analyze complete output
        print_step(4, "Analyzing complete newscast")
        
        total_duration = sum(seg.get('duration_estimate', 0) for seg in script['rundown'])
        print_info(f"Total estimated duration: {total_duration} seconds ({total_duration/60:.1f} minutes)", indent=1)
        print_info(f"Total dialogue lines: {len(script['dialogue'])}", indent=1)
        
        # Word count
        total_words = sum(len(line['text'].split()) for line in script['dialogue'])
        print_info(f"Total words: {total_words}", indent=1)
        print_info(f"Words per minute: {total_words / (total_duration/60):.0f}", indent=1)
        
        # Segment breakdown
        print_info("Segment breakdown:", indent=1)
        segments = {}
        for line in script['dialogue']:
            seg = line['segment']
            segments[seg] = segments.get(seg, [])
            segments[seg].append(line)
        
        for seg_name, lines in segments.items():
            words = sum(len(line['text'].split()) for line in lines)
            print_info(f"- {seg_name}: {len(lines)} lines, {words} words", indent=2)
        
        # Check story coverage
        print_info("Story coverage:", indent=1)
        for story in stories:
            story_id = story['id']
            mentions = sum(1 for line in script['dialogue'] if story_id in line.get('sources', []))
            print_info(f"- Story {story_id}: mentioned in {mentions} dialogue lines", indent=2)
        
        # Step 4: Save output
        print_step(5, "Saving integration test output")
        
        output_dir = Path('test_output')
        output_dir.mkdir(exist_ok=True)
        
        # Save stories
        stories_path = output_dir / 'test_stories.json'
        with open(stories_path, 'w', encoding='utf-8') as f:
            json.dump(stories, f, indent=2)
        print_success(f"Stories saved to {stories_path}")
        
        # Save script (JSON)
        script_path = output_dir / 'test_script.json'
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, indent=2)
        print_success(f"Script (JSON) saved to {script_path}")
        
        # Save script (formatted)
        formatted_path = output_dir / 'test_script.txt'
        with open(formatted_path, 'w', encoding='utf-8') as f:
            f.write(format_script_for_display(script))
        print_success(f"Script (formatted) saved to {formatted_path}")
        
        # Step 5: Display final script
        print_step(6, "Displaying complete script")
        print("\n" + format_script_for_display(script))
        
        print_section("TEST 3 COMPLETE: FULL INTEGRATION ✓")
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# MAIN TEST RUNNER
# =============================================================================

def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "TWO-HOST AI NEWSCAST TEST SUITE" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")
    
    results = []
    
    # Test 1: News Module
    test1_passed, sample_stories = test_news_module()
    results.append(('News Module', test1_passed))
    
    if not test1_passed:
        print("\n⚠ Skipping remaining tests due to news module failure")
        return
    
    # Test 2: Script Generation Module
    test2_passed, sample_script = test_script_generation_module(sample_stories)
    results.append(('Script Generation Module', test2_passed))
    
    if not test2_passed:
        print("\n⚠ Skipping integration test due to script generation failure")
        return
    
    # Test 3: Full Integration
    test3_passed = test_full_integration()
    results.append(('Full Integration', test3_passed))
    
    # Summary
    print_section("TEST SUMMARY")
    print()
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name:.<50} {status}")
    
    all_passed = all(passed for _, passed in results)
    
    print()
    if all_passed:
        print("  " + "=" * 66)
        print("  " + " " * 15 + "🎉 ALL TESTS PASSED! 🎉")
        print("  " + "=" * 66)
    else:
        print("  " + "=" * 66)
        print("  " + " " * 15 + "❌ SOME TESTS FAILED")
        print("  " + "=" * 66)
    
    print()


if __name__ == "__main__":
    main()

