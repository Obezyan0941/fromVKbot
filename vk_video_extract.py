import yt_dlp   # library for downloading videos from YouTube, VK and other platforms
import shutil
import datetime


def get_video(url, id):

    def get_video_size(url):
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('duration', 0), info

    video_duration, video_info = get_video_size(url)
    video_title = video_info.get('title', 'Video Title Not Available')
    print(video_title)
    print('video_duration: ', video_duration)

    if video_duration <= 2100:  # 2100 seconds - limit for TeleBot to send video
        timestamp = str(int(datetime.datetime.now().timestamp()))
        new_file_name = f"{id}_[{timestamp}].mp4"
        ydl_otions = {'format': 'worst',
                      'max_filesize': 50 * 1024 * 1024,
                      'outtmpl': new_file_name}
        ydl = yt_dlp.YoutubeDL(ydl_otions)
        ydl.download(url)
        print(f"new_file_name: {new_file_name}")
        shutil.move(new_file_name, 'temp_videos/'+new_file_name)
        return [True, 'temp_videos/'+new_file_name, video_title]
    else:
        return [False]


if __name__ == "__main__":
    url = 'https://vk.com/group_name?w=wall-000000000_0000&z=video-000000000_000000000'     # sample video URL
    id = '-000000000_000000000'     # sample post ID
    get_video(url, id)
