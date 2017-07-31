# database.py

import sqlite3
from datetime import datetime
# App-specific Python modules
import events
import log

db = None
curs = None
flushDB = False

def EventHandler(eventId, eventArg):
    global db, curs, flushDB
    if eventId == events.ids.PREINIT:
        db = sqlite3.connect("hubstuff.db")
        curs = db.cursor()
    if eventId == events.ids.SECONDS:
        if flushDB:
            db.commit() # Flush events to disk
            flushDB = False
# end of EventHandler

# === Status ===
def InitStatus(devKey):
    global curs, flushDB
    curs.execute("SELECT presence FROM Status WHERE devKey="+ str(devKey))
    rows = curs.fetchone()
    if rows == None:    # If row doesn't exist, create it now
        curs.execute("INSERT INTO Status DEFAULT VALUES")  # Insert blank row for status
        rowId = curs.lastrowid
        curs.execute("UPDATE Status SET devKey="+str(devKey)+" WHERE rowId="+str(rowId))
        flushDB = True # Batch up the commits

def SetStatus(devKey, item, value):
    global curs, flushDB
    #log.debug("Setting status for "+item+" with "+str(value)+" for "+str(devKey))
    curs.execute("UPDATE Status SET "+item+"_time=datetime('now', 'localtime') WHERE devKey="+str(devKey))
    if type(value) is str:
        curs.execute("UPDATE Status SET "+item+"=\""+value+"\" WHERE devKey="+str(devKey))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Status SET "+item+"="+str(value)+" WHERE devKey="+str(devKey))
    flushDB = True # Batch up the commits.  Commit status table for web access

def GetStatus(devKey, item): 
    global curs
    curs.execute("SELECT "+item+" FROM Status WHERE devKey="+str(devKey))
    rows = curs.fetchone()
    if rows != None:
        value = rows[0]
        curs.execute("SELECT "+item+"_time FROM Status WHERE devKey="+str(devKey))
        rows = curs.fetchone()
        if rows != None:
            time = datetime.strptime(rows[0], "%Y-%m-%d %H:%M:%S")
        else:
            time = "Unknown"
        #log.debug("value="+value+", time="+str(time))
        return value, time # Return value, time
    return None

# === Events ===
def NewEvent(devKey, event):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(datetime('now', 'localtime'),(?), (?))", (event, devKey))  # Insert event with local timestamp
    flushDB = True # Batch up the commits

def GetLatestEvent(devKey):
    global curs
    curs.execute("SELECT event FROM Events WHERE devKey="+str(devKey)+" ORDER BY TIMESTAMP DESC LIMIT 1")  # Get latest event of device
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

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
    curs.execute("SELECT devKeyList FROM Groups WHERE userName=\""+userName+"\"")
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
    curs.execute("SELECT devKey FROM Devices WHERE "+item+"=\""+value+"\"");
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

def GetDeviceItem(devKey, item):
    global curs
    curs.execute("SELECT "+item+" FROM Devices WHERE devKey="+str(devKey))
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetDeviceItem(devKey, item, value):
    global curs, flushDB
    if type(value) is str:
        curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE devKey="+str(devKey))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Devices SET "+item+"="+str(value)+" WHERE devKey="+str(devKey))
    flushDB = True # Batch up the commits

def NewDevice(nwkId, eui64, devType):
    global curs, db
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    rowId = curs.lastrowid
    log.debug("Newly inserted row is ID "+str(rowId))
    devKey = rowId # Just need a unique key
    curs.execute("UPDATE Devices SET devKey="+str(devKey)+" WHERE rowId="+str(rowId))   # Define device key first, since that's used everywhere!
    SetDeviceItem(devKey, "nwkId", nwkId)
    SetDeviceItem(devKey, "Username", "(New) "+nwkId)   # Default username of network ID, since that's unique
    SetDeviceItem(devKey,"devType",devType)    # SED, FFD or ZED
    SetDeviceItem(devKey,"eui64",eui64)
    InitStatus(devKey)
    db.commit() # Flush db to disk immediately
    return devKey    # Return new devKey for newly added device

def RemoveDevice(devKey):
    global curs, db
    #curs.execute("DELETE FROM Groups WHERE devKey="+str(devKey)) # This has to remove devKey from within each group's devKeyList
    curs.execute("DELETE FROM Status WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Events WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Devices WHERE devKey="+str(devKey))
    db.commit() # Flush db to disk immediately

