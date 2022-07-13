from math import atan2, dist, pi, cos, sin
from cv2 import sqrt
import numpy as np
import cv2
import pyautogui
from pyscreeze import Box, Point
import time

import Common

screenshots_taken = 0
sample_size = 18
file_name = "data/runtime_img/6{}.png"
delta_file_name = "data/runtime_img/6.txt"
save_data = False
global_debug = False
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


def GetAngleBetweenTwoPoints(first_point, second_point):
    # Multiply by -1 because we're in the fourth quadrant.
    angle = atan2( (second_point[1] - first_point[1]), (second_point[0] - first_point[0]) ) * -1
    angle = angle * 180 / pi

    if angle <= 0:
        angle = 360 + angle
    if angle == 360:
        angle = 0

    return angle


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

            angle = GetAngleBetweenTwoPoints(first_point, second_point)

            if debug:
                print("ApproximateAnglesFromContours - angle", angle)
            single_angles.append(angle)            

        
        angle = GetAngleBetweenTwoPoints(contour[-1][0], contour[0][0])

        if debug:
            print("ApproximateAnglesFromContours - angle", angle)
        single_angles.append(angle)            
        

        all_angles.append(single_angles.copy())        

    #90, 270, 150, 330, 30, 210 - important angles

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

    return contours, angles, result.copy()

def IsAngleStraight(angle: float) -> bool:
    angle_dif = 10
    if angle <= 90 + angle_dif and angle >= 90 - angle_dif:
        return True
    elif angle <= 270 + angle_dif and angle >= 270 - angle_dif:
        return True
    return False

def IsAngleMovewise(angle: float) -> bool:
    angle_dif = 10
    if angle <= 30 + angle_dif and angle >= 30 - angle_dif:
        return True
    if angle <= 210 + angle_dif and angle >= 210 - angle_dif:
        return True
    return False

def GetImportantPointsAndAnglesFromImage(contours, angles):
    important_points_of_image = list()
    important_angles_of_image = list()

    for contours_idx in range(len(contours)):
        for point_idx in range(len(contours[contours_idx])):
            point = contours[contours_idx][point_idx][0]
            angle = angles[contours_idx][point_idx]

            if IsAngleStraight(angle):
                important_points_of_image.append(point)
                important_angles_of_image.append(angle)

    return important_points_of_image, important_angles_of_image

def GetImportantPointsAndAngles(contours_of_images, angles_of_images):
    global sample_size

    important_points_of_images = list()
    important_angles_of_images = list()

    for i in range(sample_size):
        contours = contours_of_images[i]
        angles = angles_of_images[i]

        important_points_of_image, important_angles_of_image = GetImportantPointsAndAnglesFromImage(contours, angles)

        important_points_of_images.append(important_points_of_image.copy())
        important_angles_of_images.append(important_angles_of_image.copy())

    return important_points_of_images.copy(), important_angles_of_images.copy()


def GetClosestPointWithAngle(set_of_points, anchor_point):
    closest_point = list()
    closest_distance = 1000
    for point in set_of_points:
        distance = dist(anchor_point, point)
        if closest_distance > distance:
            closest_distance = distance
            closest_point = point

    angle = GetAngleBetweenTwoPoints(anchor_point, closest_point)

    return closest_point, closest_distance, angle


def GetDeltaVectorsFromTwoImages(first_points, second_points):
    distances = list()
    angles = list()
    for point_idx in range(len(first_points)):
        first_point = first_points[point_idx]
        second_point, distance, angle = GetClosestPointWithAngle(second_points, first_point)

        if distance < 20:
            distances.append(distance)
            angles.append(angle)
        else:
            distances.append(0)
            angles.append(0)

    return distances, angles


def GetPointFromDistanceAndAngle(point, distance, angle):
    radians = angle * pi / 180

    x = point[0] + (distance * cos(radians))
    y = point[1] + (distance * sin(radians) * -1)

    return Point(int(x), int(y))


def GetVelocityFromImages(point_deltas, angles_deltas, times_delta):
    all_velocities = list()

    for image_idx in range(len(point_deltas)):
        distances = point_deltas[image_idx]
        angles = angles_deltas[image_idx]
        time_delta = times_delta[image_idx]

        individual_velocity = list()
        for point_idx in range(len(distances)):
            distance = distances[point_idx]
            angle = angles[point_idx]

            individual_velocity.append( (distance * cos(angle * pi / 180) ) / time_delta)            

        all_velocities.append(individual_velocity.copy())

    return all_velocities

def GetAverageVelocityFromImages(velocities):
    approx_vel = 0
    invalid_all_count = 0

    for velocities_img in velocities:
        invalid_count = 0
        accum_vel = 0

        for velocity in velocities_img:
            if velocity == 0:
                invalid_count += 1
            accum_vel += velocity

        if invalid_count == len(velocities_img):
            invalid_all_count += 1
        else:
            accum_vel /= len(velocities_img) - invalid_count

        approx_vel += accum_vel
    
    approx_vel /= len(velocities) - invalid_all_count

    return approx_vel

def GetLeftAndRightMostPoints(points):
    left_most_point = points[0]
    right_most_point = points[-1]

    for point in points:
        if point[0] < left_most_point[0]:
            left_most_point = point
        if point[0] > right_most_point[0]:
            right_most_point = point

    return left_most_point, right_most_point

# 194 and 407 are the important x goals
def IsPointLeftTarget(point):
    dif = 5
    if point[0] <= 194 + dif and point[0] >= 194 - dif:
        return True
    return False

def IsPointRightTarget(point):
    dif = 5
    if point[0] <= 407 + dif and point[0] >= 407 - dif:
        return True
    return False

def ApproximateTimeToClick(velocities, last_points):
    approx_time = 0
    approx_vel = GetAverageVelocityFromImages(velocities)

    print("approx_vel", approx_vel)
    print("last points", last_points)

    left_most_point, right_most_point = GetLeftAndRightMostPoints(last_points)

    print("left", left_most_point)
    print("right", right_most_point)

    if IsPointLeftTarget(left_most_point):
        # have to reach 407 from right
        approx_time = (right_most_point[0] - 400) / approx_vel
    elif IsPointRightTarget(right_most_point):
        approx_time = (195 - left_most_point[0]) / approx_vel

    print("approx_time", approx_time)

    return abs(approx_time)
                


def PlayGame():
    global global_debug
    global save_data
    global screenshots_taken
    global take_screenshot
    global sample_size

    print("Press p to play")

    while Common.key_option != "p":
        pass

    game_window = GetGameWindow()
    game_center_point = pyautogui.center(game_window)

    print("Will begin playing the game")

    if take_screenshot:
        pyautogui.click(game_center_point)
        pyautogui.sleep(0.35)
    
    print("clicked screen")

    color_images = list()
    deltas_times = list()
    gray_images = list()
    images_with_contours = list()
    contours_of_images = list()
    angles_of_images = list()
    important_points_of_images = list()
    important_angles_of_images = list()
    important_points_deltas_of_images = list()
    important_angles_deltas_of_images = list()
    velocity_of_images = list()

    while Common.key_option != "q":
        screenshots_taken = 0

        for idx in range(sample_size):
            start_time = time.time()
            gray_image, color_image = GetScreenshotWithoutBackground(
                game_window, global_debug, not take_screenshot)

            color_images.append(color_image.copy())
            gray_images.append(gray_image.copy())

            contours, angles, screenshot = GetContours(gray_image, global_debug)
            images_with_contours.append(screenshot.copy())
            contours_of_images.append(contours)
            angles_of_images.append(angles)

            important_points, important_angles = GetImportantPointsAndAnglesFromImage(contours, angles)
            important_points_of_images.append(important_points)
            important_angles_of_images.append(important_angles)

            if idx > 0:
                delta_distances, delta_angles = GetDeltaVectorsFromTwoImages(
                    important_points_of_images[idx - 1],
                    important_points_of_images[idx],
                )

                important_points_deltas_of_images.append(delta_distances)
                important_angles_deltas_of_images.append(delta_angles)

            end_time = time.time()
            delta_time = end_time - start_time
            deltas_times.append(delta_time)

        if save_data:
            WriteImagesAndTimes(color_images, deltas_times)
        if not take_screenshot:
            deltas_times = GetTimes()

        velocity_of_images = GetVelocityFromImages(important_points_deltas_of_images, important_angles_deltas_of_images, deltas_times)
        time_to_click = ApproximateTimeToClick(velocity_of_images, important_points_of_images[-1])

        start_time = time.time()
        while time_to_click > time.time() - start_time:
            pass
        pyautogui.click(game_center_point)
        pyautogui.sleep(0.5)




        # image = images_with_contours[0].copy()
        # for i in range(sample_size):
        #     for point_idx in range(len(important_points_of_images[i])):
        #         point = important_points_of_images[i][point_idx]
        #         angle = important_angles_of_images[i][point_idx]
        #         try:
        #             delta_distance = important_points_deltas_of_images[i][point_idx]
        #             delta_angle = important_angles_deltas_of_images[i][point_idx]
        #             delta_velocity = velocity_of_images[i][point_idx]
        #         except:
        #             delta_distance = 0
        #             delta_angle = 0
        #             delta_velocity = 0
        #         delta_time = deltas_times[i]
        #         dest_point = GetPointFromDistanceAndAngle(point, delta_distance, delta_angle)
        #         print("i: {},\tpoint: {},\tangle: {:.2f},\tdistance to next: {:.4f},\tangle to next: {:.2f}\td time: {:.5f},\tvel: {:.2f}".format(i, point, angle, delta_distance, delta_angle, delta_time, delta_velocity))
        #         # cv2.putText(image, "{}".format(angle), point, cv2.FONT_HERSHEY_COMPLEX_SMALL, fontScale=0.5, color=(255, 255, 255))
        #         cv2.circle(image, point, 2, (0, 0, 255), -1)
        #         cv2.line(image, point, dest_point, (255,0,0), 2)
        #     print("")
        #     ShowImg("important points {}".format(i), image)





        # for i in range(sample_size - 1):
        #     first_contour = contours_of_images[i]
        #     second_contour = contours_of_images[i + 1]
        #     first_angles = angles_of_images[i]
        #     second_angles = angles_of_images[i + 1]
        #     print("For image", i)
        #     # print("Contours", first_contour)
        #     print("Amount of contours", len(first_contour))
        #     print("Angles", first_angles)
        #     print("For image", i + 1)
        #     # print("Contours", second_contour)
        #     print("Amount of contours", len(second_contour))
        #     print("Angles", second_angles)
        #     print("Delta time:", deltas_times[i])
        #     # If there's a distance delta, that's the one.
        #     # If there's a shape delta, that may be the one?
        #     first_image = images_with_contours[i].copy()
        #     filtered_contours = []
        #     if len(first_contour) == len(second_contour):
        #         for j in range(len(first_contour)):
        #             # distance = cv2.cv.ShapeDistanceExtractor.computeDistance(
        #             #     firstContour[j], secondContour[j])
        #             simmilarity = cv2.matchShapes(
        #                 first_contour[j], second_contour[j], cv2.CONTOURS_MATCH_I1, 0)
        #             # print("Distance between contours", j, "is", distance)
        #             print("Sim between contours", j, "is", simmilarity)
        #             if simmilarity == 0.0:
        #                 first_image = cv2.drawContours(
        #                     first_image, second_contour[j], -1, (0, 255, 0), 5)
        #             else:
        #                 filtered_contours.append(second_contour[j])
        #         if len(filtered_contours):
        #             print(len(filtered_contours))
        #             first_image = cv2.drawContours(
        #                 first_image, filtered_contours, -1, (0, 0, 255), 5)

        #     else:
        #         first_image = cv2.drawContours(
        #             first_image, second_contour, -1, (255, 0, 0), 5)
            
        #     if (len(first_contour) == len(second_contour)):
        #         for contours_idx in range(len(first_contour)):
        #             for contour_idx in range(len(first_contour[contours_idx])):
        #                 contour = first_contour[contours_idx][contour_idx][0]
        #                 angle = first_angles[contours_idx][contour_idx]
        #                 if IsAngleStraight(angle):
        #                     print(contour, angle)
        #                     cv2.putText(first_image, "{:.2f}".format(angle), contour, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL, fontScale=0.5, color=(255, 0, 0))
        #         for contours_idx in range(len(second_contour)):
        #             for contour_idx in range(len(second_contour[contours_idx])):
        #                 contour = second_contour[contours_idx][contour_idx][0]
        #                 angle = second_angles[contours_idx][contour_idx]
        #                 if IsAngleStraight(angle):
        #                     print(contour, angle)
        #                     cv2.putText(first_image, "{:.2f}".format(angle), contour, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL, fontScale=0.5, color=(0, 0, 255))
        #     ShowImg("img with two contours", first_image)

        #     # InteractiveApproximateContours(originalImages[i], contoursOfImages[i])

        # return

if __name__ == "__main__":
    Common.key_option = "p"
    PlayGame()
