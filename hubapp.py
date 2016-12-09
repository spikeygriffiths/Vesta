# ./hubapp
# For Raspberry Pi using Telegesis USB stick to talk to array of ZigBee devices

import time
# App-specific Python modules
import events

if __name__ == "__main__":
    main()

def main():
    events.Issue(events.ids.INIT)
    sleepDelayS = 0.1
    while True:
        time.sleep(sleepDelayS)
        events.Issue(events.ids.SECONDS, sleepDelayS)
    # end mainloop
 
def EventHandler(eventId, arg):
    if eventId == events.ids.INIT:
        print("Starting hubapp, v0.0.0.3")
    # end event handler
