# PyRPG
# File: mainmenu.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/4/2011

from gamestate import *
from gamemenu import *

_title = "Main Menu"
_options = {"T" : "Go to town", "E" : "Explore the world", "Q" : "Quit Game"}

class MainMenu(GameMenu):
    
    def __init__(self):
        self.title = _title
        self.options = dict(_options)


    def captureUserInput(self):
        userInput = input()
        state = kGameStateMainMenu
        
        if userInput.lower() in ('q', 'quit'):
            state = kGameStateExit
        
        elif userInput.lower() in ('t', 'town'):
            print("The town gates are closed. You call out to the gate keeper but no one answers.\n\n")
        
        elif userInput.lower() in ('e', 'explore'):
            print("You gaze down the path before you but can't seem to muster the strength to begin walking.\n\n")

        else:
            print("Invalid entry. Try again.")
            state = None

        return state
