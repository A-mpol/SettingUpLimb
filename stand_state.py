import cv2
import keyboard
import numpy as np

import matplotlib.pyplot as plt

from WorkingWithDrive import Drive

import pyautogui
import pygetwindow


class Stand:
    def __init__(self, camera):
        self.drive = Drive()
        self.is_drive_connected = self.drive.connected()
        self.setting_drive()

        self.video = cv2.VideoCapture(camera)

        first_image, fx, fy = self.setting_first_image()
        self.top_border, self.lower_border = self.get_coordinates_of_selected_area(first_image, fx, fy)
        self.x = (self.top_border[0] + self.lower_border[0]) // 2

        self.list_y = []
        self.drive_positions = []

        self.y_min, self.y_max = -1, -1

        self.state = "обычное"

    def setting_first_image(self):
        while True:
            first_image = self.get_image()
            cv2.imshow('Video', first_image)
            if cv2.waitKey(1) & 0xFF == 27:  # Нажатие клавиши Esc
                cv2.destroyAllWindows()
                break
        height, width = first_image.shape[:2]
        screen_width, screen_height = pyautogui.size()
        if height > screen_height or width > screen_width:
            resized_image = cv2.resize(first_image, None, fx=(screen_width / width), fy=(screen_height / height),
                                       interpolation=cv2.INTER_LINEAR)
            return resized_image, (screen_width / width), (screen_height / height)
        return first_image, 1, 1

    def setting_drive(self):
        if self.is_drive_connected:
            self.drive.turn_on()
            self.drive.change_speed(100)

    def get_image(self):
        try:
            success, image = self.video.read()
            if success:
                return image
            return []
        except:
            print("Кадр не считывается")

    def get_coordinates_of_selected_area(self, image, fx, fy):
        x1, y1, x2, y2 = -1, -1, -1, -1
        draw = False

        def get_mouse_position(event, x, y, flags, param):
            nonlocal x1, y1, x2, y2, draw

            if event == cv2.EVENT_LBUTTONDOWN:
                x1, y1 = x, y
                draw = True

            if event == cv2.EVENT_MOUSEMOVE:
                if draw:
                    img = image.copy()
                    cv2.rectangle(img, (x1, y1), (x, y), (0, 255, 0), 2)
                    cv2.imshow('image', img)

            if event == cv2.EVENT_LBUTTONUP:
                x2, y2 = x, y
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                draw = False

        cv2.namedWindow('image')
        cv2.setMouseCallback('image', get_mouse_position)

        while True:
            cv2.imshow('image', image)
            if cv2.waitKey(1000) & 0xFF == 27:  # выход по нажатию Esc
                break

        cv2.destroyAllWindows()
        if all([h != -1 for h in [x1, x2, y1, y2]]):
            x1 = int(x1 / fx)
            x2 = int(x2 / fx)
            y1 = int(y1 / fy)
            y2 = int(y2 / fy)
            return (x1, y1), (x2, y2)
        print("Область не выделена")
        return (0, 0), (image.size[1] - 1, image.size[0] - 1)

    # Работа с кадрами
    def get_image_contours(self, image):
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur_image = cv2.medianBlur(gray_image, 5)
        binary_image = cv2.adaptiveThreshold(blur_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 11, 5)
        contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) == 0:
            print("Контуров не обнаружено")
            return []
        image_contours = np.uint8(np.zeros((binary_image.shape[0], binary_image.shape[1])))
        for contour in contours:
            image_contours = cv2.drawContours(image_contours, [contour], -1, (255, 255, 255), 1)
        return image_contours

    def get_y_coordinate(self, bw_image):
        for y in range(self.top_border[1], self.lower_border[1]):
            pixel = bw_image[y][self.x]
            if pixel == 255 and bw_image[y + 1][self.x] == 0:
                is_it_white_line = True
                for i in range(100):
                    if bw_image[y][self.x + i] == 255 and bw_image[y + 1][self.x + i] == 255 \
                            and bw_image[y - 1][self.x + i] == 255:
                        is_it_white_line = False
                        break
                if not is_it_white_line:
                    continue
                return y
        print("Координата y не обнаружена")
        return -1

    def draw_point(self, image, y):
        img_copy = image.copy()
        cv2.circle(img_copy, (self.x, y), 1, (200, 255, 255), -1)
        return img_copy

    def draw_lines(self, image, y_min, y_max):
        img_copy = image.copy()
        if y_min != -1:
            cv2.line(img_copy, (0, y_min), (image.shape[1], y_min), (255, 255, 0), 1)
        if y_max != -1:
            cv2.line(img_copy, (0, y_max), (image.shape[1], y_max), (0, 255, 255), 1)
        if self.state == "обработка" or self.state == "настройка лимба":
            y_medium = (y_max + y_min) // 2
            cv2.line(img_copy, (0, y_medium), (image.shape[1], y_medium), (255, 0, 255), 1)
        return img_copy

    def get_min_and_max_y(self):
        list_y_copy = list(set(self.list_y))
        list_y_copy.sort()

        if len(list_y_copy) == 0:
            print("Список значений Y пуст")
            return -1, -1

        if len(list_y_copy) == 1:
            return list_y_copy[0], list_y_copy[0]

        if len(list_y_copy) == 2:
            return list_y_copy[0], list_y_copy[1]

        maximum = -1
        minimum = -1
        MAX_DIFFERENCE = 10

        for i in range(len(list_y_copy) - 1, 1, -1):
            if list_y_copy[i] - list_y_copy[i - 1] < MAX_DIFFERENCE:
                maximum = list_y_copy[i]
                break

        for j in range(len(list_y_copy) - 1):
            if list_y_copy[j + 1] - list_y_copy[j] < MAX_DIFFERENCE:
                minimum = list_y_copy[j]
                break

        if minimum == -1 or maximum == -1:
            print(list_y_copy)

        return minimum, maximum

    # Работа с состояниями
    def get_image_in_normal_state(self):
        image = self.get_image()
        if len(image) == 0:
            return []
        image_contours = self.get_image_contours(image)
        y = self.get_y_coordinate(image_contours)
        if y != -1:
            image_with_point = self.draw_point(image, y)
            return image_with_point
        return image

    def get_image_in_collection_state(self):
        if self.is_drive_connected:
            drive_position = self.drive.encoder_position
            if drive_position == -1:
                return [-1]
        image = self.get_image()
        if len(image) == 0:
            return []
        image_contours = self.get_image_contours(image)
        y = self.get_y_coordinate(image_contours)
        if y != -1:
            if self.is_drive_connected:
                self.drive_positions.append(drive_position)
            self.list_y.append(y)
            image_with_point = self.draw_point(image, y)
            y_min, y_max = self.get_min_and_max_y()
            image_with_lines = self.draw_lines(image_with_point, y_min, y_max)
            return image_with_lines
        y_min, y_max = self.get_min_and_max_y()
        image_with_lines = self.draw_lines(image, y_min, y_max)
        return image_with_lines

    def get_image_in_processing_state(self):
        image = self.get_image()
        if len(image) == 0:
            return []
        image_contours = self.get_image_contours(image)
        y = self.get_y_coordinate(image_contours)
        if y != -1:
            image_with_point = self.draw_point(image, y)
            image_with_lines = self.draw_lines(image_with_point, self.y_min, self.y_max)
            return image_with_lines
        image_with_lines = self.draw_lines(image, self.y_min, self.y_max)
        return image_with_lines

    def check_window(self):
        try:
            all_windows = pyautogui.getActiveWindowTitle()
            if all_windows == "video" or all_windows == "Figure 1":
                return True
            else:
                return False
        except:
            try:
                all_windows = pygetwindow.getAllTitles()
                if "Python video" in all_windows or "Python Figure 1" in all_windows:
                    return True
            except:
                return False

    def on_key_event(self):
        is_open = self.check_window()
        if is_open and (not self.is_drive_connected or self.drive.in_position):
            if self.state == "обычное":
                self.state = "сбор данных"
            elif self.state == "сбор данных":
                self.y_min, self.y_max = self.get_min_and_max_y()
                self.state = "обработка"
            elif self.state == "обработка" and self.is_drive_connected:
                self.state = "выход в позицию"
            else:
                self.list_y.clear()
                self.drive_positions.clear()
                self.y_min, self.y_max = -1, -1
                self.state = "обычное"

    # Отображение кадров
    def show_image(self, image, position):
        font = cv2.FONT_HERSHEY_COMPLEX
        font_scale = 1
        font_thickness = 2
        if self.state == "обработка" or self.state == "настройка лимба":
            cropped_image = image[self.y_min - 3:self.y_max + 3, self.top_border[0]: self.lower_border[0]]
        else:
            cropped_image = image[self.top_border[1]:self.lower_border[1], self.top_border[0]: self.lower_border[0]]
        height, width = cropped_image.shape[:2]
        screen_width, screen_height = pyautogui.size()
        print(height, width, screen_width, screen_height)
        resized_image = cv2.resize(cropped_image, None, fx=(screen_width // width), fy=(screen_height // height),
                                   interpolation=cv2.INTER_LINEAR)
        cv2.putText(resized_image, self.state, (10, 25), font, font_scale, (255, 0, 0), font_thickness, cv2.LINE_AA)
        cv2.putText(resized_image, position, (resized_image.shape[1] - 200, 25), font, font_scale, (255, 0, 0),
                    font_thickness, cv2.LINE_AA)
        cv2.imshow("video", resized_image)

    # Отображение графика
    def get_data_processing_for_graph(self):
        processed_list_y = []
        difference = self.list_y[0]
        for i in range(len(self.list_y)):
            processed_list_y.append((self.list_y[i] - difference) * -1)

        if self.is_drive_connected:
            degrees_per_pulse = 360 / 20000
            difference = self.drive_positions[0]
            processed_drive_positions = []
            for j in range(len(self.drive_positions)):
                processed_drive_positions.append(int((self.drive_positions[j] - difference) * degrees_per_pulse))
            return processed_list_y, processed_drive_positions

        return processed_list_y

    def open_close_plot(self):
        try:
            if len(plt.get_fignums()) == 0 and self.state == "обработка":
                if self.is_drive_connected and len(self.drive_positions) == len(self.list_y):
                    processed_list_y, processed_drive_positions = self.get_data_processing_for_graph()
                    plt.plot(processed_drive_positions, processed_list_y)
                else:
                    processed_list_y = self.get_data_processing_for_graph()
                    plt.plot(processed_list_y)
                plt.show(block=False)
                plt.pause(0.5)
            elif (self.state == "обычное" or self.state == "выход в позицию") and len(plt.get_fignums()) == 1:
                plt.close()
        except:
            print("Проблема с графиком")

    def event_handling_without_drive(self):
        keyboard.add_hotkey('space', self.on_key_event)
        while True:
            if self.state == "сбор данных":
                image = self.get_image_in_collection_state()
            elif self.state == "обработка":
                self.open_close_plot()
                image = self.get_image_in_processing_state()
            elif self.state == "обычное":
                self.open_close_plot()
                image = self.get_image_in_normal_state()
            if len(image) == 0:
                print("Обработка видео окончена")
                break
            self.show_image(image, str(len(self.list_y)))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    def event_handling_with_drive(self):
        one_turn = 20000 * 10
        keyboard.add_hotkey('space', self.on_key_event)
        while True:
            if self.state == "сбор данных":
                self.drive.move_to_position(self.drive.encoder_position + one_turn)
                while not self.drive.in_position:
                    img = self.get_image_in_collection_state()
                    if len(img) == 0:
                        print("Обработка видео окончена")
                        break
                    self.show_image(img, str(self.drive.encoder_position))
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                self.state = "обработка"
                self.y_min, self.y_max = self.get_min_and_max_y()

            if self.state == "обработка" or self.state == "настройка лимба":
                self.open_close_plot()
                img = self.get_image_in_processing_state()
                if len(img) == 0:
                    print("Обработка видео окончена")
                    break
                self.show_image(img, str(self.drive.encoder_position))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            if self.state == "выход в позицию":
                self.open_close_plot()
                required_position = -1
                for i in range(len(self.drive_positions)):
                    if self.list_y[i] == self.y_max:
                        required_position = self.drive_positions[i]
                        break
                if required_position == -1:
                    print("Необходимой позици нет")
                    self.state = "настройка лимба"
                    continue
                self.drive.move_to_position(required_position)
                while not self.drive.in_position:
                    img = self.get_image_in_processing_state()
                    if len(img) == 0:
                        print("Обработка видео окончена")
                        break
                    self.show_image(img, str(self.drive.encoder_position))
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                img = self.get_image_in_processing_state()
                if len(img) == 0:
                    self.state = "настройка лимба"
                    continue
                self.show_image(img, str(self.drive.encoder_position))
                self.state = "настройка лимба"

            if self.state == "обычное":
                img = self.get_image_in_normal_state()
                if len(img) == 0:
                    print("Обработка видео окончена")
                    break
                self.show_image(img, str(self.drive.encoder_position))
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

    def event_handling(self):
        if not self.is_drive_connected:
            self.event_handling_without_drive()
        else:
            self.event_handling_with_drive()
            self.drive.switch_off()
        self.video.release()


stand = Stand(0)
stand.event_handling()
cv2.destroyAllWindows()
