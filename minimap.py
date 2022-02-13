import sys
from io import BytesIO
from PIL.ImageQt import ImageQt

from PyQt5 import uic
from PyQt5.QtCore import Qt
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
        self.deltas = ["0.005", '0.0025']
        float_coordinates = [float(x) for x in self.coordinates]
        self.borders = [180 - (float_coordinates[0] if float_coordinates[0] > 0 else -float_coordinates[0]),
                        90 - (float_coordinates[1] if float_coordinates[1] > 0 else -float_coordinates[1])]
        self.map_params = {
            "ll": ",".join(self.coordinates),
            "spn": ','.join(self.deltas),
            'size': '450,450',
            "l": "map"}
        self.update_image()

    def get_image(self):
        response = requests.get(map_api_server, params=self.map_params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(self.map_params)
            print("Http статус:", response.status_code, "(", response.reason, ")")
        # self.current_img = ImageQt(Image.open(BytesIO(response.content)))
        # return self.current_img
        return ImageQt(Image.open(BytesIO(response.content)))

    def update_image(self):
        self.pixmap = QPixmap.fromImage(self.get_image())
        self.label.setPixmap(self.pixmap)

    def change_coordinates(self, direction):
        if direction == 'right':
            self.coordinates[0] = str(min(float(self.coordinates[0]) + float(self.deltas[0]),
                                          179 - float(self.deltas[0]) / 2))[:15]
        elif direction == 'left':
            self.coordinates[0] = str(max(-179.0 + float(self.deltas[0]) / 2,
                                          float(self.coordinates[0]) - float(self.deltas[0])))[:15]
            # self.coordinates[0] = str(float(self.coordinates[0]) - float(self.deltas[0]))[:15]
        if direction == 'up':
            self.coordinates[1] = str(min(float(self.coordinates[1]) + float(self.deltas[1]),
                                          89 - float(self.deltas[1]) / 2))[:15]
        elif direction == 'down':
            self.coordinates[1] = str(max(-89.0 + float(self.deltas[1]) / 2,
                                          float(self.coordinates[1]) - float(self.deltas[1])))[:15]
        self.map_params['ll'] = ",".join(self.coordinates)
        float_coordinates = [float(x) for x in self.coordinates]
        self.borders = [180 - (float_coordinates[0] if float_coordinates[0] > 0 else -float_coordinates[0]),
                        90 - (float_coordinates[1] if float_coordinates[1] > 0 else -float_coordinates[1])]
        self.update_image()

    def change_zoom(self, plus):
        for i in range(2):
            self.deltas[i] = str(min(max(float(self.deltas[i]) * (2 if plus else 0.5), 0.00125),
                                     min(self.borders * 2) / (i + 1)))[:7]
        # self.map_params['spn'] = ",".join([str(min(self.borders[0] * 2, float(self.delta))),
        #                                    str(min(self.borders[1] * 2, float(self.delta)))])
        self.map_params['spn'] = ','.join(self.deltas)
        self.update_image()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_PageUp:
            self.change_zoom(True)
        elif event.key() == Qt.Key_PageDown:
            self.change_zoom(False)
        elif event.key() == Qt.Key_Right:
            self.change_coordinates('right')
        elif event.key() == Qt.Key_Left:
            self.change_coordinates('left')
        elif event.key() == Qt.Key_Up:
            self.change_coordinates('up')
        elif event.key() == Qt.Key_Down:
            self.change_coordinates('down')


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    win = MyWidget()
    win.show()
    sys.exit(app.exec())