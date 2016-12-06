# ./rules

import events
import hubapp
import devices

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    if (eventId == events.ids.TRIGGER):
        devIndex = devices.find(arg[1]) # Lookup device from network address in arg[1]
        if int(arg[3], 16) & 1: # Bottom bit indicates alarm1
            print("Door", arg[1], "opened")
        else:
            print("Door", arg[1], "closed")
    elif (eventId == events.ids.CHECKIN):
        devIndex = devices.find(arg[1]) # Lookup device from network address in arg[1]
        # device has just checked in, so mark it as present

