# ./hubapp
# For Raspberry Pi using Telegesis USB stick to talk to array of ZigBee devices

import time
import threading
import readline
# App-specific Python modules
import events
import commands


##class mainThread(threading.Thread):
##    def __init__(self, threadId, name, counter):
##        threading.Thread.__init__(self)
##        self.threadID = threadId
##        self.name = name
##        self.counter = counter
##
##    def run(self):
        
class cliThread(threading.Thread):
    def __init__(self, threadId, name, counter):
        threading.Thread.__init__(self)
        self.threadID = threadId
        self.name = name
        self.counter = counter

    def run(self):
        while True:
            cmd = raw_input('>')
            commands.Commands(onecmd(cmd))
        # was commands.Commands().cmdloop()

def main():
    #MainThread = mainThread(1, "Main", 1)
    commandThread = cliThread(2, "OSCLI", 2)
    #mainThread.start()
    commandThread.start()
    events.Issue(events.ids.INIT)
    sleepDelayS = 0.1
    while True:
        time.sleep(sleepDelayS)
        events.Issue(events.ids.SECONDS, sleepDelayS)
    # end mainloop
     
def EventHandler(eventId, arg):
    if eventId == events.ids.INIT:
        print("Starting hubapp, v0.0.0.4")
    # end event handler
    
if __name__ == "__main__":
    main()

