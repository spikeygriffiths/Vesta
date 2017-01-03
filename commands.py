#!commands.py

# Command Line Interpreter module for hubapp

# Standard Python modules
import cmd
import readline
import sys
import select
# App-specific Python modules
import devices
import events
import telegesis
import hubapp

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    if eventId == events.ids.SECONDS:
        if select.select([sys.stdin], [], [], 0)[0]:
            cmd = sys.stdin.readline()
            if cmd:
                Commands().onecmd(cmd)
    # End of Command EventHandler

class Commands(cmd.Cmd):
    
    def do_devs(self, line):
        """devs
        Show all devices"""
        print (devices.info) # ToDo: Add formatting to improve layout.  Also use cmd args to show selected bits of devices, rather than whole list
        print (devices.ephemera) # Clumsy, since it's not easy to tie each device to equivalent ephemeral index

    def do_open(self, line):
        """open
        Opens network (for 60s) to allow new device to join"""
        telegesis.TxCmd("AT+PJOIN")

    def do_at(self, line):
        """at
        "Sends AT command to Telegesis stick"""
        telegesis.TxCmd("AT"+line)
        

