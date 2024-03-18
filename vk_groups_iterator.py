import pymongo
import vk_group_page_async
import time
import datetime
from selenium.webdriver import ChromeOptions
from seleniumrequests import Chrome


def iterate_through_all_groups():
    options = ChromeOptions()
    options.add_argument("--headless")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 "
        "Safari/537.36")
    options.add_argument("log-level=3")
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-javascript")
    driver = Chrome(options=options)

    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")
    fromvk_db = mongo_client["fromvk_db"]
    groups_data = fromvk_db["groups_data"]  # all groups from all users
    users_data = fromvk_db["users_data"]  # collection of users with their groups
    data_collected = fromvk_db["data_collected"]  # time and posts count during scraping
    user_posts = fromvk_db["user_posts"]  # collection of users with data of wall posts to send

    # get all groups
    all_groups = tuple(groups_data.find({}, {'_id': 0, 'group_URL': 1, 'last_post_ind': 1, "posts_data": 1}))

    time_elapsed_list = []
    for group_info in all_groups:
        print(group_info)
        group_url = group_info["group_URL"]
        time_start = time.perf_counter()
        last_post_ind = group_info["last_post_ind"]
        # scrape one group
        parsed_data = vk_group_page_async.get_post(driver=driver,
                                                   group_url=group_url,
                                                   last_post_id=last_post_ind)

        print(parsed_data)
        time_end = time.perf_counter()
        time_elapsed = time_end - time_start
        print(f"Time elapsed asynchronous: {time_elapsed}")
        if parsed_data:
            print("inserted")
            groups_data.update_one({"group_URL": group_url}, {"$set": {"last_post_ind": parsed_data[0]['wall_id'],
                                                                       "posts_data": parsed_data[::-1]}})
            data_collected.insert_one({"posts_num": len(parsed_data),
                                       "time_elapsed": time_elapsed,
                                       "date": datetime.datetime.now(tz=datetime.timezone.utc)})
        else:  # error log
            groups_data.update_one({"group_URL": group_url}, {"$set": {"posts_data": False}})
            data_collected.insert_one({"posts_num": 0,
                                       "time_elapsed": time_elapsed,
                                       "date": datetime.datetime.now(tz=datetime.timezone.utc)})
        time_elapsed_list.append(time_elapsed)

    print(f"Time elapsed max: {max(time_elapsed_list)},\nTime elapsed min: {min(time_elapsed_list)}")

    # Pipeline for creating data to send to user_posts, where bot would then take that data
    # and send messages with it immediately.
    result = tuple(users_data.aggregate([
        {
            '$unwind': '$User_groups'
        },
        {
            '$lookup': {
                'from': 'groups_data',
                'localField': 'User_groups',
                'foreignField': 'group_URL',
                'as': 'post_data_to_send'
            }
        },
        {
            '$project': {
                'post_data_to_send': '$post_data_to_send.posts_data'
            }
        },
        {
            '$unwind': '$post_data_to_send'
        },
        {
            '$group': {
                '_id': '$_id',
                'post_data_to_send': {'$push': '$post_data_to_send'}
            }
        }
    ]))

    user_posts.drop()
    user_posts.insert_many(result)


if __name__ == "__main__":
    iterate_through_all_groups()
