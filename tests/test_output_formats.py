"""
Test script for output format generation.

Tests:
1. JSONL transcript generation
2. VTT subtitle generation
3. Markdown show notes generation
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from output_writer import (
    write_transcript_jsonl,
    write_vtt_subtitles,
    write_show_notes,
    write_all_outputs,
    OutputWriterError
)


def load_test_data():
    """Load test script and stories."""
    test_output_dir = Path(__file__).parent / "test_output"
    
    script_path = test_output_dir / "test_script.json"
    stories_path = test_output_dir / "test_stories.json"
    
    if not script_path.exists() or not stories_path.exists():
        print("Error: Test data not found.")
        print(f"  Expected: {script_path}")
        print(f"  Expected: {stories_path}")
        return None, None
    
    with open(script_path, 'r') as f:
        script = json.load(f)
    
    with open(stories_path, 'r') as f:
        stories = json.load(f)
    
    return script, stories


def test_jsonl_transcript():
    """Test 1: JSONL transcript generation."""
    print("\n" + "="*50)
    print("TEST 1: JSONL Transcript Generation")
    print("="*50)
    
    try:
        script, stories = load_test_data()
        if not script or not stories:
            return False
        
        output_dir = Path(__file__).parent / "test_output"
        output_path = output_dir / "test_transcript.jsonl"
        
        result = write_transcript_jsonl(
            script=script,
            stories=stories,
            output_path=str(output_path),
            pause_duration_ms=1000
        )
        
        # Verify file exists and read first few lines
        if Path(result).exists():
            with open(result, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"✓ JSONL transcript created: {result}")
            print(f"  Lines: {len(lines)}")
            print(f"  Sample (first 3 lines):")
            for i, line in enumerate(lines[:3], 1):
                obj = json.loads(line)
                print(f"    Line {i}: t={obj['t']}s, speaker={obj['speaker']}, src={obj['src']}")
                print(f"            text=\"{obj['text'][:50]}...\"")
            return True
        else:
            print(f"✗ Output file not created: {result}")
            return False
        
    except Exception as e:
        print(f"✗ JSONL transcript generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vtt_subtitles():
    """Test 2: VTT subtitle generation."""
    print("\n" + "="*50)
    print("TEST 2: VTT Subtitle Generation")
    print("="*50)
    
    try:
        script, stories = load_test_data()
        if not script or not stories:
            return False
        
        output_dir = Path(__file__).parent / "test_output"
        output_path = output_dir / "test_episode.vtt"
        
        result = write_vtt_subtitles(
            script=script,
            output_path=str(output_path),
            pause_duration_ms=1000
        )
        
        # Verify file exists and read content
        if Path(result).exists():
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            print(f"✓ VTT subtitles created: {result}")
            print(f"  Lines: {len(lines)}")
            print(f"  Sample (first 20 lines):")
            for line in lines[:20]:
                print(f"    {line}")
            return True
        else:
            print(f"✗ Output file not created: {result}")
            return False
        
    except Exception as e:
        print(f"✗ VTT subtitle generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_show_notes():
    """Test 3: Markdown show notes generation."""
    print("\n" + "="*50)
    print("TEST 3: Markdown Show Notes Generation")
    print("="*50)
    
    try:
        script, stories = load_test_data()
        if not script or not stories:
            return False
        
        output_dir = Path(__file__).parent / "test_output"
        output_path = output_dir / "test_show_notes.md"
        
        result = write_show_notes(
            script=script,
            stories=stories,
            output_path=str(output_path),
            episode_title="Test Episode"
        )
        
        # Verify file exists and read content
        if Path(result).exists():
            with open(result, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            print(f"✓ Show notes created: {result}")
            print(f"  Lines: {len(lines)}")
            print(f"  Sample (first 30 lines):")
            for line in lines[:30]:
                print(f"    {line}")
            return True
        else:
            print(f"✗ Output file not created: {result}")
            return False
        
    except Exception as e:
        print(f"✗ Show notes generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_outputs():
    """Test 4: Generate all outputs at once."""
    print("\n" + "="*50)
    print("TEST 4: Generate All Outputs")
    print("="*50)
    
    try:
        script, stories = load_test_data()
        if not script or not stories:
            return False
        
        output_dir = Path(__file__).parent / "test_output"
        
        outputs = write_all_outputs(
            script=script,
            stories=stories,
            output_dir=str(output_dir),
            episode_name="test_complete",
            pause_duration_ms=1000
        )
        
        print(f"✓ All outputs generated:")
        for output_type, path in outputs.items():
            exists = Path(path).exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {output_type}: {path}")
        
        all_exist = all(Path(path).exists() for path in outputs.values())
        return all_exist
        
    except Exception as e:
        print(f"✗ All outputs generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all output format tests."""
    print("\n" + "="*50)
    print("OUTPUT FORMAT TEST SUITE")
    print("="*50)
    
    results = []
    
    # Test 1: JSONL transcript
    results.append(("JSONL Transcript", test_jsonl_transcript()))
    
    # Test 2: VTT subtitles
    results.append(("VTT Subtitles", test_vtt_subtitles()))
    
    # Test 3: Show notes
    results.append(("Show Notes", test_show_notes()))
    
    # Test 4: All outputs
    results.append(("All Outputs", test_all_outputs()))
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*50)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*50 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

