from random import randrange

import vk_api

from vk_api.longpoll import VkLongPoll, VkEventType

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

token = ''

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)


def write_msg(user_id, message, keyboard=None):
    post = {'user_id': user_id,
            'message': message,
            'random_id': randrange(10 ** 7)
            }
    if keyboard is not None:
        post['keyboard'] = keyboard.get_keyboard()
    vk.method('messages.send', post)


def create_buttons(user_id):
    keyboard = VkKeyboard()
    buttons = ['like', 'next']
    colors = [VkKeyboardColor.NEGATIVE, VkKeyboardColor.POSITIVE]
    for btn, btn_color in zip(buttons, colors):
        keyboard.add_button(btn, btn_color)

    write_msg(user_id, "push 'like' or 'next' buttons", keyboard)


def add_user_db():
    pass


def next_user():
    pass


def conversation():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:

            if event.to_me:
                request = event.text
                user_id = event.user_id

                if request == "привет":
                    write_msg(user_id,
                              f"Хай, {user_id}")  # здесь нужно вместно id вернуть имя, через взаимодействие с ВК
                    create_buttons(user_id)
                elif request == "пока":
                    write_msg(user_id, "Пока((")
                elif request == "like":
                    add_user_db()
                elif request == "next":
                    next_user()
                else:
                    write_msg(user_id, "Не поняла вашего ответа...")


def main():
    conversation()


if __name__ == "__main__":
    main()
