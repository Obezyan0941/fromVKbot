import yt_dlp
import shutil
import datetime


def get_video(url, id):

    def get_video_size(url):
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('duration', 0), info
    # 2000 sec

    video_duration, video_info = get_video_size(url)
    video_title = video_info.get('title', 'Video Title Not Available')
    print(video_title)
    print('video_duration: ', video_duration)

    if video_duration <= 2100:
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
    # url = "https://vk.com/video-224244506_456239017"
    # id = '-224244506_456239017'
    url = 'https://vk.com/real_wonderland?w=wall-222499729_2526&z=video-222499729_456239021'
    id = '-222499729_456239021'
    get_video(url, id)
