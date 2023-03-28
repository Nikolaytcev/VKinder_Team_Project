from VK_interaction.interaction import VkInteraction

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from random import randrange
import vk_api
import emoji


class VKinderBot:
    def __init__(self, bot_token, vk_token, db):
        self.db = db
        self.vk_interaction = VkInteraction(token=vk_token)
        self.vk_bot = vk_api.VkApi(token=bot_token)
        self.longpoll = VkLongPoll(self.vk_bot)
        self.user = {}
        self.user_fields = ['country', 'city', 'bdate', 'sex']
        self.user_candidates = []
        self.current_candidate = None

    def write_msg(self, message, keyboard=None, attachment=None):
        params = {
            "user_id": self.user['id'],
            "message": message,
            "random_id": randrange(10**7),
        }
        if keyboard:
            if message == 'Пока((':
                params['keyboard'] = keyboard.get_empty_keyboard()
            else:
                params['keyboard'] = keyboard.get_keyboard()
        if attachment:
            params['attachment'] = attachment

        self.vk_bot.method("messages.send", params)

    def create_buttons(self):
        keyboard = VkKeyboard()
        buttons = [
            text_emoji('В избранное', 'heart'),
            text_emoji('Следующий', 'fast_forward'),
            text_emoji('Не нравится', 'poop')
        ]
        colors = [
            VkKeyboardColor.POSITIVE,
            VkKeyboardColor.PRIMARY,
            VkKeyboardColor.NEGATIVE,
        ]
        for btn, btn_color in zip(buttons, colors):
            keyboard.add_button(btn, btn_color)
        keyboard.add_line()
        keyboard.add_button(text_emoji('Избранное', 'star'), VkKeyboardColor.PRIMARY)

    def conversation(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                request = event.text
                self.user = self.get_user_info(event.user_id)
                if not self.user_candidates:
                    self.user_candidates = self.vk_interaction.get_user_candidates(self.user)
                request_list = {
                    "привет": {
                        self.write_msg: [f"Привет, {self.user['first_name']}! Посмотри кого я нашел..."],
                        self.create_buttons: [],
                        self.next_user: [],
                    },
                    "пока": {self.write_msg: ["Пока((", VkKeyboard()]},
                    text_emoji('Следующий', 'fast_forward'): {self.next_user: []},
                    text_emoji('В избранное', 'heart'): {self.add_user_db: []},
                    text_emoji('Избранное', 'star'): {self.show_like_list: []},
                    text_emoji('Не нравится', 'poop'): {self.add_black_list: []},
                }
                if request_list.get(request) is None:
                    self.write_msg("А можно поподробнее?...")
                else:
                    for k, val in request_list.get(request).items():
                        k(*val)

    def add_user_db(self):
        print('Вызван add_user_db')

    def next_user(self):
        self.current_candidate = self.user_candidates.pop()
        user_name = f"{self.current_candidate['first_name']} {self.current_candidate['last_name']}"
        link = f'https://vk.com/id{self.current_candidate["id"]}'
        photos = self.vk_interaction.photos_get(self.current_candidate['id'])
        message = f'{user_name}\r\n{link}'
        print(photos)
        attachments = []
        i = 0
        for photo in photos:
            if i > 2:
                break
            i += 1
            attachments.append(f'photo{self.current_candidate["id"]}_{photo["id"]}')
        attachment = ','.join(attachments)
        print(f'{attachment=}')
        self.write_msg(message, attachment=attachment)

    def show_like_list(self):
        print('Вызван show_like_list')

    def add_black_list(self):
        print('Вызван add_black_list')

    def get_user_info(self, user_id):
        values = {
            'user_ids': user_id,
            'fields': ', '.join(self.user_fields)
        }
        user_info = self.vk_bot.method('users.get', values=values)
        return user_info[0]


def text_emoji(text, emoji_alias):
    return emoji.emojize(f'{text} :{emoji_alias}:', language='alias')



