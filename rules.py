# ./rules

import events
import hubapp

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    if (eventId == events.ids.TRIGGER):
        if int(arg[3], 16) & 1:
            print("Door ", arg[1], "opened")
        else:
            print("Door ", arg[1], "closed")

