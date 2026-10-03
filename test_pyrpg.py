# PyRPG state-lifecycle regression tests.
#
# Covers the full state lifecycle from character creation to game exit and
# proves that every new game rebuilds its state instead of reusing old objects.

import io
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gamestate
import pyrpg
from charcreation import createNewPlayer
from gamemenu import GameMenu
from mainmenu import MainMenu
from player import Player


def scriptInputs(values):
    """Yield scripted inputs, then keep answering 'q' so a buggy loop exits."""
    for value in values:
        yield value
    while True:
        yield "q"


class GameHarness(unittest.TestCase):
    """Runs pyrpg.main() with scripted input inside a temp working directory."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.oldCwd = os.getcwd()
        os.chdir(self.tmpdir.name)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        os.chdir(self.oldCwd)
        self.tmpdir.cleanup()

    def runGame(self, inputs, onCreate=None):
        created = []
        menus = []
        realCreate = pyrpg.createNewPlayer
        realMenu = pyrpg.MainMenu

        def spyCreate():
            player = realCreate()
            if onCreate is not None:
                onCreate(player)
            created.append(player)
            return player

        def spyMenu():
            menu = realMenu()
            menus.append(menu)
            return menu

        gen = scriptInputs(inputs)
        with mock.patch("builtins.input", side_effect=lambda *a: next(gen)), \
             mock.patch("os.system"), \
             mock.patch.object(pyrpg, "createNewPlayer", spyCreate), \
             mock.patch.object(pyrpg, "MainMenu", spyMenu), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            pyrpg.main()
        return created, menus, out.getvalue()


class TestAttributeBounds(GameHarness):
    """Bug 1: character attributes can go out of bounds via a crafted save."""

    def test_loaded_attributes_stay_within_bounds(self):
        os.mkdir("players")
        with open("players/hero.sav", "w") as f:
            f.write("9999:-100:999999:axe")

        player = Player("Hero")
        self.assertTrue(player.load())
        self.assertGreaterEqual(player.level, gamestate.kPlayerMinLevel)
        self.assertLessEqual(player.level, gamestate.kPlayerMaxLevel)
        self.assertGreaterEqual(player.experience, gamestate.kPlayerMinExperience)
        self.assertLessEqual(player.experience, gamestate.kPlayerMaxExperience)
        self.assertGreaterEqual(player.attack, gamestate.kPlayerMinAttack)
        self.assertLessEqual(player.attack, gamestate.kPlayerMaxAttack)
        self.assertEqual(player.items, ["axe"])

    def test_corrupt_save_is_rejected(self):
        os.mkdir("players")
        with open("players/hero.sav", "w") as f:
            f.write("not:a:number")
        player = Player("Hero")
        self.assertFalse(player.load())
        self.assertEqual(player.level, 1)


class TestCreationConfirmation(GameHarness):
    """Bug 2: character creation completes without confirming attributes."""

    def test_player_must_confirm_attributes(self):
        # Reject the first hero, accept the second one.
        created, _, output = self.runGame(["hero", "n", "hero2", "y", "", "q"])
        self.assertIn("accept these attributes", output.lower())
        self.assertEqual(created[-1].name, "hero2")


class TestNewGameRebuildsState(GameHarness):
    """Bug 3: stale player objects/state leak across games in the menu loop."""

    def test_each_new_game_rebuilds_state(self):
        def pickUpSword(player):
            player.items.append("sword")  # simulate gameplay in game one

        created1, menus1, _ = self.runGame(["alice", "y", "", "q"], onCreate=pickUpSword)
        created2, menus2, _ = self.runGame(["bob", "y", "", "q"])

        player1, player2 = created1[-1], created2[-1]

        # Distinct player objects per game.
        self.assertIsNot(player1, player2)
        self.assertEqual(player2.name, "bob")

        # No shared mutable state: game one's loot must not leak into game two.
        self.assertIsNot(player1.items, player2.items)
        self.assertEqual(player1.items, ["sword"])
        self.assertEqual(player2.items, [])

        # Fresh menu objects per game as well.
        self.assertTrue(menus1)
        self.assertTrue(menus2)
        self.assertIsNot(menus1[0], menus2[0])

        # Stats mutated in game one must not bleed into game two.
        player1.level = 50
        player1.attack = 500
        self.assertEqual(player2.level, 1)
        self.assertEqual(player2.attack, 10)


class TestSaveRestoreItems(GameHarness):
    """Bug 4: items are lost when a save is restored."""

    def test_items_survive_save_and_load(self):
        player = Player("tester")
        player.items = ["sword", "shield"]
        player.save()

        restored = Player("tester")
        self.assertTrue(restored.load())
        self.assertEqual(restored.items, ["sword", "shield"])
        self.assertEqual(restored.level, player.level)
        self.assertEqual(restored.attack, player.attack)


class TestInvalidMenuInput(GameHarness):
    """Bug 5: an invalid option returns the wrong menu state."""

    def test_invalid_input_never_exits_or_jumps_menu(self):
        with mock.patch("builtins.input", return_value="zzz"):
            self.assertEqual(MainMenu().captureUserInput(), gamestate.kGameStateInvalid)
        # Base menu must not fall through to the exit state either.
        self.assertNotEqual(GameMenu().captureUserInput(), gamestate.kGameStateExit)
        self.assertEqual(GameMenu().captureUserInput(), gamestate.kGameStateInvalid)

    def test_invalid_input_redisplays_same_menu(self):
        _, menus, output = self.runGame(["hero", "y", "", "x", "", "q"])
        self.assertIn("Invalid entry", output)
        self.assertGreaterEqual(output.count("Main Menu"), 2)
        self.assertGreaterEqual(len(menus), 2)


class TestFullLifecycle(GameHarness):
    """End-to-end: creation -> main menu -> actions -> save -> exit -> reload."""

    def test_creation_to_game_over(self):
        created, _, output = self.runGame(["hero", "y", "", "t", "", "e", "", "q"])

        self.assertIn("Welcome adventure", output)
        self.assertIn("Main Menu", output)
        self.assertIn("gate keeper", output)
        self.assertIn("muster the strength", output)
        self.assertEqual(created[-1].name, "hero")
        self.assertTrue(os.path.exists("players/hero.sav"))

        # Second run restores the same hero instead of starting over.
        created2, _, output2 = self.runGame(["hero", "y", "", "q"])
        self.assertIn("Welcome back hero", output2)
        self.assertEqual(created2[-1].name, "hero")


if __name__ == "__main__":
    unittest.main(verbosity=2)
