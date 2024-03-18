import time
import telebot
import pymongo
import re
import threading
import vk_groups_iterator
import os
from telebot.types import ReplyKeyboardRemove
from itertools import compress
from telebot import types
from telebot.apihelper import ApiTelegramException

bot = telebot.TeleBot('telebot_id_number')

hyperlink_text = "image link"
post_url_text = "Ссылка на пост"

mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
fromvk_db = mongo_client["fromvk_db"]
users_data = fromvk_db["users_data"]
groups_data = fromvk_db["groups_data"]
user_posts = fromvk_db["user_posts"]


@bot.message_handler(commands=['start'])
def start(message):   # Bot starting function
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.from_user.id,
                     "Добро пожаловать в FromVK bot!\n\n"
                     "Бот будет присылать посты из выбранных вами групп прмиерно раз в час.\n\n"
                     "Основные команды для управления:\n\n"
                     "/help - Напомнит все доступные команды\n\n"
                     "/add - Добавить группу к вашему списку\n\n"
                     "/delete - Убрать группу из вашего списка\n\n"
                     "Максимально доступное количество групп на одного пользователя: 4.",
                     reply_markup=markup)


@bot.message_handler(commands=['help'])
def help_command(message):     # help command that shows all possible commands
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.from_user.id,
                     "Основные команды для управления:\n\n\n"
                     "/help - Напомнит все доступные команды\n\n"
                     "/add - Добавить группу к вашему списку\n\n"
                     "/delete - Убрать группу из вашего списка\n\n"
                     "Максимально доступное количество групп на одного пользователя: 4.",
                     reply_markup=markup)


def group_pull(group_url):      # def for deleting groups from database
    users_using = groups_data.find_one({'group_URL': group_url}, {"_id": 0, "users_using": 1})[
        'users_using']
    if users_using <= 1:
        groups_data.delete_one({'group_URL': group_url})
    else:
        groups_data.update_one({"group_URL": group_url}, {"$inc": {'users_using': -1}})


@bot.message_handler(commands=['add'])
def add_group(message):     # def that handles addition of a new group for a user
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Выйти")
    markup.add(btn1)

    def handle_add(message):
        inserted_url = message.text
        if message.text == "Выйти":
            bot.send_message(message.from_user.id, "Изменения отменены", reply_markup=ReplyKeyboardRemove())
            return None
        pattern = re.findall('vk\..*?/.*?', inserted_url)
        if not pattern:
            print(inserted_url, pattern)
            bot.send_message(message.from_user.id, "Неверный URL", reply_markup=ReplyKeyboardRemove())
            return None
        users_ids = users_data.distinct("_id")
        if message.from_user.id in users_ids:
            users_group_list = users_data.find_one({'_id': message.from_user.id},
                                                   {"_id": 0, "User_groups": 1})['User_groups']
            if len(users_group_list) >= 4:
                bot.send_message(message.from_user.id, "Достигнут лимт групп", reply_markup=ReplyKeyboardRemove())
                return None
            elif inserted_url in users_group_list:
                bot.send_message(message.from_user.id, "Такая группа уже добавлена", reply_markup=ReplyKeyboardRemove())
                return None
            else:
                update_query = {"$push": {"User_groups": inserted_url}}
                users_data.update_one({"_id": message.from_user.id}, update_query)
        else:
            one_user_data = {'_id': message.from_user.id,
                             'User_groups': [inserted_url]}
            users_data.insert_one(one_user_data)
        groups_unique = groups_data.distinct("group_URL")
        if inserted_url not in groups_unique:
            groups_data.insert_one({"group_URL": inserted_url, "last_post_ind": 0, 'users_using': 1})
        else:
            groups_data.update_one({"group_URL": inserted_url}, {"$inc": {'users_using': 1}})
        bot.send_message(message.from_user.id, f"Группа {inserted_url} была добавлена к вашей лентe",
                         reply_markup=ReplyKeyboardRemove())

    bot.send_message(message.from_user.id, "Введите URL группы, которую хотите добавить.\n\n"
                                           "URL группы должен выглядить так: https://vk.com/group_name\n\n"
                                           "Получить его можно скопировав ссылку группы из ВКонтакте.",
                     reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_add)


@bot.message_handler(commands=['delete'])
def delete_group(message):      # def that handles deletion of a group for a user
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Выйти")
    markup.add(btn1)

    def handle_delete(message):
        inserted_url = message.text

        users_ids = users_data.distinct("_id")
        if message.from_user.id not in users_ids:
            bot.send_message(message.from_user.id, "У вас нет групп", reply_markup=ReplyKeyboardRemove())
            return None

        if message.text == "Выйти":
            bot.send_message(message.from_user.id, "Изменения отменены", reply_markup=ReplyKeyboardRemove())
            return None
        if inserted_url in users_group_list:
            update_query = {"$pull": {"User_groups": inserted_url}}
            users_data.update_one({"_id": message.from_user.id}, update_query)
            bot.send_message(message.from_user.id, f"Группа {inserted_url} была убрана из вашей ленты",
                             reply_markup=ReplyKeyboardRemove())
            group_pull(inserted_url)
        else:
            bot.send_message(message.from_user.id, "Такой группы нет в вашем списке",
                             reply_markup=ReplyKeyboardRemove())
            return None

    bot.send_message(message.from_user.id, "Введите URL группы, которую хотите убрать", reply_markup=markup)
    users_group_list = users_data.find_one({'_id': message.from_user.id},
                                           {"_id": 0, "User_groups": 1})['User_groups']
    list_text = "\n".join(users_group_list)
    bot.send_message(message.from_user.id, f"Список ваших групп:\n\n{list_text}")
    bot.register_next_step_handler_by_chat_id(message.from_user.id, handle_delete)


def delete_user(user_id):   # deletes a user in case of blocking the bot
    print("User has blocked the bot")

    user_group_list = users_data.find_one({'_id': user_id},
                                          {"_id": 0, "User_groups": 1})['User_groups']

    for user_group in user_group_list:
        group_pull(user_group)
    users_data.delete_one({'_id': user_id})


def send_posts(user_id, post_args, is_test=False):      # function for sending posts
    if is_test:
        user_id = 549648552
    markup = types.ReplyKeyboardRemove()
    post_id = post_args['wall_id']
    try:
        post_text_bool = (True,
                          post_args['is_forward_post'],
                          post_args['is_post_text'],
                          post_args['is_post_snippet_link'],
                          True,
                          post_args['is_file_attached'])
        post_str_list = [
            "<b>" + post_args['group_name'] + "</b>",
            "<b>Репост из " + post_args['copy_author'] + "</b>",
            post_args['post_text'],
            post_args['post_snippet_link'],
            "<a href='" + post_args['post_url'] + "'>" + post_url_text + "</a>",
            "Вложенные файлы⬇️"
        ]

        def send_one_image():
            bot.send_photo(user_id, post_args['post_img_link_list'][0], default_caption, reply_markup=markup,
                           parse_mode='HTML')

        def send_multiple_images():
            media = [types.InputMediaPhoto(url) for url in post_args['post_img_link_list']]
            media[0] = types.InputMediaPhoto(post_args['post_img_link_list'][0], caption=default_caption,
                                             parse_mode='HTML')
            bot.send_media_group(user_id, media=media)

        def send_text_only():
            bot.send_message(user_id, default_caption, parse_mode='HTML', reply_markup=markup)

        def send_with_gif():
            media = [types.InputMediaVideo(post_args['post_gif_direct_url'])]
            bot.send_message(user_id, default_caption, parse_mode='HTML', reply_markup=markup)
            bot.send_media_group(user_id, media)

        post_text_list = list(compress(post_str_list, post_text_bool))
        result_text_list = ['\n\n'] * (len(post_text_list) * 2 - 1)
        result_text_list[0::2] = post_text_list
        default_caption = ''.join(result_text_list)

        def_dict = {"one_image": send_one_image,
                    "many_images": send_multiple_images,
                    "_gif": send_with_gif,
                    "text_only": send_text_only}

        def_dict[post_args['post_mode']]()

        for text_part in post_args['end_text_list']:
            time.sleep(0.2)
            bot.send_message(user_id, "Продолжение поста:\n\n" +
                             text_part + "\n\n" +
                             post_str_list[4], parse_mode='HTML', reply_markup=markup)

        if post_args['audio_files']:
            for audio_dict in post_args['audio_files']:
                if audio_dict['is_file']:
                    bot.send_audio(chat_id=user_id, audio=open(audio_dict['url'], 'rb'),
                                   caption=audio_dict['artist'] + " - " + audio_dict['title'])
                else:
                    test_media = [types.InputMediaAudio(audio_dict['url'],
                                                        caption=audio_dict['artist'] + " - " + audio_dict['title'])]
                    bot.send_media_group(user_id, test_media)

        if post_args['video_args']:
            if post_args['video_args'][0]:
                bot.send_video(chat_id=user_id,
                               video=open(post_args['video_args'][1], 'rb'),
                               caption=post_args['video_args'][2])
            else:
                bot.send_message(user_id,
                                 "\nК посту прикреплено видео длиннее 30 минут. В данной версии передача таких видео"
                                 "невозможна.", parse_mode='HTML', reply_markup=markup)

    except Exception as e:      # error logs
        print(e)
        with open(f"error_logs\error_log_sending{post_id}.txt", "w") as f:
            f.write(str(post_args).replace(',', ',\n')+"\n\n"+str(e))


def handle_user_posts(post_args):
    user_id = post_args['_id']
    for post_data in post_args['post_data_to_send']:
        try:
            if post_data:
                for single_post in post_data:
                    send_posts(user_id, single_post, is_test=False)
                    print(f'Post sent to user \"{user_id}\".')
                    time.sleep(0.1)
        except ApiTelegramException as e:
            if "Forbidden: bot was blocked by the user" in e.description:
                delete_user(user_id)
            else:
                continue


@bot.message_handler(content_types=['text'])
def handle_random_message(message):
    if "key_code" in message.text:   # there is a special key that an Admin can use to contact
        users_ids = users_data.distinct("_id")  # all users through own telegram account
        for user_id in users_ids:
            try:
                bot.send_message(user_id, message.text[20:])
            except ApiTelegramException as e:
                if "Forbidden: bot was blocked by the user" in e.description:
                    delete_user(user_id)
                else:
                    continue
    else:
        bot.send_message(message.from_user.id, 'Я увидел ваше сообщение, но пока ответить не могу.')


print('Online.')


def posts_sender():     # main functions that handles scraping and then sending all posts
    minutes_to_await = 45
    run_sender = True   # just for debug purposes

    while run_sender:
        timer_time = minutes_to_await * 60
        time_left = timer_time

        vk_groups_iterator.iterate_through_all_groups()     # runs script that searches all user groups and scrapes data
        all_user_posts = tuple(user_posts.find())
        for current_user_post in all_user_posts:
            try:
                handle_user_posts(current_user_post)
            except:
                print("ERROR message was not sent. Something went wrong")   # This exception was never raised
                pass

        for tick in range(timer_time):  # Initiating timer to wait for each run of scraping and sending
            time.sleep(1)
            time_left -= 1
            if time_left % 60 == 0:
                print(f"До следующей итерации осталось {time_left/60} минут")


def polling_run():
    bot.polling(non_stop=True, interval=0)  # basic function for a bot to run


def create_folders():
    if not os.path.isdir("temp_videos"):
        os.makedirs("temp_videos")
    if not os.path.isdir("temp_audios"):
        os.makedirs("temp_audios")
    if not os.path.isdir("error_logs"):
        os.makedirs("error_logs")


create_folders()   # folders for saving videos and audios to send and all error logs

# Implementing multithreading for running both basic Telegram bot functions (like handling message responses)
# and working with MongoDB database, scraping VK groups and sending posts
thread1 = threading.Thread(target=posts_sender)
thread2 = threading.Thread(target=polling_run)

thread1.start()
thread2.start()

thread1.join()
thread2.join()
