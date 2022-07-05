import pyautogui
from pyscreeze import Box

import Common

# For this to work, there has to be the color white outside the game box.
def FindGameBoxFromAPoint(screenshot_img, center_x, center_y):
        # Left
        x_left = center_x
        while screenshot_img.getpixel((x_left, center_y)) != Common.COLOR_WHITE:
            x_left -= 1
        print("left: ", x_left)
        # Top
        y_top = center_y
        while screenshot_img.getpixel((center_x, y_top)) != Common.COLOR_WHITE:
            y_top -= 1
        print("top: ", y_top)
        # right
        x_right = center_x
        while screenshot_img.getpixel((x_right, center_y)) != Common.COLOR_WHITE:
            x_right += 1
        print("right: ", x_right)
        # down
        y_down = center_y
        while screenshot_img.getpixel((center_x, y_down)) != Common.COLOR_WHITE:
            y_down += 1
        print("down: ", y_down)

        #game box
        return Box(x_left, y_top,
                   x_right - x_left, y_down - y_top)


# Finds the Game Box and writes it down to a file.
def FindGameBox():
    print("Enter this link: https://www.improvememory.org/simple-games/stack-tower/ and don't click anything")
    print("Press 's' when ready to take the screenshot")

    while Common.key_option != "s":
        pass

    game_window: Box = None

    print("Display size: ", pyautogui.size())
    display_width, display_height = pyautogui.size()
    center_width = display_width // 2
    center_height = display_height // 2
    print("Display center: ", center_width, center_height)

    screenshot_img = pyautogui.screenshot()
    center_pixel = screenshot_img.getpixel((center_width, center_height))

    if center_pixel == Common.COLOR_BACKGROUND:
        print("found in center... will expand now")

        game_window = FindGameBoxFromAPoint(screenshot_img, center_width, center_height)
    else:
        print("Not found in center... make sure the game is in the middle of the screen")

    if game_window:
        print("Found the window box. Writing to file.")
        pyautogui.screenshot("data/runtime_img/gameWindow.png", region=game_window)
        file = open(Common.WINDOW_COORDINATES_TXT, "w")
        file.write(','.join(map(str, game_window)))
        file.close()
    else:
        print("Could not find the game window")


if __name__ == '__main__':
    Common.initialize_keyboard_listener()
    FindGameBox()
