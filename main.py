import os
import requests
from re import search
from random import randint
from time import time
from string import punctuation
from flask import Flask, request
import vk
from const import confirmation_token, token, group_id, images_dir, fonts_dir
from cover_editor import Cover, Avatar

app = Flask(__name__)


def get_upload_url(api):
    data = api.photos.getOwnerCoverPhotoUploadServer(access_token=token,
                                                     group_id=group_id,
                                                     crop_x2=1590,
                                                     crop_y2=400)
    return data['upload_url']


def get_api():
    session = vk.Session()
    return vk.API(session, v=5.101)


def create_cover(data):
    """ Функция создания обложки с аватаркой пользователя """

    cov = Cover(os.path.join(images_dir, 'obl.jpg'))
    try:
        photo = data['photo_200']
    except KeyError:
        photo = data['photo_100']
    ava = Avatar(photo)
    ava.crap_corners()
    cov.add_text(f'{data["first_name"]} {data["last_name"]}',
                 os.path.join(fonts_dir, 'comicsansms.ttf'),
                 font_size=35,
                 height=300)
    cov.add_user_image(ava.image, int((cov.w - ava.w) / 2), 100)
    cov.save()


def upload_cover(api):
    upload_url = get_upload_url(api)
    cover_file = {'photo': open(os.path.join(images_dir, 'final.jpg'),
                                'rb')}
    r = requests.post(upload_url, files=cover_file)
    r_json = r.json()
    api.photos.saveOwnerCoverPhoto(access_token=token,
                                   hash=r_json['hash'],
                                   photo=r_json['photo'])


def change_cover(user_url, api, current_user_id):
    """ Функция смены обложки при сообщении пользователя """

    message = 'Произошла неизвестная ошибка! Обратитесь к администратору.'
    try:
        if search(r'vk.com/', user_url) is None:
            raise Exception('invalid_url')
        if user_url[-1] == '/':
            user_url = user_url[:-1:]
        user_id = user_url.split('/')[-1]
        user_id = "".join(el for el in user_id if el not in punctuation)
        data = api.users.get(access_token=token,
                             user_ids=str(user_id),
                             fields='photo_100, photo_200')[0]
        try:
            data['deactivated']
            message = 'Данный пользователь был удален.'
        except KeyError:
            create_cover(data)
            upload_cover(api)
            message = f'Пользователь {data["first_name"]} \
                      {data["last_name"]} установлен на обложку.'
    except vk.exceptions.VkAPIError as err:
        if err.code == 113:
            message = 'Вероятно такого пользователя нет.\
                       Проверьте корректость введенного адреса.'
        if err.code == 129:
            message = 'Не удалось загрузить обложку. \
                        Обратитесь к администратору.'
    except Exception as err:
        if str(err) == 'invalid_url':
            message = 'Полученное сообщение не является ссылкой на профиль вк.'
    api.messages.send(access_token=token,
                      user_id=str(current_user_id),
                      message=message,
                      random_id=str(randint(1, 999999999999)))


@app.route('/test/', methods=['POST'])
def main():
    """ Функция ожидания и обработки запросов от vk"""

    data = request.get_json()
    api = get_api()

    if data['type'] == 'confirmation':
        return confirmation_token
    elif data['type'] == 'message_new':
        user_id = data['object']['from_id']
        if int(data['object']['date']) > time() - 10:
            change_cover(data['object']['text'], api, user_id)
    elif data['type'] == 'group_join':
        user_id = data['object']['user_id']
        data = api.users.get(access_token=token,
                             user_ids=str(user_id),
                             fields='photo_100, photo_200')[0]
        create_cover(data)
        upload_cover(api)
    return 'OK'


if __name__ == '__main__':
    app.debug = False
    app.run()
