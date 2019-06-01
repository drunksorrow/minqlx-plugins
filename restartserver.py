# restartserver.py is a plugin for minqlx to:
# -Restart the server at a certain time, or as soon as the server empties, once the restart time has passed.
# -The server restarting requires that a management program, such as supervisor, is installed and controlling
#   and monitoring the server to restart the process once the quit command is issued.
# Created by BarelyMiSSeD on 5-31-2019
#
"""
// Set these cvars in your server.cfg (or wherever you set your minqlx variables).:
set qlx_restartTime "06:00"    // Sets the time the server restarts. Format "HH:MM" to match to time on server (24 hour format)
set qlx_restartCmdEnable "1"   // Allow restart command usage (0=disable, 1=enable)
set qlx_restartUseTime "1"     // Allow time command usage (0=disable, 1=enable). Disables other script time commands.
"""

"""
Script COMMANDS (both of these commands need to be enabled with the cvars before they will function):
restart - will restart the server, with an optional modifier included. If no modifier is included the server will issue an
 immediate restart command, even if the server is not empty. If a time is included the server will restart at the
  supplied time or as soon as the server has emptied after the supplied time has passed. If "clear" is included, the
  custom restart time, if previously set, will be cleared. if "time" is included the current restart time will be
  reported.
time - will report the current server time.
"""

import minqlx
import time

VERSION = "1.3"


class restartserver(minqlx.Plugin):
    def __init__(self):
        # cvars
        self.set_cvar_once("qlx_restartTime", "06:00")  # Format "HH:MM" to match to time on server
        self.set_cvar_once("qlx_restartCmdEnable", "1")  # Allow restart command usage (0=disable, 1=enable)
        self.set_cvar_once("qlx_restartUseTime", "1")  # Allow time command usage (0=disable, 1=enable)

        # hooks
        self.add_hook("player_disconnect", self.handle_player_disconnect)

        # player commands
        self.add_command("restart", self.restart_server, 4)
        self.add_command("time", self.get_server_time)

        # Script Variables
        self.start_time = [time.strftime("%j"), time.strftime("%H:%M:%S")]
        self.checking_restart = False
        self.restart_time = None

        # Initialize commands
        self.remove_conflicting_time_comands()
        if len(self.players()) == 0:
            @minqlx.delay(5)
            def check_restart():
                self.check_restart_time()
            check_restart()

    def handle_player_disconnect(self, player, reason):
        try:
            @minqlx.delay(5)
            def check_player_count():
                if len(self.players()) == 0:
                    self.check_restart_time()
            check_player_count()
        except Exception as e:
            minqlx.console_print("^1restartserver handle_player_disconnect Exceptions: {}".format(e))

    @minqlx.thread
    def check_restart_time(self):
        try:
            if not self.checking_restart:
                self.checking_restart = True
                if not self.restart_time:
                    restart_time = ["0", self.get_cvar("qlx_restartTime")]
                else:
                    restart_time = ["0", self.restart_time]
                if time.strftime("%H:%M") >= restart_time[1]:
                    restart_time[0] = str(int(self.start_time[0]) + 1)
                else:
                    restart_time[0] = self.start_time[0]
                while self.checking_restart:
                    if restart_time[0] <= time.strftime("%j") and time.strftime("%H:%M") >= restart_time[1]:
                        minqlx.console_print("^1Restart Server script is issuing a quit command to"
                                             " restart the empty server after the scheduled time of {}"
                                             .format(restart_time[1]))
                        minqlx.console_command("quit")
                    time.sleep(60)
                    if len(self.players()) > 0:
                        self.checking_restart = False
        except Exception as e:
            minqlx.console_print("^1restartserver check_time Exceptions: {}".format(e))
        finally:
            self.checking_restart = False

    @minqlx.delay(5)
    def remove_conflicting_time_comands(self):
        if self.get_cvar("qlx_restartUseTime", bool):
            loaded_scripts = minqlx.Plugin._loaded_plugins
            scripts = set(loaded_scripts)
            command = {"time"}
            for script in scripts:
                if script == "restartserver":
                    continue
                try:
                    for cmd in loaded_scripts[script].commands.copy():
                        if command.intersection(cmd.name):
                            loaded_scripts[script].remove_command(cmd.name, cmd.handler)
                except:
                    continue

    def get_server_time(self, player, msg, channel):
        if self.get_cvar("qlx_restartUseTime", bool):
            self.msg("^3The current server time is ^2{}".format(time.strftime("%b %d %Y %H:%M:%S")))

    def restart_server(self, player, msg, channel):
        if self.get_cvar("qlx_restartCmdEnable", bool):
            if len(msg) > 1:
                if msg[1].lower().startswith("h"):
                    player.tell("^3Schedule a server restart time greater than 1 minute from the command issue time.")
                    player.tell("^3This gives you time to disconnect from the server to allow the command to execute.")
                    player.tell("^3Valid time format is HH:MM in a 24 hour format. 9pm would be 21:00 and the"
                                " current server time is {}".format(time.strftime("%H:%M")))
                elif msg[1] == "clear":
                    if self.restart_time:
                        self.restart_time = None
                        player.tell("^3The custom restart time has been cleared. The server will restart at the default"
                                    " time of {}".format(self.get_cvar("qlx_restartTime")))
                        if self.checking_restart:
                            self.checking_restart = False

                            @minqlx.delay(65)
                            def server_check():
                                if len(self.players()) == 0:
                                    self.check_restart_time()

                            server_check()
                    else:
                        player.tell("^3There was not a custom restart time set. The server will restart at the default"
                                    " time of {}".format(self.get_cvar("qlx_restartTime")))
                elif msg[1] == "time":
                    player.tell("^3The set restart time is {}".format(self.restart_time if self.restart_time else
                                                                      self.get_cvar("qlx_restartTime")))
                else:
                    check_time_format = msg[1].split(":")
                    try:
                        if len(check_time_format) == 2 and 0 <= int(check_time_format[0]) <= 24 and\
                                0 <= int(check_time_format[1]) <= 59:
                            if time.strftime("%H:%M") < msg[1]:
                                self.restart_time = msg[1]
                                if self.checking_restart:
                                    self.checking_restart = False
                                    player.tell("^1The server restart check is being stopped. Restart command will"
                                                " be sent in 65 seconds.")

                                    @minqlx.delay(65)
                                    def restart_init():
                                        player.tell("^1The server restart command has been sent to restart the"
                                                    " server at {}".format(self.restart_time if self.restart_time else
                                                                           self.get_cvar("qlx_restartTime")))
                                        self.check_restart_time()
                                    restart_init()
                                else:
                                    player.tell("^1The server restart command has been sent to restart the server at {}"
                                                .format(self.restart_time))
                                    self.check_restart_time()
                            else:
                                player.tell("^3Scheduling a restart time only works if the time is in the future.")
                        else:
                            player.tell("^3Valid time format is HH:MM in a 24 hour format. 9pm would be 21:00")
                    except ValueError:
                        player.tell("^3Valid time format is HH:MM in a 24 hour format. 9pm would be 21:00")
                    except Exception as e:
                        minqlx.console_print("^1restartserver restart_server Exceptions: {}".format(e))
            else:
                minqlx.console_print("^1Restart Server script is issuing a quit command because {}restart was issued"
                                     " by a server admin.".format(self.get_cvar("qlx_commandPrefix")))
                minqlx.console_command("quit")
        else:
            player.tell("^3The {}restart command is disabled on this server".format(self.get_cvar("qlx_commandPrefix")))
