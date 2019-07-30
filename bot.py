## -*- coding: utf-8 -*-

import json
import logging
from time import sleep

import vk_api

from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import *
from random import randint
import threading as trd
import configparser
import sys

import db
from game import Game

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG,
                    filename="log.log")
logger = logging.getLogger(__name__)

with open('game.json', encoding="utf-8") as file:
    game = Game(json.loads(file.read()))

print("Game loaded...")


class Keyboards:

    @staticmethod
    def common_keyboard():
        k = VkKeyboard()
        k.add_button("Инфо", VkKeyboardColor.PRIMARY)
        k.add_button("Помощь", VkKeyboardColor.PRIMARY)
        k.add_button("Вход", VkKeyboardColor.POSITIVE)
        return k.get_keyboard()

    @staticmethod
    def auth_keyboard():
        k = VkKeyboard()
        k.add_button("Капитан", VkKeyboardColor.POSITIVE)
        k.add_line()
        k.add_button("Губернатор", VkKeyboardColor.PRIMARY)
        k.add_line()
        k.add_button("Админ", VkKeyboardColor.NEGATIVE)
        k.add_line()
        k.add_button("Назад", VkKeyboardColor.DEFAULT)
        return k.get_keyboard()

    @staticmethod
    def pick_point_keyboard():
        k = VkKeyboard()
        k.add_button(game.points[0].name, VkKeyboardColor.PRIMARY)
        for point in game.points[1:]:
            k.add_line()
            k.add_button(point.name, VkKeyboardColor.PRIMARY)
        return k.get_keyboard()

    @staticmethod
    def governor_keyboard():
        k = VkKeyboard()
        k.add_button("Покупка", VkKeyboardColor.POSITIVE)
        k.add_button("Продажа", VkKeyboardColor.NEGATIVE)
        k.add_line()
        k.add_button("Цены", VkKeyboardColor.PRIMARY)
        k.add_button("Помощь", VkKeyboardColor.PRIMARY)
        k.add_button("Выход", VkKeyboardColor.DEFAULT)
        return k.get_keyboard()

    @staticmethod
    def admin_keyboard():
        k = VkKeyboard()
        k.add_button("START", VkKeyboardColor.POSITIVE)
        k.add_button("STOP", VkKeyboardColor.NEGATIVE)
        k.add_line()
        k.add_button("Новость", VkKeyboardColor.PRIMARY)
        k.add_button("Выход", VkKeyboardColor.DEFAULT)
        return k.get_keyboard()

    @staticmethod
    def resources_keyboard():
        k = VkKeyboard(one_time=True)
        k.add_button(game.resources[0].name, VkKeyboardColor.PRIMARY)
        for resource in game.resources[1:]:
            k.add_line()
            k.add_button(resource.name, VkKeyboardColor.PRIMARY)
        return k.get_keyboard()

    @staticmethod
    def confirmation_keyboard():
        k = VkKeyboard()
        k.add_button('Подтвердить', VkKeyboardColor.POSITIVE)
        k.add_button('Отклонить', VkKeyboardColor.NEGATIVE)
        return k.get_keyboard()


class Bot:
    users = db.User()

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read(sys.argv[1])
        self.vk = vk_api.VkApi(token=self.config['common']['token'])
        self.longpoll = VkLongPoll(self.vk)

    def polling(self):
        while True:
            print("Polling started...")
            for event in self.longpoll.listen():
                if event.type == VkEventType.MESSAGE_NEW:
                    if event.to_me:
                        self.dispatch(event)

    def resource_controlling(self):
        print(f"Pricing started. Pricing every {game.period} minutes")
        print(f"Waiting for game starting...")
        while True:
            sleep(game.period * 60)
            if game.state == 1:
                print(f"От начала игры прошло {game.current_time().seconds/60} минут...")
                print("Производство ресурсов...")
                game.produce_resources()
                print("Обновление цен...")
                game.update_prices()
                for user in self.users.get_users():
                    if user['auth'] == 1:
                        self.write_msg(user['user_id'], f"Цены обновлены")
                        self.write_msg(user['user_id'], f"{game.get_resources_on_point_string(user['point'])}")
            if game.current_time().seconds/3600 >= game.game_time:
                game.state = 0
                print(f"От начала игры прошло {game.current_time().seconds/60} минут...")
                for user in self.users.get_users():
                    self.write_msg(user['user_id'], f"Игра окончена!")

    def run(self):
        polling = trd.Thread(target=self.polling, name="polling")
        resource_controlling = trd.Thread(target=self.resource_controlling, name="resource_controlling")

        polling.start()
        resource_controlling.start()

    def write_msg(self, user_id, message, keyboard={}, payload={}):
        self.vk.method(
            'messages.send',
            {'user_id': user_id,
             'message': message,
             'keyboard': keyboard,
             "random_id": randint(0, 100000000000),
             'payload': payload
             }
        )

    def get_username(self, user_id):
        res = self.vk.method('users.get', {"user_ids": [user_id]})
        return res[0]['first_name']

    def dispatch(self, event):
        user_id = event.user_id
        message = event.text.upper()
        user = self.users.get_by_id(user_id=user_id)
        context = user['context'] if user else None
        auth = self.users.get_by_id(user_id=user_id)['auth'] if user else None

        if message == 'НАЧАТЬ':
            self.users.set_context(user_id=user_id, context=message)
            self.write_msg(user_id, f"{self.get_username(user_id=user_id)}, приветствую в игре {game.name}")
            if self.users.get_by_id(user_id=user_id):
                self.write_msg(user_id, f"Мы уже знакомы, принимай управление!",
                               keyboard=Keyboards.common_keyboard())
            else:
                self.write_msg(user_id, f"Мы еще не знакомы, сейчас я тебя проскнирую...")
                self.users.add_user(user_id)
                self.write_msg(user_id, f"Сканирование успешно завершено! Принимай управление!",
                               keyboard=Keyboards.common_keyboard())
        elif message == 'ПОМОЩЬ':
            self.write_msg(user_id, game.help_message)

        elif message == 'ВХОД':
            self.write_msg(user_id, f"Выберите роль!",
                           keyboard=Keyboards.auth_keyboard())

        elif message == 'START':
            game.start()
            for user in self.users.get_users():
                self.write_msg(user['user_id'], f"Игра началась!")

        elif message == 'STOP':
            game.stop()
            for user in self.users.get_users():
                self.write_msg(user['user_id'], f"Игра остановлена!")

        elif message == 'ГУБЕРНАТОР' or message == 'АДМИН':
            self.users.set_context(user_id=user_id, context=message)
            self.write_msg(user_id, f"Введите пароль")

        elif message == 'ТОЧКИ':
            self.users.set_context(user_id=user_id, context=message)
            self.write_msg(user_id, f"Доступные точки",
                           keyboard=Keyboards.pick_point_keyboard())

        elif message == 'ВЫХОД':
            self.users.set_context(user_id=user_id, context="")
            self.users.set_auth(user_id=user_id, auth=0)
            self.write_msg(user_id, f"Принято!",
                           keyboard=Keyboards.common_keyboard())

        elif message == 'ЦЕНЫ':
            user = self.users.get_by_id(user_id)
            if not user['auth'] == 1:
                self.write_msg(user_id, f"У вас нет доступа!",
                               keyboard=Keyboards.common_keyboard())
            elif not user["point"]:
                self.write_msg(user_id, f"Ошибка! Вы не привязаны к точке!",
                               keyboard=Keyboards.common_keyboard())
            else:
                self.write_msg(user_id, game.get_resources_on_point_string(user['point']),
                               keyboard=Keyboards.governor_keyboard())

        elif message == 'ПОКУПКА' or message == 'ПРОДАЖА':
            if game.state != 1:
                self.write_msg(user_id, f'Игра еще не началась!')
            else:
                user = self.users.get_by_id(user_id)
                if not user['auth'] == 1:
                    self.write_msg(user_id, f"У вас нет доступа!",
                                   keyboard=Keyboards.common_keyboard())
                elif not user["point"]:
                    self.write_msg(user_id, f"Ошибка! Вы не привязаны к точке!",
                                   keyboard=Keyboards.common_keyboard())
                else:
                    self.users.set_context(user_id=user_id, context=message)
                    self.write_msg(user_id, game.get_resources_on_point_string(user['point']))
                    self.write_msg(user_id, f"Выберите ресурс:",
                                   keyboard=Keyboards.resources_keyboard())

        elif message in map(str.upper, [resource.name for resource in game.resources]) \
                and (context == 'ПОКУПКА' or context == 'ПРОДАЖА'):

            if not game.is_base_resource(message, user['point']):
                self.users.set_context(user_id, f'{context}1_{message}')
                self.write_msg(user_id, f"Введите количество")
            else:
                if auth == 0:
                    self.users.set_context(user_id, '')
                    self.write_msg(user_id, f"Нельзя покупать базовый ресурс!", Keyboards.common_keyboard())
                elif auth == 1:
                    self.users.set_context(user_id, 'ГУБЕРНАТОР')
                    self.write_msg(user_id, f"Нельзя покупать базовый ресурс!", Keyboards.governor_keyboard())
                elif auth == 2:
                    self.users.set_context(user_id, 'АДМИН')
                    self.write_msg(user_id, f"Нельзя покупать базовый ресурс!!", Keyboards.admin_keyboard())

        elif message == "ПОДТВЕРДИТЬ" and (context.find("ПОКУПКА2") or context.find("ПРОДАЖА2")):
            contract = context.split("_")
            amount = int(contract[2])
            resource_name = contract[1]
            if contract[0] == "ПРОДАЖА2":
                game.sell(point=user['point'], name=resource_name, amount=amount)
                self.write_msg(user_id, f'Успешно!', Keyboards.governor_keyboard())
                if auth == 0:
                    self.users.set_context(user_id, '')
                elif auth == 1:
                    self.users.set_context(user_id, 'ГУБЕРНАТОР')
                elif auth == 2:
                    self.users.set_context(user_id, 'АДМИН')
            elif contract[0] == "ПОКУПКА2":
                game.buy(point=user['point'], name=resource_name, amount=amount)
                self.write_msg(user_id, f'Успешно!', Keyboards.governor_keyboard())
                if auth == 0:
                    self.users.set_context(user_id, '')
                elif auth == 1:
                    self.users.set_context(user_id, 'ГУБЕРНАТОР')
                elif auth == 2:
                    self.users.set_context(user_id, 'АДМИН')
            else:
                self.write_msg(user_id, f"Ошибка!", Keyboards.governor_keyboard())
                if auth == 0:
                    self.users.set_context(user_id, '')
                elif auth == 1:
                    self.users.set_context(user_id, 'ГУБЕРНАТОР')
                elif auth == 2:
                    self.users.set_context(user_id, 'АДМИН')

        elif message == 'ОТКЛОНИТЬ':

            if auth == 0:
                self.users.set_context(user_id, '')
                self.write_msg(user_id, f"Принято!", Keyboards.common_keyboard())
            elif auth == 1:
                self.users.set_context(user_id, 'ГУБЕРНАТОР')
                self.write_msg(user_id, f"Принято!", Keyboards.governor_keyboard())
            elif auth == 2:
                self.users.set_context(user_id, 'АДМИН')
                self.write_msg(user_id, f"Принято!", Keyboards.admin_keyboard())

        else:
            if context and context == 'ГУБЕРНАТОР':
                if message == game.gov_pass:
                    self.users.set_auth(user_id=user_id, auth=1)
                    self.write_msg(user_id, f"Авторизация пройдена. Выберите точку",
                                   keyboard=Keyboards.pick_point_keyboard())
                elif message in map(str.upper, game.get_points_names()):
                    self.users.set_point(user_id=user_id, point=message)
                    self.write_msg(user_id, f"Добро пожаловать на базу, Губернатор!",
                                   keyboard=Keyboards.governor_keyboard())

            elif context and context == 'АДМИН':
                if message == game.adm_pass:
                    self.users.set_auth(user_id=user_id, auth=2)
                    self.write_msg(user_id, f"Авторизация пройдена",
                                   keyboard=Keyboards.admin_keyboard())

            elif context and context.find("ПОКУПКА1") + 1 and message.isnumeric():
                amount = int(message)
                resource_name = context.split("_")[1]
                price = game.get_resource_price(name=resource_name, point=user['point'])
                self.users.set_context(user_id, f'ПОКУПКА2_{resource_name}_{amount}')
                self.write_msg(user_id, f"Стоимость составит {price * amount}",
                               keyboard=Keyboards.confirmation_keyboard())

            elif context and context.find("ПРОДАЖА1") + 1 and message.isnumeric():
                amount = int(message)
                resource_name = context.split("_")[1]

                if game.check_availability(resource_name, user['point'], amount):
                    price = game.get_resource_price(name=resource_name, point=user['point'])
                    self.users.set_context(user_id, f'ПРОДАЖА2_{resource_name}_{amount}')
                    self.write_msg(user_id, f"Стоимость составит {price * amount}",
                                   keyboard=Keyboards.confirmation_keyboard())
                else:
                    self.write_msg(user_id, f"Недостаточно {resource_name}",
                                   keyboard=Keyboards.governor_keyboard())

            else:
                self.write_msg(user_id, "Не поняла вашего ответа...")

        print(f'{user_id} --- {message} --- {context} --> {self.users.get_context(user_id)}')
