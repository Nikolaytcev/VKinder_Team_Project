# -*- coding: utf-8 -*-

from VK_interaction.bot import VKinderBot
from VKinder_db.db import connect_to_db

import configparser


def read_config(*path):
    config = configparser.ConfigParser()
    config.read("settings.ini")
    value = config.get(*path)
    return value


def main():
    db = connect_to_db('vkinder_db')
    bot_token = read_config('vk_tokens', 'bot_token')
    vk_token = read_config('vk_tokens', 'user_token')
    group_id = read_config('vk_group', 'id')
    VKinderBot(bot_token, group_id, vk_token, db).listen_longpoll()


if __name__ == "__main__":
    main()
