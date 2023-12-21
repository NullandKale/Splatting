import os
import sys
import shutil
import re
from extract_video import process_video

def sanitize_filename(filename):
    """ Sanitize the filename by replacing spaces and special characters. """
    return re.sub(r'[^a-zA-Z0-9_.]', '_', filename)

def find_all_video_files(location):
    """ Find all video files in the given directory without searching subdirectories. """
    video_files = []
    for file in os.listdir(location):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            full_path = os.path.join(location, file)
            video_files.append(full_path)
            print(f"found: {full_path}")
    return sorted(video_files, key=lambda x: os.path.getsize(x))


def process_all_videos(video_dir, temp_folder, frame_count, resolution, train_scale):
    """ Process all videos found in the specified directory. """
    video_files = find_all_video_files(video_dir)
    output_dir = os.path.join(os.path.dirname(video_dir), 'output')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for video in video_files:
        original_video_name = os.path.basename(video)
        sanitized_video_name = sanitize_filename(original_video_name)
        sanitized_folder_name = os.path.splitext(sanitized_video_name)[0]
        temp_video_folder = os.path.join(temp_folder, sanitize_filename(sanitized_folder_name))

        if not os.path.exists(temp_video_folder):
            os.makedirs(temp_video_folder)

        temp_video_path = os.path.join(temp_video_folder, sanitized_video_name)

        # Copy the video file to the temporary folder with the sanitized name
        shutil.copy(video, temp_video_path)

        try:
            process_video(temp_video_folder, frame_count, resolution, train_scale)

            # Rename and move the output .ply file if it exists
            ply_file_path = os.path.join(temp_video_folder, "out", "point_cloud", "iteration_30000", "point_cloud.ply")
            if os.path.exists(ply_file_path):
                new_ply_file_name = os.path.splitext(sanitized_video_name)[0] + '.ply'
                shutil.move(ply_file_path, os.path.join(output_dir, new_ply_file_name))

        except Exception as e:
            print(f"Error processing {sanitized_video_name}: {e}")
        finally:
            # Remove the temporary folder after processing
            shutil.rmtree(temp_video_folder, ignore_errors=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_all_videos.py <video dir location> <temp_folder_path> [frame_count] [resolution] [train_scale]")
        sys.exit(1)

    video_dir = sys.argv[1]
    temp_folder = sys.argv[2]
    frame_count = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    resolution = sys.argv[4] if len(sys.argv) > 4 else "2160x3840"
    train_scale = sys.argv[5] if len(sys.argv) > 5 else "0"

    process_all_videos(video_dir, temp_folder, frame_count, resolution, train_scale)
