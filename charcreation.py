# PyRPG
# File: charcreation.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/4/2011

from gamestate import *
from player import *


def createNewPlayer():
    confirmed = False

    while not confirmed:
        print("Welcome adventure. What is your name?")

        player = Player(input())

        # Load player data
        if player.load() == False:
            print("Ahh! a new adventure! I will save your progress now.")
            player.save()

        # Confirm the character's attributes before entering the game
        player.printStats()
        print("Are these the attributes you wish to keep? (Y/N)")
        confirmed = input().lower() in ('y', 'yes')

        if not confirmed:
            print("Very well. Let us begin again.\n")

    # Pause for reading
    print("\n-- Press any key to continue --")
    input()

    return player
