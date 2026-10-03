# PyRPG
# File: player.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/5/2011

import os.path
from gamestate import *

# Private Attributes


class Player(object):

    def __init__(self, name__):
        # Every player owns its own mutable state; nothing is shared at the
        # class level so new games cannot inherit leftover values.
        self.name = name__
        self.level = 1
        self.experience = 0
        self.attack = 10
        self.damage = 0
        self.items = []

    def health(self):
        return 50 + (self.level * 50)

    def hitpoints(self):
        return self.health() - self.damage

    def printStats(self):
        # Line padding
        stats = "\n    "

        # Level: Name
        stats = stats + "%d: %s" % (self.level, self.name)
        
        # Hitpoints/Health
        stats = stats + "\t\t%d/%d\n" % (self.hitpoints(), self.health())

        print(stats)

    def load(self):
        success = False
        path = "players/%s.sav" % (self.name.lower())

        if os.path.exists(path):
            with open(path, 'r') as file:
                data = file.readline().split(':')

            try:
                if len(data) in (3, 4):
                    level = self._clamp(int(data[0]), kPlayerMinLevel, kPlayerMaxLevel)
                    experience = self._clamp(int(data[1]),
                                             kPlayerMinExperience,
                                             kPlayerMaxExperience)
                    attack = self._clamp(int(data[2]),
                                         kPlayerMinAttack,
                                         kPlayerMaxAttack)
                    items = []
                    if len(data) == 4 and data[3] != "":
                        items = data[3].split(',')
                else:
                    raise ValueError("malformed save")
            except ValueError:
                print("The saved data for %s is corrupt and cannot be read." % (self.name))
                return False

            success = True
            self.level = level
            self.experience = experience
            self.attack = attack
            self.items = items

            print("Welcome back %s. Your progress has been restored." % (self.name))
        
        return success

    def _clamp(self, value, minimum, maximum):
        return max(minimum, min(maximum, value))

    def save(self):
        if not os.path.exists("players/"):
            os.mkdir("players/")

        path = "players/%s.sav" % (self.name.lower())
        with open(path, 'w') as file:
            data = ":".join((str(self.level),
                             str(self.experience),
                             str(self.attack),
                             ",".join(self.items)))

            file.write(data)
        print("-- Player data saved --")
