import pyautogui
from pyscreeze import Box

import Common


def FindCoordinates():
    print("Enter this link: https://www.improvememory.org/simple-games/stack-tower/ and don't click anything")
    print("Press 's' when ready to take the screenshot")

    while Common.key_option != "s":
        pass

    gameWindow: Box = None

    print("Display size: ", pyautogui.size())
    display_width, display_height = pyautogui.size()
    center_width = display_width // 2
    center_height = display_height // 2
    print("Display center: ", center_width, center_height)

    screenshotImg = pyautogui.screenshot()
    center_pixel = screenshotImg.getpixel((center_width, center_height))

    if center_pixel == Common.COLOR_BACKGROUND:
        print("found in center... will expand now")
        # Left
        x_left = center_width
        while screenshotImg.getpixel((x_left, center_height)) != Common.COLOR_WHITE:
            x_left -= 1
        print("left: ", x_left)
        # Top
        y_top = center_height
        while screenshotImg.getpixel((center_width, y_top)) != Common.COLOR_WHITE:
            y_top -= 1
        print("top: ", y_top)
        # right
        x_right = center_width
        while screenshotImg.getpixel((x_right, center_height)) != Common.COLOR_WHITE:
            x_right += 1
        print("right: ", x_right)
        # down
        y_down = center_height
        while screenshotImg.getpixel((center_width, y_down)) != Common.COLOR_WHITE:
            y_down += 1
        print("down: ", y_down)

        #game box
        gameWindow = Box(x_left, y_top,
                         x_right - x_left, y_down - y_top)

        pyautogui.screenshot(
            "data/runtime_img/gameWindow.png", region=gameWindow)
    else:
        print("Not found in center... will try somewhere else")

    if gameWindow:
        print("Found the window box. Writing to file.")
        file = open(Common.WINDOW_COORDINATES_TXT, "w")
        file.write(','.join(map(str, gameWindow)))
        file.close()
    else:
        print("Could not find the game window")


if __name__ == '__main__':
    Common.initialize_keyboard_listener()
    FindCoordinates()
