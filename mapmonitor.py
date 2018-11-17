# mapmonitor.py is a plugin for minqlx to:
# -check on a map change for a change to a bad map
# -If all players are disconnected on a map change it changes to the default map
# -If enabled (default is enabled) the script will also change to the default map when all players disconnect
# created by BarelyMiSSeD on 11-17-2018
#
"""
Set these cvars in your server.cfg (or wherever you set your minqlx variables).:
set qlx_mmDefaultMap "almostlost ca"    //set the default map and factory type
set qlx_mmCheckTime "60"                //The amount of time the script will check after a map change for a bad map
set qlx_mmChangeWhenEmpty "1"           //Enable to change to default map when all players disconnect (1=enabled, 0=disabled)
"""

import minqlx
import time

Version = 1.0


class mapmonitor(minqlx.Plugin):
    def __init__(self):
        # cvars
        self.set_cvar_once("qlx_mmDefaultMap", "almostlost ca")
        self.set_cvar_once("qlx_mmCheckTime", "60")
        self.set_cvar_once("qlx_mmChangeWhenEmpty", "1")

        # Minqlx bot Hooks
        self.add_hook("map", self.handle_map)
        self.add_hook("vote_ended", self.handle_vote_ended)
        self.add_hook("player_disconnect", self.handle_player_disconnect)

        # Script Variables
        self._map_change_time = 0.0
        self.map_changed = False
        self.mm_check = False

    def handle_map(self, mapname, factory):
        self.mm_check = False
        self._map_change_time = time.time()

        @minqlx.delay(1)
        def check():
            self.check_player_count()

        check()

    def handle_vote_ended(self, votes, vote, args, passed):
        if passed and vote.lower() == "map":
            self.mm_check = False

    def handle_player_disconnect(self, player, reason):
        if len(self.players() == 0) and self.get_cvar("qlx_mmChangeWhenEmpty", bool):
            self.change_map()

    @minqlx.thread
    def check_player_count(self):
        if not self.map_changed:
            self.mm_check = True
            loop = 1
            loop_time = self.get_cvar("qlx_mmCheckTime", int)
            while time.time() - self._map_change_time < loop_time and self.mm_check:
                time.sleep(1)
                if len(self.players()) == 0:
                    self.change_map()
                    break
                loop += 1
        self.map_changed = False
        self.mm_check = False

    @minqlx.next_frame
    def change_map(self):
        minqlx.console_print("^1Changing map to {}".format(self.get_cvar("qlx_mmDefaultMap")))
        self.map_changed = True
        minqlx.console_command("map {}".format(self.get_cvar("qlx_mmDefaultMap")))
