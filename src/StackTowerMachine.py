import Common
from ScreenWindowSelection import FindCoordinates
from Engine import PlayGame

def Menu() -> None:
    print("Welcome to the Stack Tower Machine. Please select an option.\n")

    validOption = False

    while not validOption:
        validOption = True

        print("1. Select screen window.")
        print("2. Play game mode.")
        print("\nPress q to quit at any time.\n")

        print("Select your option.")
        Common.key_option = ''
        while(Common.key_option == ''):
            pass

        if(Common.key_option == '1'):
            print("Select screen window")
            FindCoordinates()
        elif(Common.key_option == '2'):
            print("Play game in slow mode")
            PlayGame()
        elif(Common.key_option == 'q'):
            print("Force quit")
            break
        else:
            validOption = False
            print("Wrong parameter, select a number from the options.\n")


if __name__ == "__main__":
    Common.initialize_keyboard_listener()
    Menu()
