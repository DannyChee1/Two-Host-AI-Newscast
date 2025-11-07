"""
Automatic ffmpeg setup for Windows.

Downloads and configures ffmpeg for MP3 export without requiring
manual installation or admin rights.
"""

import os
import sys
import zipfile
import urllib.request
from pathlib import Path
import shutil
import platform


def is_ffmpeg_available():
    """Check if ffmpeg is already available in PATH."""
    return shutil.which('ffmpeg') is not None


def get_ffmpeg_url():
    """Get the appropriate ffmpeg download URL for the platform."""
    system = platform.system()
    
    if system == 'Windows':
        # Using a reliable Windows build
        return "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    elif system == 'Darwin':  # macOS
        print("For macOS, please install ffmpeg using Homebrew:")
        print("  brew install ffmpeg")
        return None
    elif system == 'Linux':
        print("For Linux, please install ffmpeg using your package manager:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  CentOS/RHEL: sudo yum install ffmpeg")
        return None
    else:
        print(f"Unsupported platform: {system}")
        return None


def download_ffmpeg_windows(project_root: Path):
    """Download and extract ffmpeg for Windows."""
    ffmpeg_dir = project_root / "ffmpeg"
    
    # Check if already downloaded
    ffmpeg_exe = ffmpeg_dir / "bin" / "ffmpeg.exe"
    if ffmpeg_exe.exists():
        print(f"✓ ffmpeg already exists at: {ffmpeg_exe}")
        return str(ffmpeg_dir / "bin")
    
    print("\n" + "="*60)
    print("DOWNLOADING FFMPEG")
    print("="*60 + "\n")
    
    url = get_ffmpeg_url()
    if not url:
        return None
    
    zip_path = project_root / "ffmpeg.zip"
    
    try:
        # Download
        print(f"Downloading ffmpeg from {url}")
        print("This may take a few minutes (~100 MB)...")
        
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, (downloaded / total_size) * 100)
            print(f"\rProgress: {percent:.1f}% ({downloaded // (1024*1024)} MB / {total_size // (1024*1024)} MB)", end='')
        
        urllib.request.urlretrieve(url, zip_path, reporthook=report_progress)
        print("\n✓ Download complete!")
        
        # Extract
        print("\nExtracting ffmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Find the root folder in the zip
            namelist = zip_ref.namelist()
            root_folder = namelist[0].split('/')[0]
            
            # Extract all files
            zip_ref.extractall(project_root)
        
        # Rename the extracted folder to 'ffmpeg'
        extracted_path = project_root / root_folder
        if extracted_path.exists() and not ffmpeg_dir.exists():
            extracted_path.rename(ffmpeg_dir)
        
        # Clean up zip file
        zip_path.unlink()
        
        print(f"✓ ffmpeg installed at: {ffmpeg_dir / 'bin'}")
        print(f"✓ ffmpeg.exe location: {ffmpeg_dir / 'bin' / 'ffmpeg.exe'}")
        
        return str(ffmpeg_dir / "bin")
        
    except Exception as e:
        print(f"\n✗ Error downloading ffmpeg: {e}")
        if zip_path.exists():
            zip_path.unlink()
        return None


def add_to_path(ffmpeg_bin_path: str):
    """Add ffmpeg to system PATH for current session."""
    if ffmpeg_bin_path:
        current_path = os.environ.get('PATH', '')
        if ffmpeg_bin_path not in current_path:
            os.environ['PATH'] = ffmpeg_bin_path + os.pathsep + current_path
            print(f"\n✓ Added ffmpeg to PATH for current session")


def configure_pydub(ffmpeg_bin_path: str):
    """Configure pydub to use the local ffmpeg."""
    if ffmpeg_bin_path:
        # Set environment variable that pydub will use
        ffmpeg_exe = Path(ffmpeg_bin_path) / "ffmpeg.exe"
        if ffmpeg_exe.exists():
            os.environ['FFMPEG_BINARY'] = str(ffmpeg_exe)
            print(f"✓ Configured pydub to use: {ffmpeg_exe}")


def setup_ffmpeg():
    """Main setup function."""
    print("\n" + "="*60)
    print("FFMPEG SETUP")
    print("="*60 + "\n")
    
    # Check if already available
    if is_ffmpeg_available():
        print("✓ ffmpeg is already available in your system PATH")
        print("  Location:", shutil.which('ffmpeg'))
        return True
    
    print("⚠ ffmpeg not found in system PATH")
    print("  ffmpeg is required for MP3 export")
    print("  Setting up local ffmpeg installation...\n")
    
    # Get project root
    project_root = Path(__file__).parent
    
    # Platform-specific setup
    system = platform.system()
    
    if system == 'Windows':
        ffmpeg_bin_path = download_ffmpeg_windows(project_root)
        if ffmpeg_bin_path:
            add_to_path(ffmpeg_bin_path)
            configure_pydub(ffmpeg_bin_path)
            
            print("\n" + "="*60)
            print("✓ FFMPEG SETUP COMPLETE")
            print("="*60)
            print("\nffmpeg is now ready for MP3 export!")
            print(f"Location: {ffmpeg_bin_path}")
            return True
        else:
            return False
    else:
        print(f"\nAutomatic setup not available for {system}")
        print("Please install ffmpeg manually using the instructions above.")
        return False


def verify_ffmpeg():
    """Verify ffmpeg is working."""
    try:
        import subprocess
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"\n✓ ffmpeg is working: {version_line}")
            return True
    except Exception as e:
        print(f"\n✗ ffmpeg verification failed: {e}")
    
    return False


if __name__ == "__main__":
    print("\nTwo-Host AI Newscast - ffmpeg Setup")
    print("="*60)
    
    success = setup_ffmpeg()
    
    if success:
        verify_ffmpeg()
        print("\n✓ You can now use MP3 format for audio export!")
        print("\nTest it with:")
        print("  python test_audio_rendering.py")
        sys.exit(0)
    else:
        print("\n✗ ffmpeg setup failed")
        print("\nYou can still use WAV format:")
        print("  python src/main.py --personas config/personas.json --audio-format wav")
        sys.exit(1)

