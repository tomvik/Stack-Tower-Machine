from math import atan2, pi
from cv2 import sqrt
import numpy as np
import cv2
import pyautogui
from pyscreeze import Box, Point
import time

import Common

screenshots_taken = 0
sample_size = 2
file_name = "data/runtime_img/2{}.png"
delta_file_name = "data/runtime_img/2.txt"
save_data = True
global_debug = True
take_screenshot = True


def GetGameWindow() -> Box:
    print("Reading the coordinates")
    file = open(Common.WINDOW_COORDINATES_TXT, "r")
    line = file.readline()
    raw_game_window = tuple(map(int, line.split(',')))
    game_height_fix = 85
    game_window: Box = Box(
        raw_game_window[0], raw_game_window[1] + game_height_fix, raw_game_window[2], raw_game_window[3] - game_height_fix)
    return game_window


def WriteImagesAndTimes(color_images, deltas_times):
    for i in range(len(color_images)):
        cv2.imwrite(file_name.format(i), color_images[i])
        file = open(delta_file_name, "w")
        file.write(",".join(map(str, deltas_times)))
        file.close()


def GetTimes():
    file = open(delta_file_name, "r")

    line = file.readline()
    times = list(map(float, line.split(',')))

    file.close()

    return times


def ShowImg(window_title, img):
    cv2.imshow(window_title, img)
    cv2.waitKey()


def BlurImg(input_img, debug=False):
    global screenshots_taken

    img = input_img.copy()
    if debug:
        ShowImg("BlurImg - Before Blur {}".format(screenshots_taken), img)

    img = cv2.GaussianBlur(img, (5, 5), cv2.BORDER_DEFAULT)

    if debug:
        ShowImg("BlurImg - After Blur {}".format(screenshots_taken), img)

    return img


def RemoveBackground(color_img, threshold, debug=False):
    global screenshots_taken

    color_img = BlurImg(color_img, debug)
    gray_img = cv2.cvtColor(np.array(color_img), cv2.COLOR_RGB2GRAY)
    (_, black_and_white_img) = cv2.threshold(
        gray_img, threshold, 255, cv2.THRESH_BINARY_INV)
    if debug:
        ShowImg("RemoveBackground - GrayImg {}".format(screenshots_taken), gray_img)
        ShowImg("RemoveBackground - BnW {}".format(screenshots_taken), black_and_white_img)
    return cv2.bitwise_and(gray_img, gray_img, mask=black_and_white_img)


def GetScreenshotWithoutBackground(game_window, debug=False, from_storage=False):
    global screenshots_taken
    global file_name
    original_screenshot = None
    local_file_name = file_name.format(screenshots_taken)
    screenshots_taken += 1

    if debug:
        if from_storage:
            original_screenshot = cv2.imread(local_file_name)
        else:
            original_screenshot = np.array(pyautogui.screenshot(
                local_file_name, region=game_window))
    else:
        if from_storage:
            original_screenshot = cv2.imread(local_file_name)
        else:
            original_screenshot = np.array(
                pyautogui.screenshot(region=game_window))

    gray_screenshot = RemoveBackground(
        original_screenshot.copy(), 205, debug)

    if debug:
        ShowImg("GetScreenshotWithoutBackground - With Background {}".format(
            screenshots_taken), original_screenshot)
        ShowImg("GetScreenshotWithoutBackground - Without Background Gray {}".format(
            screenshots_taken), gray_screenshot)

    return gray_screenshot.copy(), original_screenshot.copy()


def DrawContoursOnGray(gray_img, contours):
    result = None
    if len(contours):
        color_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2BGR)
        result = cv2.drawContours(
            color_img, contours, -1, (0, 255, 0), 5)

    return result.copy()


# Gotten from https://www.pyimagesearch.com/2021/10/06/opencv-contour-approximation/
def ApproximateContours(gray_img, contours, eps, debug=False):
    global screenshots_taken

    approximations = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, eps * perimeter, True)

        if debug:
            text = "eps={:.4f}, num_pts={}".format(eps, len(approx))
            print("[INFO] {}".format(text))

        approximations.append(approx)

    if debug:
        output = DrawContoursOnGray(gray_img, approximations)
        ShowImg("ApproiximateContours - Approximated Contour {}".format(screenshots_taken), output)

    return approximations


def InteractiveApproximateContours(grayImg, contours):
    for eps in np.linspace(0.001, 0.01, 10):
        ApproximateContours(grayImg, contours, eps, True)


def ApproximateAnglesFromContours(contours, debug=False):
    if debug:
        print("ApproximateAnglesFromContours - contours", contours)

    all_angles = []
    for index_contour, contour in enumerate(contours):
        if debug:
            print("ApproximateAnglesFromContours - contour {}".format(index_contour), contour)

        single_angles = []
        for index_point in range(len(contour) - 1):
            first_point = contour[index_point][0]
            second_point = contour[index_point + 1][0]

            if debug:
                print("ApproximateAnglesFromContours - {} pair of points".format(index_point), first_point, second_point)


            angle = atan2( (second_point[1] - first_point[1]), (second_point[0] - first_point[0]) )
            angle = angle * 180 / pi
            if angle < 0:
                angle = 360 + angle

            if debug:
                print("ApproximateAnglesFromContours - angle", angle)
            single_angles.append(angle)            

        
        angle = atan2( (contour[-1][0][1] - contour[0][0][1]), (contour[-1][0][0] - contour[0][0][0]) )
        angle = angle * 180 / pi
        if angle < 0:
            angle = 360 + angle

        if debug:
            print("ApproximateAnglesFromContours - angle", angle)
        single_angles.append(angle)            
        

        all_angles.append(single_angles.copy())        

    return all_angles


def GetContours(gray_img, debug=False):
    contours, hierarchy = cv2.findContours(
        gray_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

    contours = ApproximateContours(gray_img, contours, Common.EPSILON, debug)

    angles = ApproximateAnglesFromContours(contours, debug)

    # 1 contour = both merged
    # 2 contours = base and new one
    result = DrawContoursOnGray(gray_img, contours)

    if debug:
        print("Contours found: ", len(contours[0]))
        ShowImg("With contours {}".format(screenshots_taken), result)
        print("Angles ", angles)

    return contours, result.copy()


def PlayGame():
    global global_debug
    global save_data
    global take_screenshot
    global sample_size

    print("Press p to play")

    while Common.key_option != "p":
        pass

    game_window = GetGameWindow()

    print("Will begin playing the game")

    color_images = list()
    deltas_times = list()
    gray_images = list()
    images_with_contours = list()
    contours_of_images = list()

    for _ in range(sample_size):
        start_time = time.time()
        gray_image, color_image = GetScreenshotWithoutBackground(
            game_window, global_debug, not take_screenshot)

        color_images.append(color_image.copy())
        gray_images.append(gray_image.copy())

        contours, screenshot = GetContours(gray_image, global_debug)
        images_with_contours.append(screenshot.copy())
        contours_of_images.append(contours)

        end_time = time.time()
        delta_time = end_time - start_time
        deltas_times.append(delta_time)

    if save_data:
        WriteImagesAndTimes(color_images, deltas_times)
    if not take_screenshot:
        deltas_times = GetTimes()

    for i in range(sample_size - 1):
        first_contour = contours_of_images[i]
        second_contour = contours_of_images[i + 1]
        print("For image", i)
        print("Contours", first_contour)
        print("Amount of contours", len(first_contour))
        print("For image", i + 1)
        print("Contours", second_contour)
        print("Amount of contours", len(second_contour))
        print("Delta time:", deltas_times[i])
        # If there's a distance delta, that's the one.
        # If there's a shape delta, that may be the one?
        first_image = images_with_contours[i].copy()
        filtered_contours = []
        if len(first_contour) == len(second_contour):
            colors = [(255, 0, 0), (0, 0, 255), (255, 255, 255),
                      (255, 0, 255), (255, 255, 0), (0, 255, 255)]
            for j in range(len(first_contour)):
                # distance = cv2.cv.ShapeDistanceExtractor.computeDistance(
                #     firstContour[j], secondContour[j])
                simmilarity = cv2.matchShapes(
                    first_contour[j], second_contour[j], cv2.CONTOURS_MATCH_I1, 0)
                # print("Distance between contours", j, "is", distance)
                print("Sim between contours", j, "is", simmilarity)
                if simmilarity == 0.0:
                    first_image = cv2.drawContours(
                        first_image, second_contour[j], -1, (0, 255, 0), 5)
                else:
                    filtered_contours.append(second_contour[j])
            if len(filtered_contours):
                print(len(filtered_contours))
                first_image = cv2.drawContours(
                    first_image, filtered_contours, -1, (0, 0, 255), 5)

        else:
            first_image = cv2.drawContours(
                first_image, second_contour, -1, (255, 0, 0), 5)
        ShowImg("img with two contours", first_image)

        # InteractiveApproximateContours(originalImages[i], contoursOfImages[i])

    return

if __name__ == "__main__":
    Common.key_option = "p"
    PlayGame()
