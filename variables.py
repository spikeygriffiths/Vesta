#!variables.py

from datetime import datetime
# App-specific Python modules
import hubapp
import rules
import events

varList = []
oldMins = 0

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, eventArg):
    global oldMins
    if eventId == events.ids.SECONDS:
        now = datetime.now()
        if now.minute != oldMins:
            oldMins = now.minute # Ready for next time
            rules.Run("time=="+now.strftime("%H:%M")) # Run timed rules once per minute with time of date

def Set(name, value):
    global varList
    Del(name) # Remove old tuple if necessary
    varList.append((name, value)) # Add new one regardless

def Del(name):
    global varList
    for item in varList:
        if item[0] == name:
            varList.remove(item) # Remove tuple
    
def Get(name):
    global varList
    for item in varList:
        if item[0] == name:
            return item[1] # Just return value associated with name
    return None # Indicate item not found

