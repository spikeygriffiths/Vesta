#!variables.py

import random
# App-specific Python modules
import log

varList = []

def Set(name, value):
    global varList
    Del(name) # Remove old tuple if necessary
    log.debug("Variable \""+name+"\" gets "+value)
    varList.append((name, value)) # Add new one regardless

def Del(name):
    global varList
    for item in varList:
        if item[0].lower() == name.lower(): # Case-independent name matching
            varList.remove(item) # Remove tuple
    
def Get(name):
    global varList
    if name.lower() == "rand":
        log.debug("random
        return random.random() * 100    # Could return random.randrange(0,101) to give an integer percentage
    for item in varList:
        if item[0].lower() == name.lower(): # Case-independent name matching
            return item[1] # Just return value associated with name
    return None # Indicate item not found

