# ./events

# App-specific Python modules
import telegesis
import hubapp
import rules

if __name__ == "__main__":
    hubapp.main()

class ids:
    INIT = 0 # No arg
    SECONDS = 1 # Arg is elapsed time in seconds since last EVENT_SECONDS
    TRIGGER = 2 # Arg is nodeId
    BUTTON = 3  # Arg is nodeId

def Issue(eventId, arg=0):
    # Tell all interested parties about the new event
    EventHandler(eventId, arg) # Local event handler
    telegesis.EventHandler(eventId, arg)
    rules.EventHandler(eventId, arg)

def EventHandler(eventId, arg):
    if (eventId == ids.INIT):
        print("Starting hubapp, v0.0.0.1")
    elif (eventId == ids.TRIGGER):
        print("Got trigger from ", arg)
    # end event handler
