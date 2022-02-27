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

map_api_server = "http://static-maps.yandex.ru/1.x/"

modes = {'map': 'map', 'satellite': 'sat', 'hybrid': 'sat,skl', 'traffic': 'map,trf,skl'}


class MyWidget(QMainWindow):
    def __init__(self):
        super(MyWidget, self).__init__()
        uic.loadUi('mapp.ui', self)
        self.address = ('', '')
        self.deltas = ["0.005", '0.0025']
        self.lon_deformation = 1.95
        self.refreshButton.clicked.connect(self.refresh_search)
        self.searchBar.editingFinished.connect(self.search_geocode)
        self.mailBox.stateChanged.connect(self.update_statusbar)
        self.modeBox.currentTextChanged.connect(self.change_mode)
        self.initUi()

    def initUi(self):
        self.geocoder_params = {"apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
                                "geocode": toponym_to_find, "format": "json"}
        response = requests.get(geocoder_api_server, params=self.geocoder_params).json()
        coodrinates = response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
        self.coordinates = coodrinates.split(" ")
        float_coordinates = [float(x) for x in self.coordinates]
        self.borders = [180 - (float_coordinates[0] if float_coordinates[0] > 0 else -float_coordinates[0]),
                        90 - (float_coordinates[1] if float_coordinates[1] > 0 else -float_coordinates[1])]
        self.map_params = {
            "ll": ",".join(self.coordinates),
            "spn": ','.join(self.deltas),
            'size': '450,450',
            "l": "map"}
        self.update_image()

    def search_geocode(self):
        self.searchBar.clearFocus()
        self.geocoder_params['geocode'] = self.searchBar.text()
        json_response = requests.get(geocoder_api_server, params=self.geocoder_params).json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        metadata = toponym["metaDataProperty"]["GeocoderMetaData"]
        self.address = (metadata["text"],
                        metadata['Address']['postal_code'] if 'postal_code' in metadata['Address'].keys() else '(n/f)')
        self.update_statusbar()
        coodrinates = toponym["Point"]["pos"]
        self.coordinates = coodrinates.split(" ")
        float_coordinates = [float(x) for x in self.coordinates]
        self.borders = [180 - abs(float_coordinates[0]),
                        90 - abs(float_coordinates[1])]
        self.map_params['ll'] = ",".join(self.coordinates)
        self.map_params['pt'] = ",".join(self.coordinates) + ",pm2rdm"
        self.update_image()

    def click_geocode(self, lon_lat):
        self.searchBar.clearFocus()
        self.geocoder_params['geocode'] = lon_lat
        json_response = requests.get(geocoder_api_server, params=self.geocoder_params).json()
        toponym = json_response["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        metadata = toponym["metaDataProperty"]["GeocoderMetaData"]
        self.address = (metadata["text"],
                        metadata['Address']['postal_code'] if 'postal_code' in metadata['Address'].keys() else '(n/f)')
        self.update_statusbar()
        self.map_params['pt'] = lon_lat + ",pm2dbm"

    def refresh_search(self):
        if 'pt' in self.map_params.keys():
            self.map_params.pop('pt')
        self.statusBar.clearMessage()
        self.address = ('', '')
        self.update_image()

    def update_statusbar(self):
        if self.mailBox.isChecked():
            self.statusBar.showMessage(' '.join(self.address))
        else:
            self.statusBar.showMessage(self.address[0])

    def change_mode(self):
        self.map_params['l'] = modes[self.modeBox.currentText()]
        self.update_image()

    def get_image(self):
        response = requests.get(map_api_server, params=self.map_params)
        if not response:
            print("Ошибка выполнения запроса:")
            print(self.map_params)
            print("Http статус:", response.status_code, "(", response.reason, ")")
        # self.current_img = ImageQt(Image.open(BytesIO(response.content)))
        # return self.current_img
        return ImageQt(Image.open(BytesIO(response.content))).copy()

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
        self.borders = [180 - abs(float_coordinates[0]),
                        90 - abs(float_coordinates[1])]
        self.update_image()

    def change_zoom(self, plus):
        for i in range(2):
            self.deltas[i] = str(max(float(self.deltas[i]) * (2 if plus else 0.5), 0.00125 / (i + 1)))[:7]
        if float(self.deltas[0]) >= self.borders[0]:
            self.deltas = [str(round(self.borders[0], 8)), str(round(self.borders[0] / 2, 8))]
            self.lon_deformation = 1.19
        elif float(self.deltas[1]) >= self.borders[1]:
            self.deltas = [str(round(self.borders[1] * 2, 8)), str(round(self.borders[1], 8))]
            self.lon_deformation = 1.19
        self.map_params['spn'] = ','.join(self.deltas)
        self.update_image()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and 39 < event.y() < 491:
            x, y = event.x(), event.y() - 40
            lat_deformation = 3.9 + (abs(round(float(self.coordinates[1]), 8))
                                     ** 2) * (-0.0006 + abs(float(self.coordinates[1][:3])) / 1200000)
            shift = (round((x - 225) / 450 * float(self.deltas[0]), 8) * self.lon_deformation,
                     round(-(y - 225) / 450 * float(self.deltas[1]) * lat_deformation, 8))
            pt_coordinates = [str(round(float(self.coordinates[i]) + shift[i], 10)) for i in range(2)]
            self.click_geocode(','.join(pt_coordinates))
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