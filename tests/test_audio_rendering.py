"""
Test script for audio rendering functionality.

This script tests the audio renderer with a minimal script to verify:
1. Cartesia API connection
2. Voice mapping
3. Speech generation
4. Audio stitching
5. MP3/WAV export
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio_renderer import (
    render_audio,
    map_hosts_to_voices,
    validate_cartesia_credentials,
    AudioRenderError
)


def create_test_script():
    """Create a minimal test script."""
    return {
        "dialogue": [
            {
                "speaker": "Ben",
                "text": "Welcome to our test newscast!",
                "segment": "cold_open",
                "sources": []
            },
            {
                "speaker": "Jerry",
                "text": "Thanks for having me, Ben. This is a test of the audio rendering system.",
                "segment": "cold_open",
                "sources": []
            },
            {
                "speaker": "Ben",
                "text": "Let's see how well the Cartesia voices sound.",
                "segment": "story_0",
                "sources": []
            },
            {
                "speaker": "Jerry",
                "text": "Indeed. If you can hear this, the audio rendering is working perfectly.",
                "segment": "story_0",
                "sources": []
            },
            {
                "speaker": "Ben",
                "text": "That's all for our test. Thanks for listening!",
                "segment": "kicker",
                "sources": []
            }
        ],
        "rundown": [
            {"segment": "cold_open", "duration_estimate": 20},
            {"segment": "story_0", "duration_estimate": 15},
            {"segment": "kicker", "duration_estimate": 10}
        ],
        "disclaimer": ""
    }


def load_personas():
    """Load personas configuration."""
    personas_path = Path(__file__).parent / "config" / "personas.json"
    
    if not personas_path.exists():
        raise FileNotFoundError(f"Personas file not found: {personas_path}")
    
    with open(personas_path, 'r') as f:
        return json.load(f)


def test_voice_mapping():
    """Test 1: Voice mapping."""
    print("\n" + "="*50)
    print("TEST 1: Voice Mapping")
    print("="*50)
    
    try:
        personas = load_personas()
        voice_map = map_hosts_to_voices(personas)
        
        print("✓ Voice mapping successful:")
        for name, voice_id in voice_map.items():
            print(f"   {name} → {voice_id}")
        
        return True
    except Exception as e:
        print(f"✗ Voice mapping failed: {e}")
        return False


def test_cartesia_connection(api_key):
    """Test 2: Cartesia API connection."""
    print("\n" + "="*50)
    print("TEST 2: Cartesia API Connection")
    print("="*50)
    
    try:
        validate_cartesia_credentials(api_key)
        print("✓ Cartesia API connection successful")
        return True
    except Exception as e:
        print(f"✗ Cartesia API connection failed: {e}")
        return False


def test_audio_rendering(api_key, output_format="mp3"):
    """Test 3: Full audio rendering."""
    print("\n" + "="*50)
    print(f"TEST 3: Audio Rendering ({output_format.upper()})")
    print("="*50)
    
    try:
        # Create test output directory
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # Create test script and personas
        script = create_test_script()
        personas = load_personas()
        
        # Render audio
        output_path = output_dir / f"test_audio.{output_format}"
        result_path = render_audio(
            script=script,
            personas=personas,
            cartesia_api_key=api_key,
            output_path=str(output_path),
            pause_duration_ms=500,  # Shorter pauses for test
            audio_format=output_format
        )
        
        # Verify output file exists
        if Path(result_path).exists():
            file_size = Path(result_path).stat().st_size
            print(f"\n✓ Audio rendering successful!")
            print(f"   File: {result_path}")
            print(f"   Size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            return True
        else:
            print(f"✗ Output file not created: {result_path}")
            return False
        
    except AudioRenderError as e:
        error_msg = str(e)
        # Check if it's the expected ffmpeg missing error for MP3
        if "ffmpeg" in error_msg.lower() and output_format.lower() == "mp3":
            print(f"\n⊘ Skipped: MP3 requires ffmpeg (not installed)")
            print(f"   This is expected - MP3 is optional")
            print(f"   Install ffmpeg to enable MP3 support")
            return "skipped"
        else:
            print(f"✗ Audio rendering failed: {e}")
            return False
    except Exception as e:
        print(f"✗ Audio rendering failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all audio rendering tests."""
    print("\n" + "="*50)
    print("AUDIO RENDERING TEST SUITE")
    print("="*50)
    
    # Load environment
    load_dotenv()
    api_key = os.getenv('CARTESIA_API_KEY')
    
    if not api_key:
        print("\n✗ CARTESIA_API_KEY not found in .env file")
        print("   Please add your Cartesia API key to .env")
        return False
    
    # Run tests
    results = []
    
    # Test 1: Voice mapping
    results.append(("Voice Mapping", test_voice_mapping()))
    
    # Test 2: API connection
    results.append(("API Connection", test_cartesia_connection(api_key)))
    
    # Test 3: Audio rendering (MP3)
    results.append(("Audio Rendering (MP3)", test_audio_rendering(api_key, "mp3")))
    
    # Test 4: Audio rendering (WAV)
    results.append(("Audio Rendering (WAV)", test_audio_rendering(api_key, "wav")))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for test_name, result in results:
        if result == "skipped":
            status = "⊘ SKIPPED"
            skipped_count += 1
        elif result:
            status = "✓ PASSED"
            passed_count += 1
        else:
            status = "✗ FAILED"
            failed_count += 1
        print(f"{status}: {test_name}")
    
    # Consider skipped tests as acceptable (not failures)
    all_passed = all(result != False for result in [r[1] for r in results])
    
    print("\n" + "="*50)
    print(f"Results: {passed_count} passed, {failed_count} failed, {skipped_count} skipped")
    if all_passed:
        print("✓ ALL REQUIRED TESTS PASSED")
        if skipped_count > 0:
            print("  (Some optional tests were skipped)")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*50 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

