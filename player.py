# PyRPG
# File: player.py
# Version: 1.0
# Creator: Joel D. Garrett
# Modified: 3/5/2011

import os.path
from gamestate import *

# Attribute Bounds
kMinLevel = 1
kMaxLevel = 100
kMinExperience = 0
kMinAttack = 1
kMaxAttack = 999


def _clamp(value, minimum, maximum):
    return max(minimum, min(maximum, value))


class Player(object):

    def __init__(self, name__):
        self.name = name__
        self.level = 1
        self.experience = 0
        self.attack = 10
        self.damage = 0
        self.items = []

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = _clamp(int(value), kMinLevel, kMaxLevel)

    @property
    def experience(self):
        return self._experience

    @experience.setter
    def experience(self, value):
        self._experience = max(kMinExperience, int(value))

    @property
    def attack(self):
        return self._attack

    @attack.setter
    def attack(self, value):
        self._attack = _clamp(int(value), kMinAttack, kMaxAttack)

    @property
    def damage(self):
        return self._damage

    @damage.setter
    def damage(self, value):
        self._damage = _clamp(int(value), 0, self.health())

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
            file = open(path, 'r')
            data = file.readline().split(':')
            file.close()

            if len(data) in (3, 4):
                try:
                    level = int(data[0])
                    experience = int(data[1])
                    attack = int(data[2])
                except ValueError:
                    return False

                success = True
                self.level = level
                self.experience = experience
                self.attack = attack
                self.items = []
                if len(data) == 4:
                    self.items = [item for item in data[3].split(',') if item]

                print("Welcome back %s. Your progress has been restored." % (self.name))
        
        return success

    def save(self):
        if not os.path.exists("players/"):
            os.mkdir("players/")

        path = "players/%s.sav" % (self.name.lower())
        file = open(path, 'w')

        data = ":".join((str(self.level), str(self.experience), str(self.attack), ",".join(self.items)))

        file.write(data)
        print("-- Player data saved --")
        file.close()
