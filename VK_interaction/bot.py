from VK_interaction.interaction import VkInteraction

from random import randrange
import requests
import json
import emoji
import re


class VKinderBot:
    def __init__(self, bot_token, group_id, vk_token, db):
        self.db = db
        self.vk_interaction = VkInteraction(token=vk_token)
        self.url = 'https://api.vk.com/method/'
        self.group_id = group_id
        self.user_fields = ["country", "city", "bdate", "sex"]
        self.params = {
            'access_token': bot_token,
            'v': '5.85'
        }
        self.ts = 0
        self.candidates = {}
        self.current_candidate = {}

    def connect_vk(self):
        url = self.url + 'groups.getLongPollServer'
        params = {
            **self.params,
            'group_id': self.group_id
        }
        connect = requests.get(url, params).json()
        connect = connect['response']
        self.ts = connect['ts']
        return connect

    def get_longpoll_server(self, connect):
        url = connect['server']
        params = {
            'act': 'a_check',
            'key': connect['key'],
            'wait': 25,
            'mode': 2,
            'ts': self.ts
        }
        response = requests.get(url, params).json()
        if 'ts' in response:
            self.ts = response['ts']
        return response

    def listen_longpoll(self):
        connect = self.connect_vk()
        while True:
            updates = self.get_longpoll_server(connect)
            for update in updates['updates']:
                if update['type'] == 'message_new':
                    user_id = update['object']['message']['from_id']
                    user_info = self.get_user_info(user_id)
                    if 'payload' in update['object']['message']:
                        payload = update['object']['message']['payload']
                        if 'command' in payload:
                            self.add_user_db(user_info)
                            self.send_message(user_id, message=f'Привет, {user_info["first_name"]}!')
                            self.next_user(user_info)
                        if 'button' in update['object']['message']['payload']:
                            button = self.get_button_name(update['object']['message']['payload'])
                            request_list = {
                                'like': {
                                    self.add_user_db: [user_info],
                                    self.add_relation: [user_id, 'Favorite'],
                                    self.send_message: [user_id,
                                                        'Пользователь теперь у тебя в избранном! А вот и ещё один'],
                                    self.next_user: [user_info]
                                },
                                'next': {
                                    self.next_user: [user_info]
                                },
                                'dislike': {
                                    self.add_user_db: [user_info],
                                    self.add_relation: [user_id, 'Blacklist'],
                                    self.send_message: [user_id,
                                                        'Пользователь скрыт. Но может быть тебе понравится другой...'],
                                    self.next_user: [user_info]
                                },
                                'favorites': {
                                    self.show_like_list: [user_id]
                                }
                            }
                            for k, val in request_list.get(button).items():
                                k(*val)
                    else:
                        self.send_message(user_id, message='Прости, я воспринимаю только кнопочки...')

    def send_message(self, user_id, message, attachments=None):
        url = self.url + 'messages.send'
        params = {
            **self.params,
            'user_id': user_id,
            'random_id': randrange(10 ** 7),
            'message': message,
            'keyboard': json.dumps(self.get_buttons())
        }
        if attachments:
            params['attachment'] = attachments
        requests.post(url, params)

    def get_user_info(self, user_id):
        """
        Получение информации о пользователе или о кандидате в формате [user_id, 'country', 'city', 'bdate', 'sex']
        :param user_id: int
        """
        url = self.url + 'users.get'
        params = {**self.params, 'user_ids': user_id, 'fields': ','.join(self.user_fields)}
        user_info = requests.get(url, params).json()['response']
        return user_info[0]

    def add_user_db(self, user):
        """
        Добавление пользователя, избранных пользователей и пользователей из черного списка в БД.
        Проверка вышеуказанных пользователей на наличие их в БД, если пользователей нет в БД, добавить.
        :param user: dict
        """
        sex = {2: "male", 1: "female"}
        if not self.db.check_user_in_db(user['id']).all():
            db_info = [
                    user['id'],
                    user['first_name'],
                    user['last_name'],
                    sex[user['sex']]
                ]
            if 'city' in user:
                db_info.append(user['city']['title'])
            self.db.add_user(db_info)

    def next_user(self, user_info: object) -> object:
        """
        Проверяет следующего вызванного кандидата по списку избранных и черному списку, если нет кандидата в
        указанных списках, выводит информацию о нём пользователю.
        :return:
        """
        user_id = user_info['id']
        if user_id not in self.candidates:
            user_candidates = self.vk_interaction.get_user_candidates(user_info)
            self.candidates[user_id] = {'offset': 10, 'user_candidates': user_candidates}
        elif not self.candidates[user_id]['user_candidates']:
            offset = self.candidates[user_id]['offset']
            user_candidates = self.vk_interaction.get_user_candidates(user_info, offset)
            self.candidates[user_id]['offset'] += 10
            self.candidates[user_id]['user_candidates'] = user_candidates
        self.current_candidate[user_id] = self.candidates[user_id]['user_candidates'].pop()
        while not self.candidates[user_id]['user_candidates'] or \
                self.current_candidate[user_id]['is_closed'] or \
                self.candidate_done(user_id):
            if not self.candidates[user_id]['user_candidates']:
                offset = self.candidates[user_id]['offset']
                user_candidates = self.vk_interaction.get_user_candidates(user_info, offset)
                self.candidates[user_id]['offset'] += 10
                self.candidates[user_id]['user_candidates'] = user_candidates
            elif self.candidates[user_id]['user_candidates']:
                self.current_candidate[user_id] = self.candidates[user_id]['user_candidates'].pop()

        current_candidate = self.current_candidate[user_id]
        user_name = f"{current_candidate['first_name']} {current_candidate['last_name']}"
        link = f'https://vk.com/id{current_candidate["id"]}'
        photos = self.vk_interaction.photos_get(current_candidate["id"])
        message = f"{user_name}\r\n{link}"
        attachments = []
        i = 0
        for photo in photos:
            if i > 2:
                break
            i += 1
            attachments.append(
                f'photo{current_candidate["id"]}_{photo["id"]}'
            )
        attachment = ",".join(attachments)
        self.send_message(user_id, "Посмотри кого я нашел...")
        self.send_message(user_id, message, attachments=attachment)

    def candidate_done(self, user_id):
        is_done = False
        c_id = self.current_candidate[user_id]['id']
        if c_id in self.db.get_favorite_list(user_id):
            is_done = True
        elif c_id in self.db.get_blocked_list(user_id):
            is_done = True
        return is_done

    def add_relation(self, user_id, status):
        """
        Добавление кандидата в список избранных или в чёрный список.
        :param user_id: int
        :param status: str (Favorite, Blacklist)
        """

        self.add_user_db(self.current_candidate[user_id])
        self.db.add_relation(
            user_id, self.current_candidate[user_id]['id'], status=status)

    def show_like_list(self, user_id):
        """
        Выводит список избранных пользователю.
        :param user_id: int
        """
        like_list = self.db.get_favorite_list(user_id)
        if like_list:
            self.send_message(user_id, "Список избранных: ")
            for i in like_list:
                attachment, message = self.__get_message_info(i)
                self.send_message(user_id, message, attachments=attachment)
        else:
            self.send_message(user_id, "У вас пока не добавлено ни одного пользователя в избранное")

    def __get_message_info(self, user):
        """
        Получение информации о кандидате в формате: имя и фамилия, ссылка, фото.
        :param user:
        """
        name = f"{user[1]} {user[2]}"
        link = f"https://vk.com/id{user[0]}"
        photos = self.vk_interaction.photos_get(user[0])
        attachment = ",".join(
            [f'photo{user[0]}_{ph["id"]}' for idx, ph in enumerate(photos) if idx < 4]
        )
        message = f"{name}\r\n{link}"
        return attachment, message

    @staticmethod
    def get_button_name(string):
        pattern = r'"button"\s*:\s*"(\w+)"'
        match = re.search(pattern, string)
        button_name = match.group(1)
        return button_name

    @staticmethod
    def get_buttons():
        return {
            'one_time': False,
            'buttons': [
                [
                    {
                        'action': {
                            'type': 'text',
                            'payload': '{"button": "like"}',
                            'label': text_emoji("В избранное", "heart")
                        },
                        'color': 'positive'
                    },
                    {
                        'action': {
                            'type': 'text',
                            'payload': '{"button": "next"}',
                            'label': text_emoji("Следующий", "fast_forward")
                        },
                        'color': 'primary'
                    },
                    {
                        'action': {
                            'type': 'text',
                            'payload': '{\"button\": \"dislike\"}',
                            'label': text_emoji("Не нравится", "poop")
                        },
                        'color': 'negative'
                    }
                ],
                [
                    {
                        'action': {
                            'type': 'text',
                            'payload': '{\"button\": \"favorites\"}',
                            'label': text_emoji("Избранное", "star")
                        },
                        'color': 'primary'
                    }
                ]
            ]}


def text_emoji(text, emoji_alias):
    return emoji.emojize(f"{text} :{emoji_alias}:", language="alias")