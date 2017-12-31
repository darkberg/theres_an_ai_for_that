from moviepy.editor import ImageSequenceClip, VideoFileClip
from glob import glob
import os
import imageio
imageio.plugins.ffmpeg.download()

def process_video():

    base_path = "C:/Users/data/silly_walks/"
    use_audio = True
    data_path = base_path + "out/1/"
    video_filename_for_audio_only = base_path + "raw/videoplayback.mp4"
    out_path = base_path + "video_1.mp4"
    _fps = 25

    data = glob(os.path.join(data_path, "*.jpg"))
    print("Length of data:", len(data))
    print(data[:1])
    if use_audio == True:
        clipaudio = VideoFileClip(video_filename_for_audio_only)
        clipaudio.audio.write_audiofile("audio.mp3", fps = 44100)
        clip = ImageSequenceClip(data, fps=_fps)
        clip.write_videofile(out_path, codec='libx264', audio="audio.mp3")
    else:
        clip = ImageSequenceClip(data, fps=_fps)
        clip.write_videofile(out_path, audio=False)


process_video()