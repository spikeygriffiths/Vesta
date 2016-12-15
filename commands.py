# ./commands

# Command Line Interpreter module for hubapp

# Standard Python modules
import cmd
import readline
import sys
import select
#import threading
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

#        commandThread = cliThread(1, "OSCLI", 1)
#        commandThread.start()
#
#class cliThread(threading.Thread):
#    def __init__(self, threadId, name, counter):
#        threading.Thread.__init__(self)
#        self.threadID = threadId
#        self.name = name
#        self.counter = counter
#
#    def run(self):
#        Commands().cmdloop()

class Commands(cmd.Cmd):
    
    def do_devs(self, line):
        """devs
        Show all devices"""
        print (devices.info)

    def do_open(self, line):
        """open
        Opens network (for 60s) to allow new device to join"""
        telegesis.TxCmd("AT+PJOIN")

    
