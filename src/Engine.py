import numpy as np
import cv2
import pyautogui
from pyscreeze import Box, Point
import time

import Common

screenshotsTaken = 0
sampleSize = 20
fileName = "data/runtime_img/2{}.png"
deltaFileName = "data/runtime_img/2.txt"
saveData = False
globalDebug = False
takeSS = False


def GetGameWindow() -> Box:
    print("Reading the coordinates")
    file = open(Common.WINDOW_COORDINATES_TXT, "r")
    line = file.readline()
    rawGameWindow = tuple(map(int, line.split(',')))
    gameWindow: Box = Box(
        rawGameWindow[0], rawGameWindow[1], rawGameWindow[2], rawGameWindow[3])
    return gameWindow


def writeImagesAndTimes(colorImages, deltasTimes):
    for i in range(len(colorImages)):
        cv2.imwrite(fileName.format(i), colorImages[i])
        file = open(deltaFileName, "w")
        file.write(",".join(map(str, deltasTimes)))
        file.close()


def getTimes():
    file = open(deltaFileName, "r")

    line = file.readline()
    times = list(map(float, line.split(',')))

    file.close()

    return times


def ShowImg(windowTitle, img):
    cv2.imshow(windowTitle, img)
    cv2.waitKey()


def BlurImg(inputImg, debug=False):
    img = inputImg.copy()
    if debug:
        ShowImg("RemoveBackground - Before Blur", img)

    img = cv2.GaussianBlur(img, (5, 5), cv2.BORDER_DEFAULT)

    if debug:
        ShowImg("RemoveBackground - After Blur", img)

    return img


def RemoveBackground(colorImg, threshold, debug=False):
    colorImg = BlurImg(colorImg, debug)
    grayImg = cv2.cvtColor(np.array(colorImg), cv2.COLOR_RGB2GRAY)
    (_, blackAndWhiteImg) = cv2.threshold(
        grayImg, threshold, 255, cv2.THRESH_BINARY_INV)
    if debug:
        ShowImg("RemoveBackground - GrayImg", grayImg)
        ShowImg("RemoveBackground - BnW", blackAndWhiteImg)
    return cv2.bitwise_and(grayImg, grayImg, mask=blackAndWhiteImg)


def GetScreenshotWithoutBackground(gameWindow, debug=False, fromStorage=False):
    global screenshotsTaken
    global fileName
    originalScreenshot = None
    localFileName = fileName.format(screenshotsTaken)
    screenshotsTaken += 1

    if debug:
        if fromStorage:
            originalScreenshot = cv2.imread(localFileName)
        else:
            originalScreenshot = np.array(pyautogui.screenshot(
                localFileName, region=gameWindow))
    else:
        if fromStorage:
            originalScreenshot = cv2.imread(localFileName)
        else:
            originalScreenshot = np.array(
                pyautogui.screenshot(region=gameWindow))

    graySs = RemoveBackground(
        originalScreenshot.copy(), 205, debug)

    if debug:
        ShowImg("with Background {}".format(
            screenshotsTaken), originalScreenshot)
        ShowImg("without background gray {}".format(
            screenshotsTaken), graySs)

    return graySs.copy(), originalScreenshot.copy()


def DrawContoursOnGray(grayImg, contours):
    result = None
    if len(contours):
        colorImg = cv2.cvtColor(grayImg, cv2.COLOR_GRAY2BGR)
        result = cv2.drawContours(
            colorImg, contours, -1, (0, 255, 0), 5)

    return result.copy()


# Gotten from https://www.pyimagesearch.com/2021/10/06/opencv-contour-approximation/
def ApproximateContours(grayImg, contours, eps, debug=False):

    approximations = []
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, eps * perimeter, True)

        if debug:
            text = "eps={:.4f}, num_pts={}".format(eps, len(approx))
            print("[INFO] {}".format(text))

        approximations.append(approx)

    if debug:
        output = DrawContoursOnGray(grayImg, approximations)
        ShowImg("Approximated Contour", output)

    return approximations


def InteractiveApproximateContours(grayImg, contours):
    for eps in np.linspace(0.001, 0.01, 10):
        ApproximateContours(grayImg, contours, eps, True)


def GetContours(grayImg, debug=False):
    contours, hierarchy = cv2.findContours(
        grayImg, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)

    contours = ApproximateContours(grayImg, contours, Common.EPSILON, debug)

    # 1 contour = both merged
    # 2 contours = base and new one
    result = DrawContoursOnGray(grayImg, contours)

    if debug:
        print("Contours found: ", len(contours[0]))
        ShowImg("With contours {}".format(screenshotsTaken), result)

    return contours, result.copy()


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
    global globalDebug
    global saveData
    global takeSS
    global sampleSize

    print("Press p to play")

    while Common.option != "p":
        pass

    gameWindow = GetGameWindow()

    print("Will begin playing the game")

    colorImages = list()
    deltasTimes = list()
    grayImages = list()
    imagesWithContours = list()
    contoursOfImages = list()

    for _ in range(sampleSize):
        startTime = time.time()
        grayImage, colorImage = GetScreenshotWithoutBackground(
            gameWindow, globalDebug, not takeSS)

        colorImages.append(colorImage.copy())
        grayImages.append(grayImage.copy())

        contours, screenshot = GetContours(grayImage)
        imagesWithContours.append(screenshot.copy())
        contoursOfImages.append(contours)

        endTime = time.time()
        deltaTime = endTime - startTime
        deltasTimes.append(deltaTime)

    if saveData:
        writeImagesAndTimes(colorImages, deltasTimes)
    if not takeSS:
        deltasTimes = getTimes()

    for i in range(sampleSize - 1):
        print("For image", i)
        print("Contours", contoursOfImages[i])
        print("Amount of contours", len(contoursOfImages[i]))
        print("For image", i + 1)
        print("Contours", contoursOfImages[i + 1])
        print("Amount of contours", len(contoursOfImages[i + 1]))
        print("Delta time:", deltasTimes[i])
        firstImage = imagesWithContours[i].copy()
        result = cv2.drawContours(
            firstImage, contoursOfImages[i + 1], -1, (255, 0, 0), 5)
        ShowImg("img {} with two contours".format(i), result)

        # InteractiveApproximateContours(originalImages[i], contoursOfImages[i])

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
