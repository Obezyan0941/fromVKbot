import vk_api
import json
import time


def get_post(entered_id):
    access_token = 'cefa34bdcefa34bdcefa34bd87cdec8c5cccefacefa34bdab725c55a5f336c0e50a6dce'

    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()

    time_start = time.perf_counter()

    groups_ids = [
        "-206383151_69167",
        '-224244506_8',
        '-224244506_10']

    all_groups_response = vk.wall.getById(posts=groups_ids)
    print("Len: ", len(all_groups_response))
    print(json.dumps(all_groups_response, indent=4))
    time_end = time.perf_counter()
    time_elapsed_api_call = time_end - time_start
    print(f"Time elapsed api calls only: {time_elapsed_api_call}")

    quit()


    group_info = vk.groups.getById(group_id=entered_id)
    group_id = -group_info[0]['id']


    posts = vk.wall.get(owner_id=group_id, count=5)
    if posts['items'][2]['copy_history']:
        group_info_copied = vk.groups.getById(group_id=f"{posts['items'][2]['copy_history'][0]['from_id']}")
        print(group_info_copied)
        quit()

    print(json.dumps(posts['items'][2]['copy_history'][0], indent=4))
    # for attachment in posts['items'][1]['copy_history'][0]['attachments']:
    #     if attachment['type'] == 'photo':
    #         print(attachment['photo']['sizes'][4])

    quit()

    photo_urls = []

    # print(posts['items'][0]['attachments'][0]['photo']['sizes'])
    # input()

    for i in range(len(posts['items'])):
        # print(json.dumps(posts['items'], indent=4))
        print("_________________________________________________________________________")
        if "is_pinned" in posts['items'][i].keys() and posts['items'][i]['is_pinned'] == 1:
            continue
        print('id: ', posts['items'][i]['id'])
        print('likes: ', posts['items'][i]['likes'])
        print('views: ', posts['items'][i]['views'])
        print('reposts: ', posts['items'][i]['reposts'])
        print('post_type: ', posts['items'][i]['post_type'])
        print('text: ', posts['items'][i]['text'])
        print('attachments: ', json.dumps(posts['items'][i]['attachments'], indent=4))
        high_quality_ind = 0
        last_max = 0
        for attachment in posts['items'][i]['attachments']:
            for num, k in enumerate(attachment['photo']['sizes']):
                current_size = k['height'] + k['width']
                if current_size > last_max:
                    last_max = current_size
                    high_quality_ind = num
            # print(attachment['photo']['sizes'][high_quality_ind])
            photo_urls.append(attachment['photo']['sizes'][high_quality_ind]['url'])
        # print(posts['items'][i]['attachments'][0]['photo'].keys())

    # posts = vk.wall.get(owner_id=group_id, count=1)

    return posts['items'][0]['text'], photo_urls


if __name__ == "__main__":
    # group_id = "meme_kafe"
    group_id = "club224244506"
    time_start = time.perf_counter()

    text, pics = get_post(group_id)

    time_end = time.perf_counter()
    time_elapsed = time_end - time_start
    print(f"Time elapsed: {time_elapsed}")
    print(pics)
    print(text)
