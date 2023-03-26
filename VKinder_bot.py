# -*- coding: utf-8 -*-

from random import randrange

import vk_api

from vk_api.longpoll import VkLongPoll, VkEventType

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class VKinderBot:
    def __init__(self, token):
        self.token = token
        self.vk = vk_api.VkApi(token=self.token)
        self.longpoll = VkLongPoll(self.vk)
        self.user_id = None

    def write_msg(self, message, keyboard=None):
        post = {
            "user_id": self.user_id,
            "message": message,
            "random_id": randrange(10**7),
        }
        if keyboard is not None:
            if message == "Пока((":
                post["keyboard"] = keyboard.get_empty_keyboard()
            else:
                post["keyboard"] = keyboard.get_keyboard()

        self.vk.method("messages.send", post)

    def create_buttons(self):
        keyboard = VkKeyboard()
        buttons = ["like", "next", "add in black list"]
        colors = [
            VkKeyboardColor.NEGATIVE,
            VkKeyboardColor.POSITIVE,
            VkKeyboardColor.PRIMARY,
        ]
        for btn, btn_color in zip(buttons, colors):
            keyboard.add_button(btn, btn_color)
        keyboard.add_line()
        keyboard.add_button("like list", VkKeyboardColor.NEGATIVE)
        self.write_msg("Push 'like' or 'next' buttons", keyboard)

    def conversation(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW:
                if event.to_me:
                    request = event.text
                    self.user_id = event.user_id
                    request_list = {
                        "привет": {
                            self.write_msg: [f"Хай, {self.user_id}"],
                            self.create_buttons: [],
                            self.next_user: [],
                        },
                        "пока": {self.write_msg: ["Пока((", VkKeyboard()]},
                        "next": {self.next_user: []},
                        "like": {self.add_user_db: []},
                        "like list": {self.show_like_list: []},
                        "add in black list": {self.add_black_list: []},
                    }
                    if request_list.get(request) is None:
                        self.write_msg("Не поняла вашего ответа...")
                    else:
                        for k, val in request_list.get(request).items():
                            k(*val)

    def add_user_db(self):
        pass

    def next_user(self):
        pass

    def show_like_list(self):
        pass

    def add_black_list(self):
        pass


def main():
    token = ""
    VKinderBot(token).conversation()


if __name__ == "__main__":
    main()
