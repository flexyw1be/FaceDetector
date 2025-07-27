import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QVBoxLayout,
                             QWidget, QPushButton, QFileDialog, QSlider)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap


class FaceDetectionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Detection Tester")
        self.setGeometry(100, 100, 800, 600)

        # Загрузка модели детекции лиц
        self.face_net = cv2.dnn.readNet(
            "ml_models/opencv_face_detector_uint8.pb",
            "ml_models/opencv_face_detector.pbtxt"
        )

        # Инициализация UI
        self.initUI()

        # Переменные для хранения изображения
        self.image = None
        self.detected_image = None
        self.conf_threshold = 0.5

    def initUI(self):
        # Основной виджет и layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Виджет для отображения изображения
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image_label)

        # Кнопка для загрузки изображения
        self.load_button = QPushButton("Загрузить изображение")
        self.load_button.clicked.connect(self.load_image)
        layout.addWidget(self.load_button)

        # Слайдер для настройки порога уверенности
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setRange(10, 90)
        self.threshold_slider.setValue(50)
        self.threshold_slider.valueChanged.connect(self.update_threshold)
        layout.addWidget(QLabel("Порог уверенности (0.1-0.9):"))
        layout.addWidget(self.threshold_slider)

        # Кнопка для детекции лиц
        self.detect_button = QPushButton("Обнаружить лица")
        self.detect_button.clicked.connect(self.detect_faces)
        layout.addWidget(self.detect_button)

        central_widget.setLayout(layout)

    def load_image(self):
        # Диалог выбора файла
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )

        if file_name:
            # Загрузка изображения
            self.image = cv2.imread(file_name)
            self.show_image(self.image)

    def update_threshold(self, value):
        # Обновление порога уверенности (0.1-0.9)
        self.conf_threshold = value / 100
        if self.image is not None:
            self.detect_faces()

    def detect_faces(self):
        if self.image is not None:
            # Копируем изображение для рисования рамок
            frame = self.image.copy()

            # Вызываем функцию highlight_face
            boxes = self.highlight_face(self.face_net, frame, self.conf_threshold)

            # Рисуем рамки вокруг обнаруженных лиц
            for (x1, y1, x2, y2) in boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Добавляем текст с уверенностью
                cv2.putText(frame, f"Face: {self.conf_threshold:.2f}",
                            (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 255, 0), 1)

            self.detected_image = frame
            self.show_image(frame)

            # Выводим информацию в консоль
            print(f"Обнаружено лиц: {len(boxes)} с порогом {self.conf_threshold:.2f}")

    def highlight_face(self, net, frame, conf_threshold=0.5):
        """Функция детекции лиц (как в вашем коде)"""
        if net is None:
            return []
        try:
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123], False, False)
            net.setInput(blob)
            detections = net.forward()
            boxes = []
            for i in range(detections.shape[2]):
                conf = detections[0, 0, i, 2]
                if conf > conf_threshold:
                    x1 = int(detections[0, 0, i, 3] * w)
                    y1 = int(detections[0, 0, i, 4] * h)
                    x2 = int(detections[0, 0, i, 5] * w)
                    y2 = int(detections[0, 0, i, 6] * h)
                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(w, x2)
                    y2 = min(h, y2)
                    if x2 > x1 and y2 > y1:
                        boxes.append([x1, y1, x2, y2])
            return boxes
        except Exception as e:
            print(f"Ошибка в highlight_face: {e}")
            return []

    def show_image(self, image):
        # Конвертируем изображение из BGR (OpenCV) в RGB (Qt)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Масштабируем изображение под размер виджета
        scaled_image = qt_image.scaled(
            self.image_label.width(),
            self.image_label.height(),
            Qt.KeepAspectRatio
        )

        self.image_label.setPixmap(QPixmap.fromImage(scaled_image))

    def resizeEvent(self, event):
        # При изменении размера окна обновляем изображение
        if self.detected_image is not None:
            self.show_image(self.detected_image)
        elif self.image is not None:
            self.show_image(self.image)
        super().resizeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FaceDetectionApp()
    window.show()
    sys.exit(app.exec_())