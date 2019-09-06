# -*- coding: utf-8 -*-
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from const import images_dir


class ImageForCover:
    """ Родительский класс для всех изображений,
        которые будут расположены на обложке """

    def __init__(self, h, w):
        self.h = h
        self.w = w


class Avatar(ImageForCover):
    """ Класс для работы с аварками пользователя """

    def __init__(self, image_url, h=200, w=200):
        super().__init__(h, w)
        response = requests.get(image_url)
        self.image = Image.open(BytesIO(response.content)).resize((self.w, self.h))

    def crap_corners(self, ellipse_size=(3, 3, 197, 197)):
        im_a = Image.new('L', self.image.size, 0)
        draw = ImageDraw.Draw(im_a)
        draw.ellipse(ellipse_size, fill=255)
        im_a_blur = im_a.filter(ImageFilter.GaussianBlur(2))
        self.image.putalpha(im_a_blur)


class Cover(ImageForCover):
    """ Класс для работы с обложкой сообщества """

    def __init__(self, image, h=400, w=1590):
        super().__init__(h, w)
        self.image = Image.open(image).resize((self.w, self.h))

    def add_text(self, text, font_path, font_size=30, width=None, height=320):
        font = ImageFont.truetype(font_path, font_size)
        draw = ImageDraw.Draw(self.image)
        w, h = draw.textsize(text, font)
        if width == None:
            width = (self.w-w)/2
        draw.text((width, height), text, font=font, fill='black')

    def add_user_image(self, avatar, width=100, height=100):
        self.image.paste(avatar, (width, height),  avatar)

    def save(self):
        self.image.save(os.path.join(images_dir, 'final.jpg'))
