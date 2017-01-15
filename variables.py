#!variables.py

from datetime import datetime
# App-specific Python modules
import hubapp
import rules
import log
import events

varList = []

if __name__ == "__main__":
    hubapp.main()

#def EventHandler(eventId, eventArg):

def Set(name, value):
    global varList
    Del(name) # Remove old tuple if necessary
    #log.log("Variable "+name+" gets "+value)
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

