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
            print(max(self.measurements), min(self.measurements))

    def get_starting_position(self):
        return 0

    def get_current_position(self):
        return len(self.measurements) - 1


class Shot:
    def __init__(self, image):
        self.last_coordinate = 0
        self.image = image

    def image_processing(self):
        gaussian_image = cv2.GaussianBlur(self.image, ksize=(5, 5), sigmaX=0, sigmaY=0)

        sharp_filter = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])

        sharpen_img = cv2.filter2D(gaussian_image, ddepth=-1, kernel=sharp_filter)

        grayscale_image = cv2.cvtColor(sharpen_img, cv2.COLOR_BGR2GRAY)

        _, binary_image = cv2.threshold(grayscale_image, 87, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        img_contours = np.uint8(np.zeros((binary_image.shape[0], binary_image.shape[1])))

        for contour in contours:
            if 200 < len(contour) < 1500:
                img_contours = cv2.drawContours(img_contours, [contour], -1, (255, 255, 255), 2)

        return img_contours

    def get_y_coordinate(self):
        bw_image = self.image_processing()
        x = (bw_image.shape[1] // 3) * 2

        height = bw_image.shape[0]

        for y in range(50, height - 50):
            pixel = bw_image[y][x]
            if pixel == 255 and bw_image[y + 1][x] == 0:

                is_it_white_line = True
                for i in range(100):
                    if bw_image[y][x + i] == 255 and bw_image[y + 1][x + i] == 255 and bw_image[y - 1][x + i] == 255 \
                            and bw_image[y + 2][x + i] == 255 and bw_image[y - 2][x + i] == 255:
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
        x = (self.image.shape[1] // 3) * 2
        cv2.circle(img_copy, (x, y), 2, (0, 255, 0), -1)
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
    setting_up_limb("Video.mp4")
