# fromVKbot
Telegram bot for sending wall posts from VK

The bot manages every user's chousen groups through a MongoDB database. Once in 45 minutes bot searches for new wall posts in VK groups, scrapes wall posts's data and sends it as telegram messages to respective users.

Scripts of this project:
1. from_vk_bot - main script for running the bot. Contains all Telebot functions and reads data from database to send messages.
2. vk_group_page_async - script for scraping one group page asynchorously (AsyncIO)
3. vk_groups_iterator - script that contains some MongoDB pipelines for getting all users' groups, running vk_group_page_async script and storeing new data in database
4. vk_video_extract - script for downloading wall post's video
5. vk_audio_extractor - script for downloading wall post's audio

All key codes are changed for security purposes. 
