#!events.py

# App-specific Python modules
import telegesis
import hubapp
import devices
import rules
import commands
import variables
import iottime
import database

if __name__ == "__main__":
    hubapp.main()

class ids:
    INIT = 0 # No arg
    SECONDS = 1 # Arg is elapsed time in seconds since last EVENT_SECONDS, currently 0.1
    TRIGGER = 2 # Arg is list, including nodeId in arg[1]
    BUTTON = 3  # Arg is list, including nodeId in arg[1] as well as button message in arg[0]
    CHECKIN = 4 # Arg is list, including nodeId in arg[1]
    RXMSG = 5 # Arg is list, direct from Telegesis
    RXERROR = 6 # Arg is decimal number indicating error
    RXEXPRSP = 7 # Arg is the whole response
    DEVICE_ANNOUNCE = 8 # Arg is the whole response (devType, devEui, devNodeId)
    INFO = 9 # No arg, just print any useful info
    RX_TELEGESIS = 10   # Arg is line of raw Telegesis text
    MINUTES = 11 # No arg
    PREINIT = 12 #  No arg.  Issued immediately before INIT

def Issue(eventId, eventArg=0):
    # Tell all interested parties about the new event
    hubapp.EventHandler(eventId, eventArg)
    telegesis.EventHandler(eventId, eventArg)
    database.EventHandler(eventId, eventArg)
    devices.EventHandler(eventId, eventArg)
    iottime.EventHandler(eventId, eventArg)
    rules.EventHandler(eventId, eventArg)
    commands.EventHandler(eventId, eventArg)
    
