# ./hubapp
# For Raspberry Pi using Telegesis USB stick to talk to array of ZigBee devices

import time
# App-specific Python modules
import events

def main():
    events.Issue(events.ids.INIT)
    sleepDelayS = 0.1
    while True:
        time.sleep(sleepDelayS)
        events.Issue(events.ids.SECONDS, sleepDelayS)
    # end mainloop

if __name__ == "__main__":
    main()
 
