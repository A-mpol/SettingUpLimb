import cv2
import numpy as np
import keyboard


class Limb:
    def __init__(self):
        self.engine_is_rotating = False
        self.measurements = []

    def start(self):
        self.measurements = []
        self.engine_is_rotating = True

    def stop(self):
        self.engine_is_rotating = False
        if self.measurements:
            minimum, maximum = self.coordinate_processing()
            print("Минимум:", minimum, "Максимум:", maximum)

    def get_starting_position(self):
        return 0

    def get_current_position(self):
        return len(self.measurements) - 1

    def coordinate_processing(self):
        self.measurements = sorted(list(set(self.measurements)))
        minimum = 0
        maximum = 0
        for i in range(1, len(self.measurements) - 2):
            if self.measurements[i] - self.measurements[i - 1] < 6 \
                    and self.measurements[i + 1] - self.measurements[i] < 6:
                minimum = self.measurements[i - 1]
                break
        for j in range(len(self.measurements) - 1, 1, -1):
            if self.measurements[j] - self.measurements[j - 1] < 6 \
                    and self.measurements[j - 1] - self.measurements[j - 2] < 6:
                maximum = self.measurements[j]
                break
        return minimum, maximum


class Shot:
    def __init__(self, image):
        self.last_coordinate = 0
        self.image = image
        self.x = (image.shape[1] // 3) * 2

    def image_processing(self):
        gray_frame = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)

        average_color = int(np.mean(gray_frame))

        gaussian_image = cv2.GaussianBlur(self.image, ksize=(5, 5), sigmaX=0, sigmaY=0)
        sharp_filter = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharpen_img = cv2.filter2D(gaussian_image, ddepth=-1, kernel=sharp_filter)
        grayscale_image = cv2.cvtColor(sharpen_img, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(grayscale_image, average_color, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        contour_area_size = sorted([cv2.contourArea(contour) for contour in contours if cv2.contourArea(contour) > 250],
                                   reverse=True)
        if contour_area_size:
            average_area_size = contour_area_size[0]
            for i in range(1, len(contour_area_size) - 1):
                if contour_area_size[i - 1] - contour_area_size[i] < 5000:
                    average_area_size = contour_area_size[i - 1]
                    break
        else:
            average_area_size = 10000

        img_contours = np.uint8(np.zeros((binary_image.shape[0], binary_image.shape[1])))
        for contour in contours:
            if 200 < len(contour) and cv2.contourArea(contour) <= average_area_size:
                img_contours = cv2.drawContours(img_contours, [contour], -1, (255, 255, 255), 1)

        return img_contours

    def get_y_coordinate(self):
        bw_image = self.image_processing()

        height = bw_image.shape[0]

        for y in range(50, height - 50):
            pixel = bw_image[y][self.x]
            if pixel == 255 and bw_image[y + 1][self.x] == 0:

                is_it_white_line = True
                for i in range(100):
                    if bw_image[y][self.x + i] == 255 and bw_image[y + 1][self.x + i] == 255 \
                            and bw_image[y - 1][self.x + i] == 255 and bw_image[y + 2][self.x + i] == 255 \
                            and bw_image[y - 2][self.x + i] == 255:
                        is_it_white_line = False
                        break
                if not is_it_white_line:
                    continue

                if self.last_coordinate != 0 and abs(self.last_coordinate - y) > 15:
                    continue

                self.last_coordinate = y
                return y

        tmp = self.last_coordinate
        self.last_coordinate = 0
        return tmp

    def draw(self, y):
        img_copy = self.image.copy()
        cv2.circle(img_copy, (self.x, y), 2, (0, 255, 0), -1)
        return img_copy


def setting_up_limb(camera):
    limb = Limb()

    video = cv2.VideoCapture(camera)
    keyboard.add_hotkey("s", lambda: limb.start())
    keyboard.add_hotkey("e", lambda: limb.stop())

    while True:
        success, image = video.read()
        if not success:
            break

        if limb.engine_is_rotating:
            new_img = Shot(image)
            y = new_img.get_y_coordinate()
            limb.measurements.append(y)
            image = new_img.draw(y)

        cv2.imshow("video", image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    setting_up_limb(0)
