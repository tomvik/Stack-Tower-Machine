from pynput import keyboard

import Common
from ScreenWindowSelection import FindCoordinates
from Engine import PlayGame


def on_press(key):
    if key == keyboard.Key.esc:
        print('Esc')
        Common.option = 'q'
    try:
        Common.option = key.char
        if key.char == 'q':
            print('q')
    except:
        Common.option = ''
        pass


def Menu() -> None:
    print("Welcome to the Stack Tower Machine. Please select an option.\n")

    validOption = False

    while not validOption:
        validOption = True

        print("1. Select screen window.")
        print("2. Play game mode.")
        print("\nPress q to quit at any time.\n")

        print("Select your option.")
        Common.option = ''
        while(Common.option == ''):
            pass

        if(Common.option == '1'):
            print("Select screen window")
            FindCoordinates()
        elif(Common.option == '2'):
            print("Play game in slow mode")
            PlayGame()
        elif(Common.option == 'q'):
            print("Force quit")
            break
        else:
            validOption = False
            print("Wrong parameter, select a number from the options.\n")


if __name__ == "__main__":
    keyboardListener = keyboard.Listener(on_press=on_press)
    keyboardListener.start()
    Menu()
