import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
from Vk_token import TOKEN
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import requests
import wikipediaapi
import sqlite3
from Rapid_api import x_rapidapi_host, x_rapidapi_key

Genres = ['комедия', 'драма', 'мелодрама', 'детектив', 'документальный', 'ужасы', 'музыка', 'фантастика',
          'анимация', 'биография', 'боевик', 'приключения', 'война', 'семейный' 'триллер',
          'фэнтези', 'вестерн', 'мистика', 'короткометражный', 'мюзикл', 'исторический', 'нуар']
url = "https://movie-database-imdb-alternative.p.rapidapi.com/"

settings = dict(one_time=False, inline=True)
main_keyboard = VkKeyboard(**settings)
main_keyboard.add_callback_button(label='Посоветуй фильм', color=VkKeyboardColor.POSITIVE, payload={"type": "custom_1"})
main_keyboard.add_line()
main_keyboard.add_callback_button(label='Найди Информацию о фильме', color=VkKeyboardColor.PRIMARY,
                                  payload={"type": "custom_2"})
cancel_keyboard = VkKeyboard(**settings)
cancel_keyboard.add_callback_button(label='Отменить', color=VkKeyboardColor.NEGATIVE, payload={"type": "cancel"})
FAQ_keyboard = VkKeyboard(**settings)
FAQ_keyboard.add_callback_button(label='Как правильно сделать запрос?', color=VkKeyboardColor.POSITIVE,
                                 payload={"type": "question"})
FAQ_keyboard.add_line()
FAQ_keyboard.add_callback_button(label='Список жанров', color=VkKeyboardColor.PRIMARY, payload={"type": "genres"})
FAQ_keyboard.add_line()
FAQ_keyboard.add_callback_button(label='Отменить', color=VkKeyboardColor.NEGATIVE, payload={"type": "cancel_2"})


def test_lang(a):
    if 122 >= ord(a) >= 97 or 90 >= ord(a) >= 65:
        return True
    else:
        return False


def imdb_req(title, wiki_ru, x_rapidapi_key, x_rapidapi_host):
    try:
        if test_lang(title[0]) is True:
            params = {"s": title, "page": "1"}
            headers = {
                'x-rapidapi-key': x_rapidapi_key,
                'x-rapidapi-host': x_rapidapi_host
            }
            response = requests.request("GET", url, headers=headers, params=params).json()
            response = response['Search'][0]
            text = ""
            for el in response:
                if type(response[el]) == str:
                    if el == 'imdbID':
                        text += 'Ссылка на IMDB: ' + "https://www.imdb.com/title/" + response[
                            el] + "/" + "\n"
                    else:
                        text += el + ": " + response[el] + '\n'
            return text
        else:
            page_py = wiki_ru.page(title)
            info_1 = page_py.summary[0:100]
            info = info_1[info_1.find("("):]
            info = info[:info.find(")")]
            info = info[info.find(".") + 2:]
            params = {"s": info, "page": "1"}
            headers = {
                'x-rapidapi-key': x_rapidapi_key,
                'x-rapidapi-host': x_rapidapi_host
            }
            response = requests.request("GET", url, headers=headers, params=params)
            response = response.json()
            response = response['Search'][0]
            text = ""
            for el in response:
                if type(response[el]) == str:
                    if el == 'imdbID':
                        text += 'Ссылка на IMDB: ' + "https://www.imdb.com/title/" + response[
                            el] + "/" + "\n"
                    else:
                        text += el + ": " + response[el] + '\n'
            return text
    except Exception:
        text_err = 'К сожалению, название фильма было написано с ошибкой или бот не смог найти подходящей ' \
                   'вам информации, поробуйте написать название '  \
                   'фильма снова, либо нажмите кнопку отменить.'
        return text_err


def sq_req(text):
    try:
        text = text.split()
        genre = text[0]
        if text[1] != "-":
            duration = text[1].split("-")
        else:
            duration = text[1]
        if "-" in text[2]:
            year = text[2].split("-")
        else:
            year = text[2]
        con = sqlite3.connect("films_db.sqlite")
        cur = con.cursor()
        req = 'SELECT title FROM films WHERE '
        flag_and = False
        if text[2] != "-":
            if type(text[2]) is str:
                req += '(year = {})'.format(year)
            else:
                req += '(year BETWEEN {} AND {})'.format(year[0], year[1])
            flag_and = True
        if duration != "-":
            if flag_and is False:
                req += '(duration BETWEEN {} AND {})'.format(duration[0], duration[1])
                flag_and = True
            else:
                req += ' AND (duration BETWEEN {} AND {})'.format(duration[0], duration[1])
                flag_and = True
        if genre != "-":
            if flag_and is False:
                req += '(genre=(SELECT id FROM genres WHERE title = "{}"))'.format(genre)
            else:
                req += ' AND (genre=(SELECT id FROM genres WHERE title = "{}"))'.format(genre)
            flag_and = True
        if flag_and is False:
            req = req[:24]
        result = cur.execute(req).fetchall()
    except Exception:
        return "Запрос составлен некорректно."
    mn = []
    text_f = "Фильмы, которые я нашел:\n"
    if result:
        if len(result) > 20:
            for el in range(20):
                a = random.choice(result)
                result.remove(a)
                mn.append(a)
            for el in mn:
                text_f += el[0] + '\n'
        else:
            for el in result:
                text_f += el[0] + '\n'
    else:
        text_f = "По вашему запросу ничего не было найдено, возможно он был составлен некорректно."
    return text_f


def main():
    vk_session = vk_api.VkApi(
        token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, 204089127)
    flag_find = False
    flag_advice = False
    wiki_ru = wikipediaapi.Wikipedia('ru')

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if flag_find is True:
                title = event.obj.message['text']
                information = imdb_req(title, wiki_ru, x_rapidapi_key, x_rapidapi_host)
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=information,
                                 random_id=random.randint(0, 2 ** 64))
                if information[:5] == "Title":
                    flag_find = False

            elif flag_advice is True:
                text_f = sq_req(event.obj.message['text'])
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message=text_f,
                                 random_id=random.randint(0, 2 ** 64))
                if text_f[:7] == "Я нашел":
                    flag_advice = False

            elif event.obj.message['text'] == "Старт":
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="Привет, я помогу тебе найти интересующий тебя фильм.",
                                 random_id=random.randint(0, 2 ** 64))
                if event.obj.message['text'] != '':
                    if event.from_user:
                        if 'callback' not in event.obj.client_info['button_actions']:
                            print(f'Клиент {event.obj.message["from_id"]} не поддерж. callback')
                        vk.messages.send(
                            user_id=event.obj.message['from_id'],
                            random_id=random.randint(0, 2 ** 64),
                            peer_id=event.obj.message['from_id'],
                            keyboard=main_keyboard.get_keyboard(),
                            message="Выберите необходимую вам функцию на клавиатуре.")

            else:
                vk.messages.send(user_id=event.obj.message['from_id'],
                                 message="{}, чтобы начать работу с чат ботом напиши команду 'Старт'.".format(vk.users.
                                                                                                              get(
                                 user_id=event.obj.message['from_id'])[0]['first_name']),
                                 random_id=random.randint(0, 2 ** 64))

        elif event.type == VkBotEventType.MESSAGE_EVENT:
            if event.object.payload.get('type') == 'custom_1':
                vk.messages.send(user_id=event.object.user_id,
                                 message="Введите нужную информацию о фильме.",
                                 keyboard=FAQ_keyboard.get_keyboard(),
                                 random_id=random.randint(0, 2 ** 64))
                flag_advice = True
                flag_find = False

            if event.object.payload.get('type') == 'custom_2':
                vk.messages.send(user_id=event.object.user_id,
                                 message="Введите название фильма, Допускается запись как на русском, "
                                         "так и на английском.",
                                 keyboard=cancel_keyboard.get_keyboard(),
                                 random_id=random.randint(0, 2 ** 64))
                flag_find = True
                flag_advice = False

            if event.object.payload.get('type') == 'cancel':
                flag_find = False

            if event.object.payload.get('type') == 'question':
                vk.messages.send(user_id=event.object.user_id,
                                 message="Бот принимает запросы в формате 'Жанр Время Год_выпуска'\n"
                                         "1. Жанр необходимо выбрать из 'Списка жанров'\n"
                                         "2. Временной промежуток записывется в минутах\n"
                                         "3. Вы можете записать как конкретный год, так и охватить сразу несколько "
                                         "лет\n"
                                         "4. Если вас не интересует какая либо информация о фильме, поставьте "
                                         "вместо нее '-'\n"
                                         "Примеры: 'комедия 90-180 2000-2010', '- 90-120 2005'",
                                 random_id=random.randint(0, 2 ** 64))

            if event.object.payload.get('type') == 'genres':
                text_genres = "Список жанров:\n"
                text_genres += ", ".join(Genres)
                vk.messages.send(user_id=event.object.user_id,
                                 message=text_genres,
                                 random_id=random.randint(0, 2 ** 64))

            if event.object.payload.get('type') == 'cancel_2':
                flag_advice = False


if __name__ == '__main__':
    main()