# ./events

# App-specific Python modules
import telegesis
import hubapp
import devices
import rules

if __name__ == "__main__":
    hubapp.main()

class ids:
    INIT = 0 # No arg
    SECONDS = 1 # Arg is elapsed time in seconds since last EVENT_SECONDS
    TRIGGER = 2 # Arg is list, including nodeId in arg[1]
    BUTTON = 3  # Arg is list, including nodeId in arg[1]
    CHECKIN = 4 # Arg is list, including nodeId in arg[1]
    RXMSG = 5 # Arg is list, direct from Telegesis
    RXERROR = 6 # Arg is decimal number indicating error

def Issue(eventId, arg=0):
    # Tell all interested parties about the new event
    EventHandler(eventId, arg) # Local event handler
    telegesis.EventHandler(eventId, arg)
    devices.EventHandler(eventId, arg)
    rules.EventHandler(eventId, arg)

def EventHandler(eventId, arg):
    if (eventId == ids.INIT):
        print("Starting hubapp, v0.0.0.2")
    elif (eventId == ids.TRIGGER):
        print("Got trigger from ", arg)
    # end event handler
