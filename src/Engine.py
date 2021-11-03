import numpy as np
import cv2
import pyautogui
from pyscreeze import Box, Point
import Common

screenshotsTaken = 0


def GetGameWindow() -> Box:
    print("Reading the coordinates")
    file = open(Common.WINDOW_COORDINATES_TXT, "r")
    line = file.readline()
    rawGameWindow = tuple(map(int, line.split(',')))
    gameWindow: Box = Box(
        rawGameWindow[0], rawGameWindow[1] + 120, rawGameWindow[2], rawGameWindow[3] - 120)
    return gameWindow


def ShowImg(windowTitle, img):
    cv2.imshow(windowTitle, img)
    cv2.waitKey()


def RemoveBackground(img, threshold, debug=False):
    grayImg = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    (_, blackAndWhiteImg) = cv2.threshold(
        grayImg, threshold, 255, cv2.THRESH_BINARY_INV)
    if debug:
        ShowImg("RemoveBackground - GrayImg", grayImg)
        ShowImg("RemoveBackground - BnW", blackAndWhiteImg)
    return cv2.bitwise_and(grayImg, grayImg, mask=blackAndWhiteImg)


def GetScreenshotWithoutBackground(gameWindow, debug=False, fromStorage=False):
    global screenshotsTaken
    screenshotsTaken += 1
    originalScreenshot = None

    if debug:
        fileName = "data/runtime_img/{}.png".format(screenshotsTaken)
        if fromStorage:
            originalScreenshot = cv2.imread(fileName)
        else:
            originalScreenshot = pyautogui.screenshot(
                fileName, region=gameWindow)
    else:
        originalScreenshot = pyautogui.screenshot(region=gameWindow)

    whiteScreenshot = RemoveBackground(originalScreenshot.copy(), 205)

    if debug:
        ShowImg("with Background {}".format(
            screenshotsTaken), originalScreenshot)
        ShowImg("without background {}".format(
            screenshotsTaken), whiteScreenshot)

    return whiteScreenshot.copy()


def GetContours(screenshot, debug=False):
    # 1 contour = both merged
    # 2 contours = base and new one
    contours, hierarchy = cv2.findContours(
        screenshot, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if debug:
        print("Contours found: ", len(contours))

        colorScreenshot = cv2.cvtColor(screenshot, cv2.COLOR_GRAY2BGR)

        if len(contours):
            result = cv2.drawContours(
                colorScreenshot, contours, -1, (0, 255, 0), 3)
            ShowImg("With contours {}".format(screenshotsTaken), result)

    return contours


def ColorSortImg(gameWindow, screenshot):
    colors = dict()
    for y in range(gameWindow.height):
        for x in range(gameWindow.width):
            new_key = screenshot[y][x]
            if new_key in colors:
                colors[new_key] += 1
            else:
                colors[new_key] = 1

    sorted_colors = list(sorted(colors.items(), key=lambda item: item[1]))

    print(sorted_colors)
    print("amount of colors:", len(sorted_colors))

    colorSortedImg = np.zeros(screenshot.shape, dtype=screenshot.dtype)

    ShowImg("empty_color_sorted", colorSortedImg)

    colorIndex = 0
    currentOfIndex = 0
    for y in range(gameWindow.height):
        for x in range(gameWindow.width):
            colorSortedImg[y][x] = sorted_colors[colorIndex][0]
            currentOfIndex += 1

            if currentOfIndex == sorted_colors[colorIndex][1]:
                colorIndex += 1
                currentOfIndex = 0

    ShowImg("colored_sorted", colorSortedImg)


def GetBlackTiles(binaryImg, width, height, lanes):
    # Draw a line in the center of the lane
    desiredWidth = width // (lanes * 2)

    blackTiles = []
    for i in range(4):
        lineX = (desiredWidth * 2 * i) + desiredWidth

        lineBlackTiles = []
        consecutiveBlackPixels = 0
        MinBlackPixelsForTile = 50
        inBlackTile = False
        for lineY in reversed(range(height)):
            if binaryImg[lineY][lineX] == Common.BINARY_WHITE:
                consecutiveBlackPixels = 0
                inBlackTile = False
                binaryImg[lineY][lineX] = Common.BINARY_BLACK
            else:
                consecutiveBlackPixels += 1
                binaryImg[lineY][lineX] = Common.BINARY_WHITE

            if consecutiveBlackPixels > MinBlackPixelsForTile and not inBlackTile:
                inBlackTile = True
                lineBlackTiles.append(
                    Point(lineX, lineY + MinBlackPixelsForTile))

        blackTiles += lineBlackTiles

        # print(blackTiles)
        # ShowImg("lineimg", blackAndWhiteImg)

    def sortingFunction(point: Point):
        return point.y

    blackTiles.sort(reverse=True, key=sortingFunction)
    # print(blackTiles)

    return blackTiles


def CheckIfGameOver(binaryImg, width, height):
    lineY = height // 2

    blackSpots = 0
    blackPixelsCount = 0
    for lineX in range(width // 4, (width // 4) * 3):
        if binaryImg[lineY][lineX] == Common.BINARY_BLACK:
            blackPixelsCount += 1
        else:
            blackPixelsCount = 0

        if blackPixelsCount == 5:
            blackSpots += 1

    return blackSpots == 7
    # print(blackSpots)
    # cv2.line(binaryImg, Point(desiredWidth, height//2),
    #          Point(desiredWidth * 3, height//2), (0, 255, 0), 3)
    # ShowImg("CheckIfGameOver", binaryImg)


# v1 = [45, 50]
# v2 = [245, 396]
# v3 Possibly infinite?
def PlayGame(version: int = 2):
    print("Press p to play")

    while Common.option != "p":
        pass

    gameWindow = GetGameWindow()

    print("Will begin playing the game")

    screenshot = GetScreenshotWithoutBackground(gameWindow, True, True)
    contours = GetContours(screenshot, True)

    secondScreenshot = GetScreenshotWithoutBackground(gameWindow, True, True)
    secondContours = GetContours(secondScreenshot, True)

    print("first contours", contours)
    print("second contours", secondContours)

    # ColorSortImg(gameWindow, screenshot)

    return

    count = 0
    firstClick = True
    while Common.option != 'q':
        count += 1
        screenshot = pyautogui.screenshot(region=gameWindow)
        blackAndWhiteImg = ConvertToBlackAndWhite(screenshot)

        if not CheckIfGameOver(blackAndWhiteImg, gameWindow.width, gameWindow.height):
            blackTiles = GetBlackTiles(
                blackAndWhiteImg, gameWindow.width, gameWindow.height, 4)
            blackTilesPosition = [
                Point(
                    tile.x + gameWindow.left,
                    tile.y + gameWindow.top + 50
                ) for tile in blackTiles]

            if version == 1:
                if len(blackTilesPosition):
                    blackTile = blackTilesPosition[0]
                    if firstClick:
                        pyautogui.moveTo(blackTile.x, blackTile.y, duration=0)
                        pyautogui.mouseDown(
                            blackTile.x+40, blackTile.y, duration=0.11)
                        firstClick = False
                    pyautogui.mouseDown(
                        blackTile.x+40, blackTile.y, duration=0)
            elif version == 2:
                for blackTile in blackTilesPosition:
                    if firstClick:
                        pyautogui.moveTo(blackTile.x, blackTile.y, duration=0)
                        pyautogui.mouseDown(
                            blackTile.x+40, blackTile.y, duration=0.11)
                        firstClick = False
                    pyautogui.mouseDown(
                        blackTile.x+40, blackTile.y, duration=0)
            elif version == 3:
                if len(blackTilesPosition):
                    blackTile = blackTilesPosition[0]
                    if firstClick:
                        pyautogui.moveTo(blackTile.x, blackTile.y, duration=0)
                        pyautogui.mouseDown(
                            blackTile.x+40, blackTile.y, duration=0.11)
                        firstClick = False
                    pyautogui.mouseDown(
                        blackTile.x+40, blackTile.y, duration=0)
                    positions = [
                        gameWindow.left + gameWindow.width // 8,
                        gameWindow.left + (gameWindow.width // 8) * 3,
                        gameWindow.left + (gameWindow.width // 8) * 5,
                        gameWindow.left + (gameWindow.width // 8) * 7,
                    ]
                    while Common.option != 'q':
                        for position in positions:
                            pyautogui.mouseDown(
                                position, blackTile.y, duration=0.1)
            else:
                version = 2

        else:
            print("Game over")
            break

    pyautogui.mouseUp()


if __name__ == "__main__":
    Common.option = "p"
    PlayGame()
