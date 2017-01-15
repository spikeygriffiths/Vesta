#!events.py

# App-specific Python modules
import telegesis
import hubapp
import devices
import rules
import commands
import variables

if __name__ == "__main__":
    hubapp.main()

class ids:
    INIT = 0 # No arg
    SECONDS = 1 # Arg is elapsed time in seconds since last EVENT_SECONDS
    TRIGGER = 2 # Arg is list, including nodeId in arg[1]
    BUTTON = 3  # Arg is list, including nodeId in arg[1] as well as button message in arg[0]
    CHECKIN = 4 # Arg is list, including nodeId in arg[1]
    RXMSG = 5 # Arg is list, direct from Telegesis
    RXERROR = 6 # Arg is decimal number indicating error
    RXEXPRSP = 7 # Arg is the whole response
    NEWDEV = 8 # Arg is the whole response (devType, devEui, devNodeId)
    INFO = 9 # No arg, just print any useful info

def Issue(eventId, eventArg=0):
    # Tell all interested parties about the new event
    hubapp.EventHandler(eventId, eventArg)
    telegesis.EventHandler(eventId, eventArg)
    devices.EventHandler(eventId, eventArg)
    rules.EventHandler(eventId, eventArg)
    commands.EventHandler(eventId, eventArg)
    variables.EventHandler(eventId, eventArg)
