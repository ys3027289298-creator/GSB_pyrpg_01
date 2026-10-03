# PyRPG
# File: test_pyrpg.py
# Reproduction + regression tests for the shared-mutable-state bugs.

import contextlib
import io
import os
import shutil
import tempfile
import unittest
from unittest import mock

import charcreation
import gamemenu
import mainmenu
import player as player_module
import pyrpg
from gamestate import (
    kGameStateExit,
    kGameStateMainMenu,
    kGameStateCharacterCreation,
)
from gamemenu import GameMenu
from mainmenu import MainMenu
from player import Player


class TempCwdTestCase(unittest.TestCase):
    """Run each test inside a scratch cwd so save files stay isolated."""

    def setUp(self):
        self._old_cwd = os.getcwd()
        self._tmp = tempfile.mkdtemp(prefix="pyrpg_test_")
        os.chdir(self._tmp)

    def tearDown(self):
        os.chdir(self._old_cwd)
        shutil.rmtree(self._tmp, ignore_errors=True)

    def run_game(self, inputs):
        """Run one full game of pyrpg.main() with scripted stdin."""
        created_players = []
        real_create = charcreation.createNewPlayer

        def tracking_create():
            new_player = real_create()
            created_players.append(new_player)
            return new_player

        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs), \
             mock.patch("os.system"), \
             mock.patch("pyrpg.createNewPlayer", new=tracking_create):
            with contextlib.redirect_stdout(stdout):
                rc = pyrpg.main()
        return rc, stdout.getvalue(), created_players


class TestAttributeBounds(TempCwdTestCase):
    """Bug 1: character attributes can go out of bounds."""

    def test_assignment_stays_within_bounds(self):
        hero = Player("Hero")
        hero.level = -5
        self.assertGreaterEqual(hero.level, 1)
        hero.level = 500
        self.assertLessEqual(hero.level, 100)
        hero.attack = -10
        self.assertGreaterEqual(hero.attack, 1)
        hero.experience = -1
        self.assertGreaterEqual(hero.experience, 0)
        hero.damage = -5
        self.assertGreaterEqual(hero.damage, 0)
        hero.damage = 10 ** 9
        self.assertLessEqual(hero.damage, hero.health())
        self.assertGreater(hero.health(), 0)

    def test_load_with_out_of_bounds_save_is_sanitized(self):
        os.makedirs("players")
        with open(os.path.join("players", "corrupt.sav"), "w") as f:
            f.write("-5:-100:-50")
        hero = Player("Corrupt")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(hero.load())
        self.assertGreaterEqual(hero.level, 1)
        self.assertGreaterEqual(hero.experience, 0)
        self.assertGreaterEqual(hero.attack, 1)
        self.assertGreater(hero.health(), 0)


class TestCreationConfirmation(TempCwdTestCase):
    """Bug 2: attribute confirmation after creation is skipped."""

    def test_creation_confirms_attributes_and_allows_recreate(self):
        # 'n' at the confirmation prompt must restart creation.
        inputs = ["First", "n", "Second", "y", ""]
        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=inputs):
            with contextlib.redirect_stdout(stdout):
                hero = charcreation.createNewPlayer()
        self.assertEqual(hero.name, "Second")
        self.assertIn("Second", stdout.getvalue())


class TestStalePlayerState(TempCwdTestCase):
    """Bug 3: stale player/menu state leaks through shared mutable state."""

    def test_player_state_is_instance_owned(self):
        one = Player("One")
        two = Player("Two")
        one.level = 5
        one.attack = 42
        one.items.append("Sword")
        self.assertEqual(two.level, 1)
        self.assertEqual(two.attack, 10)
        self.assertEqual(two.items, [])
        self.assertIsNot(one.items, two.items)
        self.assertIn("items", one.__dict__)

    def test_menu_options_are_not_shared_between_instances(self):
        first = MainMenu()
        second = MainMenu()
        self.assertIsNot(first.options, second.options)
        first.options["Z"] = "Injected"
        self.assertNotIn("Z", second.options)

    def test_menu_title_and_options_unchanged(self):
        menu = MainMenu()
        self.assertEqual(menu.title, "Main Menu")
        self.assertEqual(
            menu.options,
            {"T": "Go to town", "E": "Explore the world", "Q": "Quit Game"},
        )


class TestSaveRestoreItems(TempCwdTestCase):
    """Bug 4: items are lost after a save/restore round trip."""

    def test_items_survive_save_and_load(self):
        hero = Player("Pack")
        hero.items.extend(["Sword", "Potion"])
        with contextlib.redirect_stdout(io.StringIO()):
            hero.save()
        restored = Player("Pack")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(restored.load())
        self.assertEqual(restored.items, ["Sword", "Potion"])

    def test_legacy_three_field_save_still_loads(self):
        os.makedirs("players")
        with open(os.path.join("players", "old.sav"), "w") as f:
            f.write("3:250:15")
        hero = Player("Old")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(hero.load())
        self.assertEqual((hero.level, hero.experience, hero.attack), (3, 250, 15))
        self.assertEqual(hero.items, [])


class TestInvalidMenuInput(TempCwdTestCase):
    """Bug 5: invalid input returns the wrong menu state."""

    def test_invalid_choice_reprompts_instead_of_leaving_menu(self):
        menu = MainMenu()
        stdout = io.StringIO()
        with mock.patch("builtins.input", side_effect=["bogus", "q"]):
            with contextlib.redirect_stdout(stdout):
                state = menu.display()
        self.assertEqual(state, kGameStateExit)
        self.assertIn("Invalid entry", stdout.getvalue())

    def test_base_menu_input_does_not_exit_game(self):
        menu = GameMenu()
        with mock.patch("builtins.input", return_value="zzz"):
            with contextlib.redirect_stdout(io.StringIO()):
                state = menu.captureUserInput()
        self.assertNotEqual(state, kGameStateExit)
        self.assertIsNone(state)


class TestFullLifecycle(TempCwdTestCase):
    """Full state lifecycle: character creation -> menus -> game end."""

    def test_creation_to_exit_lifecycle(self):
        inputs = ["Life", "y", "", "t", "", "e", "", "q"]
        rc, out, players = self.run_game(inputs)
        self.assertEqual(rc, 0)
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0].name, "Life")
        self.assertIn("Main Menu", out)
        self.assertIn("Life", out)
        self.assertTrue(os.path.exists(os.path.join("players", "life.sav")))

    def test_returning_player_restores_save(self):
        os.makedirs("players")
        with open(os.path.join("players", "vet.sav"), "w") as f:
            f.write("4:900:33:Sword,Shield")
        rc, out, players = self.run_game(["Vet", "y", "", "q"])
        self.assertEqual(rc, 0)
        hero = players[0]
        self.assertEqual((hero.level, hero.experience, hero.attack), (4, 900, 33))
        self.assertEqual(hero.items, ["Sword", "Shield"])

    def test_every_new_game_rebuilds_state(self):
        rc1, _, players1 = self.run_game(["Alpha", "y", "", "q"])
        rc2, _, players2 = self.run_game(["Beta", "y", "", "q"])
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)
        self.assertEqual(len(players1), 1)
        self.assertEqual(len(players2), 1)
        first, second = players1[0], players2[0]
        # Brand new objects, never reused across games.
        self.assertIsNot(first, second)
        self.assertIsNot(first.items, second.items)
        self.assertEqual(first.name, "Alpha")
        self.assertEqual(second.name, "Beta")
        # Mutating the old game state must not leak into the new game.
        first.level = 99
        first.items.append("GhostItem")
        self.assertEqual(second.level, 1)
        self.assertEqual(second.items, [])


if __name__ == "__main__":
    unittest.main()
