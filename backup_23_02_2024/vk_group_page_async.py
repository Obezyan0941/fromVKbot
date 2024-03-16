import re
import urllib.parse
import vk_audio_extractor
import vk_video_extract
import pymongo
import asyncio
from itertools import compress
from selenium.webdriver import ChromeOptions
from seleniumrequests import Chrome
from bs4 import BeautifulSoup


def get_post(driver, group_url, last_post_id):
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

    test_fromvk_db = mongo_client["fromvk_db"]
    users_data = test_fromvk_db["users_data"]

    def transform_link(source_link):
        transformed_link = source_link.replace('&amp', "")
        transformed_link = transformed_link.replace(';', "&")
        return transformed_link

    # url = 'https://vk.com/' + group_id
    url = group_url

    driver.get(url)
    # print(driver.page_source)

    try:
        soup = BeautifulSoup(driver.page_source, "html.parser")
        # public_wall = soup.find('div', {'id': 'public_wall'})
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
            # post_init_ind += 1
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
    except:
        print(f"ERROR in group {group_url}")
        with open(f"error_log_last_post_{last_post_id}.txt", "w") as f:
            f.write(f"ERROR in group {group_url}, last post: {last_post_id}")
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
        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(text, "html.parser")
        # Получаем текст без HTML-тегов
        clean_text = soup.get_text("\n", strip=True)
        return clean_text


    async def get_post_text(post_content):
        post_text = ""
        post_text_found = post_content.find_all("div", {"class": "wall_post_text"})
        is_post_text = False
        if post_text_found:
            # clean_text = remove_html_tags(str(post_text_found[0]))
            # print(clean_text)
            is_post_text = True
            post_text = re.sub(r'<div class="wall_post_text">', "", str(post_text_found[0]))
            post_text = re.sub(r'</div>', "", post_text)
            if "<br/>" in post_text:
                post_text = re.sub("<br/>", "\n", post_text)
            if "<img alt=" in post_text:
                emoji_found = re.findall('<img alt=.*?>', post_text)
                for num, emoji in enumerate(emoji_found):
                    emoji = emoji[10:11]
                    post_text = post_text.replace(emoji_found[num], emoji)
            if "<a href=\"/feed" in post_text:
                hashtag_patterns = re.findall('<a href="/feed\?section=.*?">#.*?</a>', post_text)
                # print(f"hashtag_patterns {hashtag_patterns}")
                for pattern in hashtag_patterns:
                    hashtag = "#" + re.sub('<a href="/feed\?section=.*?">#', "", pattern)[0:-4]
                    post_text = post_text.replace(pattern, hashtag)
                post_text = post_text.replace("</span>", "")
            if "<button class=\"PostTextMore\"" in post_text:
                button_pattern = re.findall('<button class=\"PostTextMore\".*?style="display: none">', post_text)
                if button_pattern:
                    post_text = post_text.replace(button_pattern[0], "")
            if "<a href=\"/away" in post_text:
                link_patterns = re.findall('<a href=\"/away\.php\?.*?</a>', post_text)
                # print(f"link_patterns {link_patterns}")
                for link_pattern in link_patterns:
                    link = re.sub('<a href=\"/away\.php\?.*?\"_blank\">', "", link_pattern)[0:-4]
                    # print(f"link {link}")
                    post_text = post_text.replace(link_pattern, link)
# ERROR in group https://vk.com/real_wonderland, post: -222499729_2526
            print(post_text)
        else:
            print("No text")
        return post_text, is_post_text

    async def get_post_pics(post_content):
        post_img_found = post_content.find_all("div", {"class": "PhotoPrimaryAttachment"})
        img_attachments = len(post_img_found)
        print("Photo attachments: ", img_attachments)
        post_img_link_list = []
        if post_img_found:
            for img_num in range(img_attachments):
                post_img_link = re.findall("https:.*?type=album", str(post_img_found[img_num]))
                post_img_link = transform_link(post_img_link[1])
                post_img_link_list.append(post_img_link)
                print(post_img_link)
        else:
            MediaGrid_found = post_content.find_all("img", {"class": "MediaGrid__imageElement"})
            MediaGrid_len = len(MediaGrid_found)
            print("MediaGrid attachments: ", MediaGrid_len)
            for grid_num in range(MediaGrid_len):
                post_mediagrid_link = transform_link(
                    re.findall("https:.*?type=album", str(MediaGrid_found[grid_num]))[0])
                post_img_link_list.append(post_mediagrid_link)
                print(post_mediagrid_link)
        if not post_img_link_list:
            print("No img")
        return post_img_link_list

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
            # print(post_gif_id)
            post_gif_inner_link = 'https://vk.com/doc' + post_gif_id[1] + '?hash=' + post_gif_id[2]
            # print(post_gif_inner_link)
            driver.get(post_gif_inner_link)
            post_gif_direct_url = re.findall("type=\"hidden\" value=\"https.*?\"", str(driver.page_source))
            post_gif_direct_url = re.sub('type=\"hidden\" value=\"', "", post_gif_direct_url[0])[:-1]
            print(post_gif_direct_url)
            # https://vk.com/doc592638807_671379248?hash=IXIJypLfo3geN5w0tCZTA0dMlC9BpYzpzS4OrzKG7rT
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
            # post_header_link, wall_id = get_post_header(post_contents_i_str)
            post_header_link = 'https://vk.com/wall' + wall_id
            results_list = asyncio.run(process_post_content(post_ind, post_contents, post_contents_i_str))

            is_forward_post, copy_author, copy_post_id = results_list[0]
            post_text, is_post_text = results_list[1]
            post_img_link_list = results_list[2]
            post_snippet_link_any, is_post_snippet_link_any = results_list[3]
            # post_header_link, wall_id = results_list[4]
            post_gif_direct_url, is_gif_file_attached = results_list[4]
            audio_files, is_audio_file_attached = results_list[5]
            video_args, is_video_file_attached, post_snippet_link_video, is_post_snippet_link_video = results_list[6]

            is_file_attached = False
            if is_gif_file_attached or is_audio_file_attached or is_video_file_attached:
                is_file_attached = True

            post_snippet_link = tuple(compress((post_snippet_link_any, post_snippet_link_video),
                                               (is_post_snippet_link_any, is_post_snippet_link_video)))

            is_post_snippet_link = False
            if post_snippet_link:
                is_post_snippet_link = True
                post_snippet_link = post_snippet_link[0]

            group_posts.append(((True, is_forward_post, is_post_text, is_post_snippet_link, True, is_file_attached),
                                group_name,
                                group_url,
                                wall_id,
                                copy_author,
                                copy_post_id,
                                post_text,
                                post_img_link_list,
                                post_snippet_link,
                                post_header_link,
                                post_gif_direct_url,
                                audio_files,
                                video_args))
        except:
            print(f"ERROR in group {group_url}, post: {wall_id}")
            with open(f"error_log_{wall_id}.txt", "w") as f:
                f.write(f"ERROR in group {group_url}, post: {wall_id}")
            f.close()
            continue

    print(group_posts)
    return group_posts


if __name__ == "__main__":
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-javascript")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
        "Safari/537.36")

    driver = Chrome(options=options)

    # group_id = "meme_kafe"
    # group_id = "doctorlivesey228"
    group_id = "https://vk.com/kpru"
    # group_id = 'club224244506'
    # group_id = 'https://vk.com/real_wonderland'
    # last_post_id = '-224244506_6'
    last_post_id = -15722194_8464212
    # last_post_id = '-222499729_2526'
    get_post(driver, group_id, last_post_id)
