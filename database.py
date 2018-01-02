# database.py

import sqlite3
from datetime import datetime
import os
# App-specific Python modules
import events
import rules    # For isNumber()
import log

db = None
curs = None
flushDB = False

def EventHandler(eventId, eventArg):
    global db, curs, flushDB
    if eventId == events.ids.PREINIT:
        db = sqlite3.connect("vesta.db")
        curs = db.cursor()
    if eventId == events.ids.SECONDS:
        if flushDB:
            try:
                db.commit() # Flush events to disk
                flushDB = False
            except:
                log.fault("Database couldn't commit")
    if eventId == events.ids.NEWDAY:
        FlushOldEvents()    # Flush old events to avoid database getting too big and slow
        FlushOldLoggedItems()
        Defragment()    # Compact the database now that we've flushed the old items
    if eventId == events.ids.SHUTDOWN:
        db.commit() # Flush events to disk prior to shutdown
# end of EventHandler

# === Miscellaneous ===
def GetFileSize():
    return os.stat("vesta.db").st_size

def Defragment():
    global curs
    curs.execute("VACUUM")  # Rebuild database in order to compress its file size
    flushDB = True # Commit newly-built table 

# === Logged items ===

def LogItem(devKey, item, value):
    global curs, flushDB
    previousValue = GetLatestLoggedValue(devKey, item)
    if previousValue == None:
        if rules.isNumber(value):
            previousValue = value + 1    # Force values to be different
        else:
            previousvalue = "Not"+value  # Force values to be different
    if previousValue != value:  # Only log the item if it has changed since last time.  Not a good idea for presence!
        log.debug("Setting "+item+" with "+str(value)+" for "+str(devKey)+" (changed from "+str(previousValue))
        if rules.isNumber(value):
            dbCmd = "INSERT INTO "+item+" VALUES (datetime('now', 'localtime'),"+str(value)+","+str(devKey)+")"
        else: # Assume string
            dbCmd = "INSERT INTO "+item+" VALUES (datetime('now', 'localtime'),\""+str(value)+"\","+str(devKey)+")"
    else:  # Value unchanged, so update timestamp of the latest entry
        dbCmd = "UPDATE "+item+" SET timestamp=datetime('now', 'localtime') WHERE devKey="+str(devKey)+" ORDER BY timestamp DESC LIMIT 1"
    log.debug(dbCmd)
    curs.execute(dbCmd)
    flushDB = True # Batch up the commits.  Commit table for web access

def RefreshLoggedItem(devKey, item):
    global curs, flushDB
    dbCmd = "UPDATE "+item+" SET timestamp=datetime('now', 'localtime') WHERE devKey="+str(devKey)+" ORDER BY timestamp DESC LIMIT 1"
    log.debug(dbCmd)
    curs.execute(dbCmd)
    flushDB = True # Batch up the commits.  Commit table for web access

def GetLoggedItemsSinceTime(devKey, item, time):
    global curs
    dbCmd = "SELECT value, timestamp FROM "+item+" WHERE devKey="+str(devKey)+" AND timestamp > "+time  # Get all items after time
    curs.execute(dbCmd)
    rows = curs.fetchall()
    if rows != None:
        return rows  # NB return row as list with (value, time)
    return None

def GetLatestLoggedValue(devKey, item):
    entry = GetLatestLoggedItem(devKey, item)
    if entry != None:
        return entry[0] # Just the value
    return None

def GetLatestLoggedItem(devKey, item):
    return GetLastNLoggedItems(devKey, item, 1)

def GetLastNLoggedItems(devKey, item, num):
    global curs
    curs.execute("SELECT value, timestamp FROM "+item+" WHERE devKey="+str(devKey)+" ORDER BY timestamp DESC LIMIT "+str(num))  # Get latest specified logged items
    if num == 1:
        rows = curs.fetchone()
    else:
        rows = curs.fetchmany(num)	# Or could use fetchall(), I think
    if rows != None:
        return rows  # NB return rows as list with (value, time)
    return None

def FlushOldLoggedItems():
    global curs, flushDB
    curs.execute("DELETE FROM BatteryPercentage WHERE timestamp <= datetime('now', '-1 year')")
    curs.execute("DELETE FROM TemperatureCelsius WHERE timestamp <= datetime('now', '-1 month')")
    curs.execute("DELETE FROM SignalPercentage WHERE timestamp <= datetime('now', '-3 days')")  # Signal strength is only a worry for a while
    curs.execute("DELETE FROM Presence WHERE timestamp <= datetime('now', '-3 days')")  # Don't care about presence after a while
    curs.execute("DELETE FROM PowerReadingW WHERE timestamp <= datetime('now', '-3 days')") # We have the energy readings for long-term comparisons
    curs.execute("DELETE FROM EnergyGeneratedWh WHERE timestamp <= datetime('now', '-1 year')")
    curs.execute("DELETE FROM EnergyConsumedWh WHERE timestamp <= datetime('now', '-1 year')")
    flushDB = True # Batch up the commits

# === Events ===
def NewEvent(devKey, event):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(datetime('now', 'localtime'),(?), (?))", (event, devKey))  # Insert event with local timestamp
    flushDB = True # Batch up the commits

def GetLatestEvent(devKey):
    global curs
    curs.execute("SELECT event FROM Events WHERE devKey="+str(devKey)+" ORDER BY timestamp DESC LIMIT 1")  # Get latest event of device
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def FlushOldEvents():
    global curs, flushDB
    curs.execute("DELETE FROM Events WHERE timestamp <= datetime('now', '-7 days')")  # Remove all events older than 1 week
    flushDB = True # Batch up the commits

# === Groups ===
def IsGroupName(checkName): # Return True if arg is a group name
    global curs
    curs.execute("SELECT userName FROM Groups")
    while True: # Do...while, Python-style
        rows = curs.fetchone()
        if rows == None:
            return False # Didn't find name in Groups
        if checkName == rows[0]:
            return True

def GetGroupsWithDev(devKey):   # Return list of all group names that include specified device
    global curs
    groups = []
    curs.execute("SELECT userName FROM Groups")
    while True: # Do...while, Python-style
        rows = curs.fetchone()
        if rows == None:
            return groups # This is the end of the loop
        groupName = rows[0]
        devList = GetGroupDevs(groupName)
        if str(devKey) in devList:
            groups.append(groupName)    # Append name of each group that features our device

def GetGroupDevs(userName): # Get list of devices that belong to specified group
    global curs
    curs.execute("SELECT devKeyList FROM Groups WHERE userName=\""+userName+"\" COLLATE NOCASE") # Case-insensitive matching
    rows = curs.fetchone()
    if rows != None:
        return "["+rows[0]+"]"  # List of comma separated devKeys.  Surrounding square brackets to convert to Python list
    return None

# === Devices ===
def GetDevicesCount():
    global curs
    curs.execute("SELECT COUNT(*) FROM Devices") # Get number of devices
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return 0

def GetDevKey(item, value):
    global curs
    curs.execute("SELECT devKey FROM Devices WHERE "+item+"=\""+value+"\" COLLATE NOCASE") # Case-insensitive matching
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def GetAllDevKeys():
    global curs
    keyList = []
    curs.execute("SELECT devKey FROM Devices")
    for row in curs:
        keyList.append(row[0])
    return keyList

def GetDeviceItem(devKey, item, defVal = None):
    global curs
    curs.execute("SELECT "+item+" FROM Devices WHERE devKey="+str(devKey))
    rows = curs.fetchone()
    if rows != None:
        if rows[0] == None and defVal != None:  # If database entry is empty and we have a sensible default...
            SetDeviceItem(devKey, item, defVal) # ... then update database...
            return defVal   # ... and return that default
        else:
            return rows[0]
    return None

def SetDeviceItem(devKey, item, value):
    global curs, flushDB
    if type(value) is str:
        if value == "" or value == None:
            value = "(empty)"
        value = value.replace('\x00', '')   # Strip any NUL chars, after LEEDARSON bulb had one in the model name
        curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE devKey="+str(devKey))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Devices SET "+item+"="+str(value)+" WHERE devKey="+str(devKey))
    flushDB = True # Batch up the commits

def NewDevice(nwkId, eui64, devType):
    global curs, db
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    rowId = curs.lastrowid
    log.debug("Newly inserted row is ID "+str(rowId))
    curs.execute("SELECT MAX(devkey) FROM Devices")
    rows = curs.fetchone()
    if rows != None:
        devKey = rows[0]+1  # Add 1o largest devKey to create new unique devKey
    else:
        devKey = 0 # First item to be added
    curs.execute("UPDATE Devices SET devKey="+str(devKey)+" WHERE rowId="+str(rowId))   # Define device key first, since that's used everywhere!
    SetDeviceItem(devKey, "nwkId", nwkId)
    SetDeviceItem(devKey, "Username", "(New) "+nwkId)   # Default username of network ID, since that's unique
    SetDeviceItem(devKey,"devType",devType)    # SED, FFD or ZED
    SetDeviceItem(devKey,"eui64",eui64)
    db.commit() # Flush db to disk immediately
    return devKey    # Return new devKey for newly added device

def RemoveDevice(devKey):
    global curs, db
    #curs.execute("DELETE FROM Groups WHERE devKey="+str(devKey)) # This has to remove devKey from within each group's devKeyList
    userName = GetDeviceItem(devKey, "userName")
    curs.execute("DELETE FROM Rules WHERE rule LIKE '%"+userName+"%'")  # Remove all rules associated with device
    curs.execute("DELETE FROM BatteryPercentage WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM SignalPercentage WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM TemperatureCelsius WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Presence WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM PowerReadingW WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM EnergyConsumedWh WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM EnergyGeneratedWh WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Events WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Devices WHERE devKey="+str(devKey))
    db.commit() # Flush db to disk immediately

# === Rules ===
def GetRules(item):
    global curs
    ruleList = []
    curs.execute("SELECT * FROM Rules WHERE rule LIKE '%"+item+"%'") # NB LIKE is already case-insensitive, so no need for COLLATE NOCASE
    for row in curs:
        ruleList.append(row[0]) # Build a list of all rules that mention item
    return ruleList

# === AppState ===
def GetAppState(item):
    global curs
    curs.execute("SELECT Value FROM AppState WHERE Name=\""+item+"\" COLLATE NOCASE")
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetAppState(item, val):
    global curs, flushDB
    curs.execute("INSERT OR REPLACE INTO AppState VALUES(\""+item+"\", \""+val+"\")") # Run the update
    flushDB = True # Batch up the commits

def DelAppState(item):
    global curs, flushDB
    curs.execute("DELETE FROM AppState WHERE Name=\""+item+"\" COLLATE NOCASE")
    flushDB = True # Batch up the commits

