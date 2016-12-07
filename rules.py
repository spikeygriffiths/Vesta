# ./rules

import events
import hubapp
import devices

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    #if (eventId == ids.INIT):
        # Ought to load existing set of rules so we know how to respond to events
    if (eventId == events.ids.TRIGGER):
        devIndex = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        devName = devices.GetVal(devIndex, "Name")
        if devName == "DWS003":
            if int(arg[3], 16) & 1: # Bottom bit indicates alarm1
                print("Door", arg[1], "opened")
            else:
                print("Door", arg[1], "closed")
        elif devName == "MOT003":
            print("PIR", arg[1], "active")
        else:
            print("DevName:", devName, " id:", arg[1]," zonestatus", arg[3])
    elif (eventId == events.ids.BUTTON):
        devIndex = devices.GetIdx(arg[1]) # Lookup device from network address in arg[1]
        print ("Button ", arg[1], " pressed")
