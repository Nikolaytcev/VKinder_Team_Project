from VK_interaction.interaction import VkInteraction
from VKinder_db.db import DBService, DBHandler, connect_to_db

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
        self.user_fields = ["country", "city", "bdate", "sex"]
        self.user_candidates = {}
        self.current_candidate = None
        self.users_data = {}

    def write_msg(self, message, keyboard=None, attachment=None):
        params = {
            "user_id": self.user["id"],
            "message": message,
            "random_id": randrange(10**7),
        }
        if keyboard:
            if message == "Пока((":
                params["keyboard"] = keyboard.get_empty_keyboard()
            else:
                params["keyboard"] = keyboard.get_keyboard()
        if attachment:
            params["attachment"] = attachment

        self.vk_bot.method("messages.send", params)

    def create_buttons(self):
        keyboard = VkKeyboard()
        buttons = [
            text_emoji("В избранное", "heart"),
            text_emoji("Следующий", "fast_forward"),
            text_emoji("Не нравится", "poop"),
        ]
        colors = [
            VkKeyboardColor.POSITIVE,
            VkKeyboardColor.PRIMARY,
            VkKeyboardColor.NEGATIVE,
        ]
        for btn, btn_color in zip(buttons, colors):
            keyboard.add_button(btn, btn_color)
        keyboard.add_line()
        keyboard.add_button(text_emoji("Избранное", "star"), VkKeyboardColor.PRIMARY)
        self.write_msg("Посмотри кого я нашел...", keyboard)

    def conversation(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                request = event.text
                self.user = self.get_user_info(event.user_id)

                self.user_candidates[event.user_id] = self.vk_interaction.get_user_candidates(self.user)

                request_list = {
                    "привет": {
                        self.write_msg: [f"Привет, {self.user['first_name']}!"],
                        self.create_buttons: [],
                        self.next_user: [],
                        self.add_user_db: [request],
                    },
                    "пока": {self.write_msg: ["Пока((", VkKeyboard()]},
                    text_emoji("Следующий", "fast_forward"): {self.next_user: []},
                    text_emoji("В избранное", "heart"): {
                        self.add_user_db: [request],
                        self.add_relation: ["Favorite"],
                    },
                    text_emoji("Избранное", "star"): {self.show_like_list: []},
                    text_emoji("Не нравится", "poop"): {
                        self.add_user_db: [request],
                        self.add_relation: ["Blacklist"],
                    },
                }
                if request_list.get(request) is None:
                    self.write_msg("А можно поподробнее?...")
                else:
                    for k, val in request_list.get(request).items():
                        k(*val)

    def add_user_db(self, request):
        sex = {2: "male", 1: "female"}
        if request == "привет":
            if not self.db.check_user_in_db(self.user["id"]).all():
                self.db.add_user(
                    [
                        self.user["id"],
                        self.user["first_name"],
                        self.user["last_name"],
                        sex.get(self.user["sex"]),
                        self.user["city"]["title"],
                    ]
                )
        else:
            if not self.db.check_user_in_db(self.users_data.get(self.user["id"])).all():
                like_person = self.get_user_info(self.users_data.get(self.user["id"]))
                self.db.add_user(
                    [
                        like_person["id"],
                        like_person["first_name"],
                        like_person["last_name"],
                        sex.get(like_person["sex"]),
                        like_person["city"]["title"],
                    ]
                )

    def next_user(self):

        self.current_candidate = self.user_candidates.get(self.user['id']).pop()

        try:
            favorite_list = [i[0] for i in self.db.get_blocked_list(self.user["id"])]
            blocked_list = [i[0] for i in self.db.get_favorite_list(self.user["id"])]
            if (
                self.current_candidate["id"] not in favorite_list
                and self.current_candidate["id"] not in blocked_list
            ):
                self.users_data[self.user["id"]] = self.current_candidate["id"]
                user_name = f"{self.current_candidate['first_name']} {self.current_candidate['last_name']}"
                link = f'https://vk.com/id{self.current_candidate["id"]}'
                photos = self.vk_interaction.photos_get(self.current_candidate["id"])
                message = f"{user_name}\r\n{link}"
                attachments = []
                i = 0
                for photo in photos:
                    if i > 2:
                        break
                    i += 1
                    attachments.append(
                        f'photo{self.current_candidate["id"]}_{photo["id"]}'
                    )
                attachment = ",".join(attachments)
                self.write_msg(message, attachment=attachment)
            else:
                self.next_user()
        except vk_api.exceptions.ApiError:
            print("This profile is private")
            self.next_user()

    def __check_mutual_sympathy(self):
        user_favorite_list = [i[0] for i in self.db.get_favorite_list(self.user["id"])]
        candidate_favorite_list = [
            i[0]
            for i in self.db.get_favorite_list(self.users_data.get(self.user["id"]))
        ]
        return (
            self.user["id"] in candidate_favorite_list
            and self.users_data.get(self.user["id"]) in user_favorite_list
        )

    def __get_message_info(self, user):
        name = f"{user[1]} {user[2]}"
        link = f"https://vk.com/id{user[0]}"
        photos = self.vk_interaction.photos_get(user[0])
        attachment = ",".join(
            [f'photo{user[0]}_{ph["id"]}' for idx, ph in enumerate(photos) if idx < 4]
        )
        message = f"{name}\r\n{link}"
        return attachment, message

    def add_relation(self, status):
        self.db.add_relation(
            self.user["id"], self.users_data.get(self.user["id"]), status=status
        )
        if self.__check_mutual_sympathy():
            attachment, message = self.__get_message_info(
                self.get_user_info(self.users_data.get(self.user["id"]))
            )
            self.write_msg(
                f" У вас взаимная симпатия с {message}", attachment=attachment
            )
        else:
            self.next_user()

    def show_like_list(self):
        like_list = self.db.get_favorite_list(self.user["id"])
        self.write_msg("Список избранных: ")
        if like_list:
            for i in like_list:
                attachment, message = self.__get_message_info(i)
                self.write_msg(message, attachment=attachment)

    def get_user_info(self, user_id):
        values = {"user_ids": user_id, "fields": ", ".join(self.user_fields)}
        user_info = self.vk_bot.method("users.get", values=values)
        return user_info[0]


def text_emoji(text, emoji_alias):
    return emoji.emojize(f"{text} :{emoji_alias}:", language="alias")
