#!/usr/bin/env python3
"""
MP4 Video Merger Script
Merges multiple MP4 files in each chapter folder into a single video.
"""

import os
import subprocess
import sys
import re
from pathlib import Path
from typing import List, Tuple

# Configuration
LECTURES_DIR = "CSE6250_Lectures"
OUTPUT_DIR = "merged_output"
TEMP_CONCAT_FILE = "temp_concat_list.txt"


def check_ffmpeg():
    """Check if FFmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ FFmpeg is installed and ready")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg is not installed or not in PATH")
        print("\nPlease install FFmpeg:")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")
        return False


def natural_sort_key(filename: str) -> List:
    """
    Extract numeric prefix from filename for natural sorting.
    Examples: "0 - Introduction.mp4" -> 0, "75 - Intro.mp4" -> 75
    """
    match = re.match(r'^(\d+)', filename)
    if match:
        return [int(match.group(1))]
    return [float('inf')]  # Put non-matching files at the end


def get_chapter_folders(lectures_dir: str) -> List[Path]:
    """Get all numbered chapter folders sorted by chapter number."""
    lectures_path = Path(lectures_dir)

    if not lectures_path.exists():
        print(f"✗ Directory not found: {lectures_dir}")
        return []

    # Find all directories that start with a number followed by underscore
    chapter_folders = [
        d for d in lectures_path.iterdir()
        if d.is_dir() and re.match(r'^\d+_', d.name)
    ]

    # Sort by the numeric prefix
    chapter_folders.sort(key=lambda x: int(re.match(r'^(\d+)', x.name).group(1)))

    return chapter_folders


def get_video_files(chapter_folder: Path) -> List[Path]:
    """Get all MP4 files in a chapter folder, sorted by numeric prefix."""
    mp4_files = list(chapter_folder.glob("*.mp4"))

    # Sort by numeric prefix
    mp4_files.sort(key=lambda x: natural_sort_key(x.name))

    return mp4_files


def create_concat_file(video_files: List[Path], concat_file: Path) -> None:
    """Create a concat demuxer file list for FFmpeg."""
    with open(concat_file, 'w', encoding='utf-8') as f:
        for video in video_files:
            # FFmpeg requires absolute paths or paths relative to concat file
            # Escape single quotes in filenames
            safe_path = str(video.absolute()).replace("'", "'\\''")
            f.write(f"file '{safe_path}'\n")


def merge_videos(chapter_folder: Path, output_dir: Path, verbose: bool = False) -> bool:
    """
    Merge all videos in a chapter folder into a single MP4 file.

    Args:
        chapter_folder: Path to the chapter folder containing MP4 files
        output_dir: Path to the output directory
        verbose: Show detailed FFmpeg output

    Returns:
        True if successful, False otherwise
    """
    chapter_name = chapter_folder.name
    print(f"\n{'='*60}")
    print(f"Processing: {chapter_name}")
    print(f"{'='*60}")

    # Get video files
    video_files = get_video_files(chapter_folder)

    if not video_files:
        print(f"⚠ No MP4 files found in {chapter_name}")
        return False

    print(f"Found {len(video_files)} video files:")
    for i, video in enumerate(video_files, 1):
        print(f"  {i}. {video.name}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create temporary concat file
    concat_file = Path(TEMP_CONCAT_FILE)
    create_concat_file(video_files, concat_file)

    # Output file path
    output_file = output_dir / f"{chapter_name}_merged.mp4"

    # FFmpeg command using concat demuxer
    cmd = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",  # Copy streams without re-encoding (fast & lossless)
        "-y",  # Overwrite output file if exists
        str(output_file)
    ]

    print(f"\nMerging videos...")
    print(f"Output: {output_file}")

    try:
        # Run FFmpeg
        if verbose:
            result = subprocess.run(cmd, check=True)
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

        # Clean up temporary file
        if concat_file.exists():
            concat_file.unlink()

        # Verify output file was created
        if output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"✓ Successfully merged! Output size: {size_mb:.2f} MB")
            return True
        else:
            print(f"✗ Output file was not created")
            return False

    except subprocess.CalledProcessError as e:
        print(f"✗ FFmpeg error occurred")
        if verbose or (hasattr(e, 'stderr') and e.stderr):
            print(f"Error details: {e.stderr if hasattr(e, 'stderr') else str(e)}")

        # Clean up temporary file
        if concat_file.exists():
            concat_file.unlink()

        return False


def main():
    """Main execution function."""
    print("=" * 60)
    print("MP4 Video Merger for CSE6250 Lectures")
    print("=" * 60)

    # Check FFmpeg
    if not check_ffmpeg():
        sys.exit(1)

    # Get chapter folders
    print(f"\nScanning for chapter folders in: {LECTURES_DIR}")
    chapter_folders = get_chapter_folders(LECTURES_DIR)

    if not chapter_folders:
        print("✗ No chapter folders found")
        sys.exit(1)

    print(f"✓ Found {len(chapter_folders)} chapter folders")

    # Process each chapter
    output_dir = Path(OUTPUT_DIR)
    successful = 0
    failed = 0

    for chapter_folder in chapter_folders:
        if merge_videos(chapter_folder, output_dir, verbose=False):
            successful += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("MERGE COMPLETE - SUMMARY")
    print("=" * 60)
    print(f"Total chapters processed: {len(chapter_folders)}")
    print(f"✓ Successful merges: {successful}")
    if failed > 0:
        print(f"✗ Failed merges: {failed}")
    print(f"\nMerged videos saved to: {output_dir.absolute()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
