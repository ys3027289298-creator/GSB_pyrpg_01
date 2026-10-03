# PyRPG
# File: pyrpg.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/4/2011

import os
from gamestate import *
from mainmenu import *
from player import *
from charcreation import *

def main():
    currentState = kGameStateCharacterCreation
    player = None

    while currentState > kGameStateExit:
        # (Re)build all game state from scratch for every new game
        if currentState == kGameStateCharacterCreation:
            player = createNewPlayer()
            currentState = kGameStateMainMenu
            continue

        os.system('clear')

        print("%s you are standing at the gates of the town. What would you like to do?" % (player.name))

        # Display Main Menu
        player.printStats()

        if currentState == kGameStateMainMenu:
            currentState = MainMenu().display() 

        # TODO: Enter town

        # TODO: Enter world

        # Pause for reading
        if currentState != kGameStateExit:
            print("\n -- Press any key to continue --")
            input()

    return 0

if __name__ == "__main__":
    main()
