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
    RXEXPRSP = 7 # Arg is the whole response

def Issue(eventId, arg=0):
    # Tell all interested parties about the new event
    hubapp.EventHandler(eventId, arg)
    telegesis.EventHandler(eventId, arg)
    devices.EventHandler(eventId, arg)
    rules.EventHandler(eventId, arg)

