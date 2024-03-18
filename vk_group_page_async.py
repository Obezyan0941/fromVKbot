import re
import urllib.parse
import vk_audio_extractor
import vk_video_extract
import asyncio
from itertools import compress
from selenium.webdriver import ChromeOptions
from seleniumrequests import Chrome
from bs4 import BeautifulSoup

# get_post is the main function for scraping the web-page of one VK group.
# It works simply by parsing web page loaded by Selenium and searching strings in html code.
# For each element of a wall post there are specific functions. Their process is mainly:
#   1. Parsing page with BeautifulSoup
#   2. Searching element with regular expressions


def get_post(driver, group_url, last_post_id):

    def transform_link(source_link):
        transformed_link = source_link.replace('&amp', "")
        transformed_link = transformed_link.replace(';', "&")
        return transformed_link

    url = group_url

    driver.get(url)

    try:    # try in case of some error during page loading. Being solved automatically during next scraping run.
        soup = BeautifulSoup(driver.page_source, "html.parser")
        post_contents = soup.find_all('div', {'class': 'wall_text'})
        wall_posts_found = len(post_contents)
        print("wall_posts_found: ", wall_posts_found)

        page_name_class = soup.find('h1', {'class': 'page_name'})
        group_name = re.findall("\"page_name\">.*?<", str(page_name_class))
        group_name = re.sub("\"page_name\">", "", group_name[0])[:-1]

        post_init_ind = 0
        pinned = soup.find('span', {'class': 'PostHeaderTitle__pin'})

        def get_post_id(post_html):
            id_raw = re.search("id=\"wpt-\d*?_\d*?\">", str(post_html)).group()
            post_id = re.sub("id=\"wpt|\">", "", id_raw)
            return post_id

        post_id_found = []
        for post_content in post_contents:
            post_id_found.append(get_post_id(post_content))

        if pinned:
            post_id_found = post_id_found[1:]
            post_contents = post_contents[1:]

        print(post_id_found)
        print(last_post_id)
        post_ind_list = []
        if last_post_id != 0:
            for post_id in post_id_found:
                if last_post_id == post_id:
                    break
                post_ind_list.append(post_init_ind)
                post_init_ind += 1
        else:
            post_ind_list = [post_init_ind]
        print(post_ind_list)
        if not post_ind_list:
            return False
    except Exception as e:
        print(f"ERROR in group {group_url}\nPost: {url}?w=wall{last_post_id}\nError: {e}")
        with open(f"error_logs\error_log_last_post_{last_post_id}.txt", "w") as f:
            f.write(f"ERROR in group {group_url}\nPost: {url}?w=wall{last_post_id}\nError: {e}")
        f.close()
        return False

    async def get_copy_quote(post_content):
        copy_quote_post = post_content.find_all("div", {"class": "copy_quote"})
        is_forward_post = False
        copy_author = ""
        copy_post_id = ""
        if copy_quote_post:
            is_forward_post = True
            print("Forwared post")
            copy_author = copy_quote_post[0].find_all("a", {"class": "copy_author"})
            copy_author = re.findall('">.*?</a>', str(copy_author[0]))
            copy_author = re.sub('"|>|<|/|a>', "", copy_author[0])
            print("copy_author: ", copy_author)
            copy_post_id = copy_quote_post[0].find_all("a", {"class": "copy_post_image"})
            copy_post_id = re.findall('data-post-id=".*?"', str(copy_post_id[0]))
            copy_post_id = re.sub('data-post-id="|"', "", copy_post_id[0])
            print("copy_post_id: ", copy_post_id)
        return is_forward_post, copy_author, copy_post_id

    def remove_html_tags(text):
        soup = BeautifulSoup(text, "html.parser")
        clean_text = soup.get_text("\n", strip=True)
        return clean_text

    def text_cutting(restriction_len, base_str):
        import math
        division_len = restriction_len - 3
        text_divisions = math.ceil(len(base_str) / restriction_len)
        end_str_list = []
        for i in range(text_divisions):
            str_part = base_str[i * division_len:division_len * (i + 1)]
            if i != text_divisions - 1:
                str_part += "..."
            end_str_list.append(str_part)
        return end_str_list[0], end_str_list[1:]

    async def get_post_text(post_content):
        temp = []
        message_len_restriction = 900
        post_text = ""
        end_text_list = []

        post_text_found = post_content.find_all("div", {"class": "wall_post_text"})
        is_post_text = False
        if post_text_found:
            is_post_text = True
            post_text = remove_html_tags(str(post_text_found[0]))
            post_text = post_text.replace('Показать ещё\n', "")
        else:
            print("No text")

        post_poll_found = post_content.find_all("div", {"class": "media_voting_header"})
        if post_poll_found:
            is_post_text = True
            post_text += "\n\n<i>К посту добавлен опрос</i>"

        if len(post_text) > message_len_restriction:
            post_text, end_text_list = text_cutting(message_len_restriction, post_text)
        print(post_text)

        return post_text, is_post_text, end_text_list

    async def get_post_pics(post_content):
        is_one_img = False
        is_many_img = False
        post_img_link_list = []

        post_img_found = post_content.find_all("div", {"class": "PhotoPrimaryAttachment"})
        img_attachments = len(post_img_found)
        if post_img_found:
            is_one_img = True
            if img_attachments > 1:
                is_many_img = True
                is_one_img = False
            print("Photo attachments: ", img_attachments)
            for img_num in range(img_attachments):
                post_img_link = re.findall("https:.*?type=album", str(post_img_found[img_num]))
                post_img_link = transform_link(post_img_link[1])
                post_img_link_list.append(post_img_link)
                print(post_img_link)
            return post_img_link_list, is_one_img, is_many_img

        MediaGrid_found = post_content.find_all("img", {"class": "MediaGrid__imageElement"})
        if MediaGrid_found:
            is_one_img = True
            MediaGrid_len = len(MediaGrid_found)
            if MediaGrid_len > 1:
                is_many_img = True
                is_one_img = False
            print("MediaGrid attachments: ", MediaGrid_len)
            for grid_num in range(MediaGrid_len):
                post_mediagrid_link = transform_link(
                    re.findall("https:.*?type=album", str(MediaGrid_found[grid_num]))[0])
                post_img_link_list.append(post_mediagrid_link)
                print(post_mediagrid_link)
        else:
            print("No img")
        return post_img_link_list, is_one_img, is_many_img

    async def get_post_snippet_link(post_content):
        post_snippet_link = ""
        is_post_snippet_link = False
        post_snippet_link_found = post_content.find_all("div", {
            "class": "LinkSnippetPrimaryAttachmentReactBlock__root PrimaryAttachmentReactBlock PrimaryAttachmentReactBlock--withRatio PrimaryAttachmentReactBlock--wide"})
        snippet_link_attachments = len(post_snippet_link_found)
        print("Snippet link attachments: ", snippet_link_attachments)
        if post_snippet_link_found:
            post_snippet_link = re.findall("href=\".*?\"", str(post_snippet_link_found[0]))
            post_snippet_link = re.sub(".*?to=", "", post_snippet_link[0])
            post_snippet_link = post_snippet_link.replace("\"", "")
            post_snippet_link = urllib.parse.unquote(post_snippet_link)
            print(post_snippet_link)
            is_post_snippet_link = True
        else:
            print("No snippet links")
        return post_snippet_link, is_post_snippet_link

    async def get_post_gif(post_content):
        post_gif_direct_url = ""
        is_file_attached = False
        post_gif_found = post_content.find_all("div", {"class": "page_gif_actions"})
        if post_gif_found:
            is_file_attached = True
            post_gif_id = re.findall("Page.shareGif.*?\)\"", str(post_gif_found[0]))
            post_gif_id = re.sub("Page.shareGif\(", "", post_gif_id[0])
            post_gif_id = re.sub("\)\"", "", post_gif_id)
            post_gif_id = post_gif_id.replace("\'", "")
            post_gif_id = tuple(map(str, post_gif_id.split(', ')))
            post_gif_inner_link = 'https://vk.com/doc' + post_gif_id[1] + '?hash=' + post_gif_id[2]
            driver.get(post_gif_inner_link)
            post_gif_direct_url = re.findall("type=\"hidden\" value=\"https.*?\"", str(driver.page_source))
            post_gif_direct_url = re.sub('type=\"hidden\" value=\"', "", post_gif_direct_url[0])[:-1]
            print(post_gif_direct_url)
        else:
            print("No gif found")
        return post_gif_direct_url, is_file_attached

    async def get_audio_files(post_content):
        audio_files = []
        is_file_attached = False
        post_audio_found = post_content.find_all("div", {
            "class": "SecondaryAttachment js-SecondaryAttachment SecondaryAttachment--interactive"})
        post_audio_module_found = post_content.find_all("div", {
            "class": "PrimaryAttachmentAudio-module__container--wF6BS PrimaryAttachmentAudio-module__withSvgBlur--_5qI_"})
        if post_audio_found or post_audio_module_found:
            print("Audio found")
            audio_files = vk_audio_extractor.get_audio(wall_id)
            print(wall_id)
            print(audio_files)
            is_file_attached = True
        else:
            print("No audio")
        return audio_files, is_file_attached

    async def get_post_video(post_content_str, post_content):
        # return False, False, False, False
        video_args = []
        is_file_attached = False
        post_snippet_link = ""
        is_post_snippet_link = False
        if "data-video" in post_content_str:
            print("Video found")
            video_thumb_label_item = post_content.find_all("span", {"class": "video_thumb_label_item"})[
                0]
            video_thumb_label_item = re.search('">.*?</span>', str(video_thumb_label_item)).group()
            video_thumb_label_item = re.sub('">|</span>', "", video_thumb_label_item)
            vk_video_id = re.search('data-video=".*?"', post_content_str).group()
            vk_video_id = re.sub('data-video="|"', "", vk_video_id)
            vk_video_url = 'https://vk.com/video' + vk_video_id
            print(vk_video_url)
            print(vk_video_id)
            if video_thumb_label_item == 'YouTube':
                print("From YouTube")
                driver.get(vk_video_url)
                video_page_str = str(driver.page_source)
                video_url = re.search('href="http://www.youtube.*?">', video_page_str).group()
                video_url = re.sub('href="|">', "", video_url)
                post_snippet_link = video_url
                is_post_snippet_link = True
                print(post_snippet_link)
            elif not video_thumb_label_item:
                print("VK video")
                video_args = vk_video_extract.get_video(vk_video_url, vk_video_id)
                is_file_attached = True
        return video_args, is_file_attached, post_snippet_link, is_post_snippet_link

    # all processes are handled asynchronously which helped by cutting scraping time by roughly 40%
    async def process_post_content(post_ind_local, post_contents_local, post_contents_i_str_local):
        async_tasks = [
            get_copy_quote(post_contents_local[post_ind_local]),
            get_post_text(post_contents_local[post_ind_local]),
            get_post_pics(post_contents_local[post_ind_local]),
            get_post_snippet_link(post_contents_local[post_ind_local]),
            get_post_gif(post_contents_local[post_ind_local]),
            get_audio_files(post_contents_local[post_ind_local]),
            get_post_video(post_contents_i_str_local, post_contents_local[post_ind_local]),
        ]

        results_args = await asyncio.gather(*async_tasks)

        return results_args

    group_posts = []
    for post_ind in post_ind_list:
        wall_id = post_id_found[post_ind]
        try:
            post_contents_i_str = str(post_contents[post_ind])
            post_header_link = 'https://vk.com/wall' + wall_id
            results_list = asyncio.run(process_post_content(post_ind, post_contents, post_contents_i_str))

            #   All results are put inside a dictionary for better and easier scaling of a project. It helped.
            results_dict = {'group_name': group_name, 'group_url': group_url, 'wall_id': wall_id,
                            'is_forward_post': results_list[0][0], 'copy_author': results_list[0][1],
                            'copy_post_id': results_list[0][2], 'post_text': results_list[1][0],
                            'is_post_text': results_list[1][1],  'end_text_list': results_list[1][2],
                            'post_img_link_list': results_list[2][0],
                            'post_snippet_link_any': results_list[3][0], 'is_post_snippet_link_any': results_list[3][1],
                            'post_gif_direct_url': results_list[4][0], 'is_gif_file_attached': results_list[4][1],
                            'audio_files': results_list[5][0], 'is_audio_file_attached': results_list[5][1],
                            'video_args': results_list[6][0], 'is_video_file_attached': results_list[6][1],
                            'post_snippet_link_video': results_list[6][2],
                            'is_post_snippet_link_video': results_list[6][3], 'is_file_attached': False,
                            'post_url': post_header_link}

            if (results_dict['is_gif_file_attached']
                    or results_dict['is_audio_file_attached']
                    or results_dict['is_video_file_attached']):
                results_dict['is_file_attached'] = True

            # Fancy way of handling booleans instead of nested if else statements
            is_one_img, is_many_img, is_gif = results_list[2][1], results_list[2][2], results_list[4][1]
            post_mode = tuple(compress(("one_image", "many_images", "_gif"),
                                       (is_one_img, is_many_img, is_gif)))
            if not post_mode:
                post_mode = "text_only"
            else:
                post_mode = post_mode[0]

            print(f"post_mode: {post_mode:>20}")
            results_dict['post_mode'] = post_mode

            # Fancy way of handling booleans instead of nested if else statements
            results_dict['post_snippet_link'] = tuple(compress((results_dict['post_snippet_link_any'],
                                                results_dict['post_snippet_link_video']),
                                               (results_dict['is_post_snippet_link_any'],
                                                results_dict['is_post_snippet_link_video'])))

            results_dict['is_post_snippet_link'] = False
            if results_dict['post_snippet_link']:
                results_dict['is_post_snippet_link'] = True
                results_dict['post_snippet_link'] = results_dict['post_snippet_link'][0]

            group_posts.append(results_dict)
        except Exception as e:
            print(f"ERROR in group {group_url}, post: {wall_id},\nError: {e}")
            with open(f"error_logs\error_log_{wall_id}.txt", "w") as f:
                f.write(f"ERROR in group {group_url}\nPost: {url}?w=wall{last_post_id}\nError: {e}")
            f.close()
            continue

    print(group_posts)
    return group_posts


if __name__ == "__main__":
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")    # it did not help much with loading time
    options.add_argument("--disable-javascript")    # it did not help much with loading time
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
        "Safari/537.36")

    driver = Chrome(options=options)

    group_id = 'https://vk.com/group_name'  # sample group URL
    last_post_id = '-000000000_00000'   # sample last post ID
    get_post(driver, group_id, last_post_id)
