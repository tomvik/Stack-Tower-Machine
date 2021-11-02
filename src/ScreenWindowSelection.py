import pyautogui
from pyscreeze import Box

import Common


def FindCoordinates():
    print("Enter this link: https://www.improvememory.org/simple-games/stack-tower/ and don't click anything")
    print("Press 's' when ready to take the screenshot")

    while Common.option != "s":
        pass

    gameWindow: Box = None
    startButton: Box = None

    try:
        startButton: Box = pyautogui.locateOnScreen(
            'data/img/Start.png', confidence=0.8)
    except:
        print("Start button was not there")

    if startButton:
        print(startButton)
        pyautogui.screenshot(
            "data/runtime_img/startButton.png", region=startButton)

        startButtonCenter = pyautogui.center(startButton)

        print(startButtonCenter)
        gameWindow = Box(startButton.left, startButton.top + 50,
                         startButton.width, startButton.height - 50)

        pyautogui.screenshot(
            "data/runtime_img/gameWindow.png", region=gameWindow)

    if gameWindow:
        print("Found the window box. Writing to file.")
        file = open(Common.WINDOW_COORDINATES_TXT, "w")
        file.write(','.join(map(str, gameWindow)))
        file.close()


if __name__ == '__main__':
    pyautogui.sleep(2)
    FindCoordinates()
