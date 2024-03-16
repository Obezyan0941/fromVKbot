import os

def create_folders():
    if not os.path.isdir("temp_videos"):
        os.makedirs("temp_videos")
    if not os.path.isdir("temp_audios"):
        os.makedirs("temp_audios")
    if not os.path.isdir("error_logs"):
        os.makedirs("error_logs")


create_folders()
