import sys
from io import BytesIO
from PIL.ImageQt import ImageQt

from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow

import requests
from PIL import Image

if sys.argv[1:]:
    toponym_to_find = " ".join(sys.argv[1:])
else:
    toponym_to_find = input()

geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

geocoder_params = {"apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                   "geocode": toponym_to_find, "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)
json_response = response.json()
toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
toponym_coodrinates = toponym["Point"]["pos"]

map_api_server = "http://static-maps.yandex.ru/1.x/"


class MyWidget(QMainWindow):
    def __init__(self):
        super(MyWidget, self).__init__()
        uic.loadUi('mapp.ui', self)
        self.initUi()

    def initUi(self):
        self.coordinates = toponym_coodrinates.split(" ")
        self.delta = "0.005"
        self.map_params = {
            "ll": ",".join(self.coordinates),
            "spn": ",".join([self.delta, self.delta]),
            'size': '650,450',
            "l": "map"}
        self.pixmap = QPixmap.fromImage(self.get_image())
        self.label.setPixmap(self.pixmap)

    def get_image(self):
        response = requests.get(map_api_server, params=self.map_params)
        # self.current_img = ImageQt(Image.open(BytesIO(response.content)))
        # return self.current_img
        return ImageQt(Image.open(BytesIO(response.content)))


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    win = MyWidget()
    win.show()
    sys.exit(app.exec())