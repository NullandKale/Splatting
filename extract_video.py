import subprocess
import os
import sys
import json
import re

def get_video_frame_count(video_path):
    """ Get the total number of frames in the video. """
    cmd = f"ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=noprint_wrappers=1:nokey=1 {video_path}"
    result = subprocess.run(cmd, shell=True, capture_output=True)
    frame_count = result.stdout.strip()

    # If the frame count is 'N/A', use an alternative method to count frames
    if (frame_count == b'N/A' or frame_count == b''):
        cmd = f"ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of default=noprint_wrappers=1:nokey=1 {video_path}"
        result = subprocess.run(cmd, shell=True, capture_output=True)
        frame_count = result.stdout.strip()
        if re.match(b'^\\d+$', frame_count):  # Check if the output is a number
            return int(frame_count)
        else:
            raise ValueError(f"Unable to determine frame count for video: {video_path}")

    return int(frame_count)

def scale_and_extract_frames(video_path, output_dir, frame_count, resolution):
    """ Scale and extract a specific number of frames evenly from the video. """
    total_frames = get_video_frame_count(video_path)
    interval = max(1, total_frames // frame_count)

    new_width, new_height = resolution.split('x')
    cmd = f"ffmpeg -i {video_path} -vf \"select='not(mod(n\\,{interval}))',scale={new_width}:{new_height}:flags=lanczos\" -vsync vfr {output_dir}/%04d.png"
    subprocess.run(cmd, shell=True)

def run_colmap(location):
    """ Run the COLMAP process. """
    cmd = f"python convert.py -s {location}"
    subprocess.run(cmd, shell=True)

def run_training(source_location, model_location, train_scale):
    """ Run the training process with specified source path, model path, and scale. """
    cmd = f"python train.py -s {source_location} -m {model_location}"
    if train_scale != "0":
        cmd += f" -r {train_scale}"
    
    subprocess.run(cmd, shell=True)

def find_video_file(location):
    """ Find the first video file in the given directory. """
    for file in os.listdir(location):
        if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            return os.path.join(location, file)
    return None

def process_video(location, frame_count, resolution, train_scale):
    """ Process the first found video in the given location and run COLMAP and training. """
    video_path = find_video_file(location)
    if not video_path:
        print("No video file found in the specified location.")
        return

    output_dir = os.path.join(location, "input")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    scale_and_extract_frames(video_path, output_dir, frame_count, resolution)

    run_colmap(location)

    model_location = os.path.join(location, "out")
    run_training(location, model_location, train_scale)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_video.py <location> [frame_count] [resolution] [train_scale]")
        sys.exit(1)
    
    location = sys.argv[1]
    frame_count = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    resolution = sys.argv[3] if len(sys.argv) > 3 else "2160x3840"
    train_scale = sys.argv[4] if len(sys.argv) > 4 else "0"
    process_video(location, frame_count, resolution, train_scale)
