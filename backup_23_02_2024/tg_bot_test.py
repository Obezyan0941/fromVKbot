import telebot
import vk_group_page_parser
import pymongo
import json
from itertools import compress
from telebot import types
from selenium.webdriver import ChromeOptions
from seleniumrequests import Chrome

bot = telebot.TeleBot('6436918457:AAHQpL1ratkw72bjheXHFtmgENZIqEcSqGc')

options = ChromeOptions()
options.add_argument("--headless")
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
    "Safari/537.36")
driver = Chrome(options=options)

hyperlink_text = "image link"
post_url_text = "Ссылка на пост"

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
fromvk_db = mongo_client["fromvk_db"]
users_data = fromvk_db["users_data"]


# bot.send_audio(549648552, audio=open(r"C:\Users\gamer\Downloads\rZp5L67_P3JJOvU6NC9w_lvQMFBhU-aGF3kf_DACHKcHbXY-lI7rFKqAHEGWsN2-CeCu3Q3XcsRkhT1Pw9GHCxzOzz-UdEs_XPE_cOprtQo_WeGlz8KbPDE4ITn4CrIE2oqI3KHMikhiiummd7w2oh-S8kUto-KO3OAJnkTHo7pVc_TCcf7B.mp3", 'rb'))
# test_audio_url = 'https://cs9-16v4.vkuseraudio.net/s/v1/acmp/rZp5L67_P3JJOvU6NC9w_lvQMFBhU-aGF3kf_DACHKcHbXY-lI7rFKqAHEGWsN2-CeCu3Q3XcsRkhT1Pw9GHCxzOzz-UdEs_XPE_cOprtQo_WeGlz8KbPDE4ITn4CrIE2oqI3KHMikhiiummd7w2oh-S8kUto-KO3OAJnkTHo7pVc_TCcf7B.mp3'
# test_audio_url = 'https://cs9-11v4.vkuseraudio.net/s/v1/acmp/jEAmpes3A9jrQoBvG4HBorasmiuzFLX-0cHzndEGNaACp1ir0LZ-xj3ibPWboL9XfmeuNa2NfP60m1iq6yAso9dFA3nRY4Qrj388ToJD5-DhchQP-Yvi6MF01N5hfZ2F59dzwohF2QWinNttFFn04bMbwmv4Y3KBXJHrIQj1VK_25_vqibtc.mp3'
# print(test_audio_url)
# test_media = [types.InputMediaAudio(test_audio_url, caption="filename")]
# bot.send_media_group(549648552, test_media)
# quit()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🇷🇺 Русский")
    btn2 = types.KeyboardButton('🇬🇧 English')
    markup.add(btn1, btn2)
    bot.send_message(message.from_user.id, "🇷🇺 Выберите язык / 🇬🇧 Choose your language", reply_markup=markup)


print('Online.')


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    # print(message.from_user.id)
    # bot.send_video(chat_id=message.from_user.id,
    #                video=open(r'temp_videos/-224244506_456239017_[128435719.98832417].mp4', 'rb'),
    #                caption="post_video_args[2]", supports_streaming=True)

    # test_audio_url = 'https://cs9-11v4.vkuseraudio.net/s/v1/acmp/jEAmpes3A9jrQoBvG4HBorasmiuzFLX-0cHzndEGNaACp1ir0LZ-xj3ibPWboL9XfmeuNa2NfP60m1iq6yAso9dFA3nRY4Qrj388ToJD5-DhchQP-Yvi6MF01N5hfZ2F59dzwohF2QWinNttFFn04bMbwmv4Y3KBXJHrIQj1VK_25_vqibtc.mp3'
    # test_media = [types.InputMediaAudio(test_audio_url, caption="filename")]
    # bot.send_media_group(message.from_user.id, test_media)
    # test_url = r"https://sun9-33.userapi.com/c828603/u238248823/docs/d3/4a52b2ac5075/video.mp4?extra=8QgNnVy93cBLFWC81b4jTrQjk7tH-nJ_dYRgx-ANmfhEIRP59g8AwPTcnEuZLQjHjNGSkkCp4vrWunBSuAMK1slwd1RuQqT_6BXQbsOYlO8yJu69gt-Lkkc1FBPrJynYoF3fdUjP-uUyKtXGwBLOg-1F9dY"
    # test_media = [types.InputMediaVideo(test_url)]
    # print(test_media)
    # bot.send_media_group(message.from_user.id, test_media)
    # response = requests.get(test_url)
    # video_data = BytesIO(response.content)
    # bot.send_video(message.chat.id, video_data)

    markup = types.ReplyKeyboardRemove()
    if message.text == '🇷🇺 Русский':
        bot.send_message(message.from_user.id, '❓ Задайте интересующий вопрос', reply_markup=markup)
    else:
        try:
            (post_text_bool,
             group_name,
             post_id,
             forwarded_author,
             forwarded_post_id,
             post_text,
             img_url_list,
             snippet_link,
             post_url,
             post_gif_url,
             post_audio_json,
             post_video_args) = vk_group_page_parser.get_post(driver, message.text)

            post_str_list = [
                "<b>" + group_name + "</b>",
                "<b>Репост из " + forwarded_author + "</b>",
                post_text,
                snippet_link,
                "<a href='" + post_url + "'>" + post_url_text + "</a>",
                "Вложенные файлы⬇️"
            ]

            post_text_list = list(compress(post_str_list, post_text_bool))
            result_text_list = ['\n\n'] * (len(post_text_list) * 2 - 1)
            result_text_list[0::2] = post_text_list
            default_caption = ''.join(result_text_list)

            # default_caption = ("<b>" + group_name + '</b>\n\n' + post_text + '\n\n' + snippet_link + '\n\n'
            #                    + "<a href='" + post_url + "'>" + post_url_text + "</a>")
            img_url_list_len = len(img_url_list)
            if img_url_list_len == 0:
                if post_gif_url:
                    media = [types.InputMediaVideo(post_gif_url)]
                    bot.send_message(message.from_user.id, default_caption, parse_mode='HTML', reply_markup=markup)
                    bot.send_media_group(message.from_user.id, media)
                else:
                    bot.send_message(message.from_user.id, default_caption, parse_mode='HTML', reply_markup=markup)
            elif img_url_list_len == 1:
                bot.send_photo(message.from_user.id, img_url_list[0], default_caption, reply_markup=markup,
                               parse_mode='HTML')
            else:
                media = [types.InputMediaPhoto(url) for url in img_url_list]
                media[0] = types.InputMediaPhoto(img_url_list[0], caption=default_caption, parse_mode='HTML')
                bot.send_media_group(message.from_user.id, media=media)
            if post_audio_json:
                try:
                    print("______________________________")
                    print("Audio exists.")
                    for audio_dict in post_audio_json:
                        print(audio_dict['url'])
                        test_media = [types.InputMediaAudio(audio_dict['url'],
                                                            caption=audio_dict['artist'] + " - " + audio_dict['title'])]
                        bot.send_media_group(message.from_user.id, test_media)
                except:
                    bot.send_message(message.from_user.id,
                                     "\nК посту прикреплено аудио больше 5 мб, в данной версии отправить невозможно",
                                     parse_mode='HTML', reply_markup=markup)
            if post_video_args:
                if post_video_args[0]:
                    bot.send_video(chat_id=message.from_user.id,
                                   video=open(post_video_args[1], 'rb'),
                                   caption=post_video_args[2])
                else:
                    bot.send_message(message.from_user.id,
                                     "\nК посту прикреплено видео длиннее 30 минут. Получайте видео без ограничений с"
                                     " премиум подпиской", parse_mode='HTML', reply_markup=markup)

            one_user_data = {'_id': message.from_user.id,
                             'User_groups': [message.text],
                             'User_groups_last_post_id': [1]}

            users_data.insert_one(one_user_data)

        except:
            bot.send_message(message.from_user.id, 'Ошибка', reply_markup=markup)


bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть

# meme_kafe
