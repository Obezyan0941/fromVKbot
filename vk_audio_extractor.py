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


def get_audio(post_id):
    access_token = 'cefa34bdcefa34bdcefa34bd87cdec8c5cccefacefa34bdab725c55a5f336c0e50a6dce'

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
    post_id = '-224244506_6'
    get_audio(post_id)



# escaped_text = r'\u041e\u0441\u0442\u0440\u043e\u0432 \u0441\u043e\u043a\u0440\u043e\u0432\u0438\u0449'
# normal_text = escaped_text.encode('utf-8').decode('unicode-escape')
# print(normal_text)

# print(json.dumps(post_info[0]['attachments'][1]["audio"]["url"], indent=4))



