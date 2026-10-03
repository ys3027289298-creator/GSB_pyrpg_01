# PyRPG
# File: gamemenu.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/2/2011

# Private Attributes
_kGameMenuLineLength = 80

class GameMenu:

    def __init__(self):
        # Instance-owned state so menus never share mutable defaults
        self.title = "Menu"
        self.options = {"Q" : "Quit Game"}

    def printDivider(self):
        divider = ""
        length = _kGameMenuLineLength

        while length > 0:
            divider = divider + "-"
            length -= 1

        print("%s" % (divider))

    def printTitle(self):
        length = (_kGameMenuLineLength / 2) - (len(self.title) / 2)
        padding = ""

        while length > 0:
            padding = padding + " "
            length -= 1

        print("%s%s" % (padding, self.title))

    def captureUserInput(self):
        print("Invalid entry. Try again.")
        return None

    def display(self):
        state = None

        # Re-prompt until the user picks a valid option
        while state is None:
            self.printDivider()
            self.printTitle()
            self.printDivider()

            for key, value in self.options.items():
                print("  %s: %s" % (key, value))

            state = self.captureUserInput()

        return state
