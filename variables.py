#!variables.py

import random
from datetime import datetime
# App-specific Python modules
import log
import events
import database

varList = []

def EventHandler(eventId, eventArg):
    global varList
    if eventId == events.ids.SECONDS:
        away = database.GetAppState("away")
        if away == None:
            away = "False"    # Assume at home if we don't know any better
            database.SetAppState("away", away)  # Ensure database has our same default
            Set("away", away)  # Keep our variable in sync with the value from the database, so now user can update the db via the web and we'll know...
        oldAway = Get("away")
        if oldAway == None:
            oldAway = "Unknown" # Force update
        if oldAway != away:
            log.debug("Away state has changed from "+oldAway+" to "+away)
            if away == "False":
                database.NewEvent(0, "Arrived Home")
            else:
                database.NewEvent(0, "Gone Away")
            Set("away", away)  # Keep our variable in sync with the value from the database, so now user can update the db via the web and we'll know...

def Set(name, value):
    global varList
    if Get(name) != value:  # Only update value if it has changed
        Del(name) # Remove old tuple if necessary
        log.debug("Variable \""+name+"\" gets "+value+" @ "+"{0:%Y-%m-%d %H:%M:%S}".format(datetime.now()))
        varList.append((name, value, "{0:%Y-%m-%d %H:%M:%S}".format(datetime.now()))) # Add new one regardless

def Del(name):
    global varList
    for item in varList:
        if item[0].lower() == name.lower(): # Case-independent name matching
            varList.remove(item) # Remove tuple
    
def Get(name):  # Get value associated with name
    global varList
    if name.lower() == "rand":
        return random.random() * 100    # Could return random.randrange(0,101) to give an integer percentage
    for item in varList:
        if item[0].lower() == name.lower(): # Case-independent name matching
            return item[1] # Just return value associated with name
    return None # Indicate item not found

def GetTime(name):  # Get time when value associated with name was last updated
    global varList
    if name.lower() == "rand":
        return random.random() * 100    # Could return random.randrange(0,101) to give an integer percentage
    for item in varList:
        if item[0].lower() == name.lower(): # Case-independent name matching
            return item[2] # Just return time associated with name
    return None # Indicate item not found

