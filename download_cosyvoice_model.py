#!/usr/bin/env python3
"""
Download CosyVoice2-0.5B model from ModelScope

This script downloads the CosyVoice2-0.5B model and saves it to the models directory.
"""
import os
import sys
from pathlib import Path

# Add CosyVoice to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "third_party" / "CosyVoice"))

try:
    from modelscope import snapshot_download
except ImportError:
    print("Error: modelscope not installed. Please install it first:")
    print("pip install modelscope==1.20.0")
    sys.exit(1)

def download_model():
    """Download CosyVoice2-0.5B model"""
    model_dir = project_root / "models" / "CosyVoice2-0.5B"

    print(f"Downloading CosyVoice2-0.5B model to: {model_dir}")
    print("This may take a while (model size ~1.5GB)...")

    try:
        # Download model from ModelScope
        snapshot_download(
            'iic/CosyVoice2-0.5B',
            local_dir=str(model_dir),
            revision='master'
        )

        print(f"\nModel downloaded successfully to: {model_dir}")
        print("\nModel files:")
        for file in model_dir.rglob("*"):
            if file.is_file():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"  {file.relative_to(model_dir)}: {size_mb:.2f} MB")

        return True
    except Exception as e:
        print(f"Error downloading model: {e}")
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
