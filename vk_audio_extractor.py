import shutil
import requests
import vk_api
import datetime


def download_audio(title, link):
    response = requests.get(link)

    current_datetime = str(int(datetime.datetime.now().timestamp()))
    filename = f"{str(title)}_[{current_datetime}].mp3"
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        shutil.move(filename, 'temp_audios/' + filename)
        print(f'Аудиофайл успешно скачан как {filename}')
        return 'temp_audios/' + filename
    else:
        return False


def get_audio(post_id):     # simply parsing vk-api data for direct links
    access_token = 'vk_api_access_token'

    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()

    post_info = vk.wall.getById(posts=post_id)
    post_attachments = post_info[0]['attachments']
    # print(json.dumps(post_attachments, indent=4))
    audio_files = []
    for ind, attachment in enumerate(post_attachments):
        if attachment['type'] != "audio":
            continue
        audio_attachment_dict = {
            'is_file': False,
            'url': attachment["audio"]["url"],
            'artist': attachment["audio"]['artist'],
            "title": attachment['audio']['title']}
        if int(attachment["audio"]["duration"]) >= 30:
            file_path = download_audio(audio_attachment_dict['title'], audio_attachment_dict["url"])
            if not file_path:
                continue
            audio_attachment_dict['is_file'] = True
            audio_attachment_dict['url'] = file_path
        audio_files.append(audio_attachment_dict)

    print(audio_files)
    return audio_files


if __name__ == "__main__":
    post_id = '-000000000_0'    # sample post ID
    get_audio(post_id)


