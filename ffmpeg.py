import os
import subprocess


def merge_video_audio(video_path, audio_path, output_path):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c", "copy", output_path], check=True)
    return output_path
