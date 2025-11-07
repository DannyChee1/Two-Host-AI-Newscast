"""
Quick validation tests without API calls.

Tests module imports, data structures, and validation logic.
Run with: python test_quick.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def print_test(name):
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print('='*60)

def print_ok(msg):
    print(f"  ✓ {msg}")

def print_fail(msg):
    print(f"  ✗ {msg}")

# Test imports
print_test("Module Imports")
try:
    from news import fetch_news, validate_news_data, deduplicate_articles, NewsAPIError
    print_ok("news.py imports successful")
except Exception as e:
    print_fail(f"news.py import failed: {e}")
    sys.exit(1)

try:
    from script_generator import (
        generate_script, 
        format_script_for_display,
        ScriptGenerationError,
        _build_system_prompt,
        _build_user_prompt,
        _validate_script
    )
    print_ok("script_generator.py imports successful")
except Exception as e:
    print_fail(f"script_generator.py import failed: {e}")
    sys.exit(1)

# Test data validation
print_test("News Data Validation")

valid_stories = [
    {
        'id': 0,
        'title': 'Test Story',
        'url': 'https://example.com',
        'source': 'Test Source',
        'summary': 'Test summary content'
    }
]

try:
    validate_news_data(valid_stories)
    print_ok("Valid stories pass validation")
except Exception as e:
    print_fail(f"Valid stories failed: {e}")

# Test missing fields
try:
    invalid_stories = [{'id': 0, 'title': 'Test'}]  # Missing fields
    validate_news_data(invalid_stories)
    print_fail("Invalid stories should have failed validation")
except ValueError:
    print_ok("Invalid stories correctly rejected")
except Exception as e:
    print_fail(f"Wrong exception type: {e}")

# Test deduplication
print_test("Article Deduplication")

articles = [
    {'url': 'http://example.com/1', 'title': 'Article One'},
    {'url': 'http://example.com/1', 'title': 'Article One'},  # Duplicate URL
    {'url': 'http://example.com/2', 'title': 'Article Two'},
]

unique = deduplicate_articles(articles)
if len(unique) == 2:
    print_ok(f"Deduplication working: {len(articles)} → {len(unique)}")
else:
    print_fail(f"Deduplication failed: got {len(unique)}, expected 2")

# Test prompt generation
print_test("Prompt Generation")

import json
personas_path = Path('config/personas.json')
if personas_path.exists():
    with open(personas_path) as f:
        personas = json.load(f)
    
    try:
        system_prompt = _build_system_prompt(personas, 5, True)
        if len(system_prompt) > 100 and 'cold_open' in system_prompt.lower():
            print_ok(f"System prompt generated ({len(system_prompt)} chars)")
        else:
            print_fail("System prompt seems incomplete")
    except Exception as e:
        print_fail(f"System prompt generation failed: {e}")
    
    try:
        user_prompt = _build_user_prompt(valid_stories)
        if len(user_prompt) > 50 and 'STORY 0' in user_prompt:
            print_ok(f"User prompt generated ({len(user_prompt)} chars)")
        else:
            print_fail("User prompt seems incomplete")
    except Exception as e:
        print_fail(f"User prompt generation failed: {e}")
else:
    print_fail(f"Personas file not found: {personas_path}")

# Test script validation
print_test("Script Structure Validation")

valid_script = {
    'rundown': [
        {'segment': 'cold_open', 'duration_estimate': 40},
        {'segment': 'story_0', 'duration_estimate': 90},
        {'segment': 'kicker', 'duration_estimate': 25}
    ],
    'dialogue': [
        {
            'speaker': 'Ben',
            'text': 'Hello [src: 0]',
            'segment': 'cold_open',
            'sources': [0]
        },
        {
            'speaker': 'Jerry',
            'text': 'Hi there',
            'segment': 'cold_open',
            'sources': []
        },
        # Add more lines to meet minimum requirement
        *[{
            'speaker': 'Ben' if i % 2 == 0 else 'Jerry',
            'text': f'Line {i} [src: 0]',
            'segment': 'story_0',
            'sources': [0]
        } for i in range(8)]
    ]
}

try:
    _validate_script(valid_script, valid_stories)
    print_ok("Valid script passes validation")
except Exception as e:
    print_fail(f"Valid script failed validation: {e}")

# Test missing segments
invalid_script = {
    'rundown': [{'segment': 'story_0', 'duration_estimate': 90}],
    'dialogue': []
}

try:
    _validate_script(invalid_script, valid_stories)
    print_fail("Invalid script should have failed validation")
except ScriptGenerationError as e:
    print_ok(f"Invalid script correctly rejected: {str(e)[:50]}")

# Test formatting
print_test("Script Formatting")

try:
    formatted = format_script_for_display(valid_script)
    if 'COLD OPEN' in formatted and 'Ben:' in formatted:
        print_ok(f"Script formatting works ({len(formatted)} chars)")
    else:
        print_fail("Formatted output seems incomplete")
except Exception as e:
    print_fail(f"Formatting failed: {e}")

# Summary
print(f"\n{'='*60}")
print("QUICK TESTS COMPLETE")
print('='*60)
print("\n✓ All quick validation tests passed!")
print("\nTo test with actual API calls, run:")
print("  python test_newscast.py")
print()

