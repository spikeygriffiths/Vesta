# ./devices

import events
import hubapp

if __name__ == "__main__":
    hubapp.main()

# Keep a track of known devices present in the system
info = []

def EventHandler(eventId, arg):
    #if eventId == events.ids.INIT:
        # Load previous cache of devices into dev[]
    if eventId == events.ids.CHECKIN:
        # See if we have anything to ask the device...
        devIdx = find(arg[2])
        if -1 != devIdx:
            devIdx = new(arg[2])
            

def find(devId):
    devIdx = 0
    for device in info:
        for item in device:
            if item == ("devId", devId):
                return devIdx
        devIdx = devIdx + 1
    return -1 # Failed to find device

def newDev(devId):
    info.append([("devId",devId)])
    return len(info)-1 # -1 to convert number of elements in list to an index

def addKeyVal(devIdx, name, value):
    info[devIdx].append((name, value) )

    
