# database.py

import sqlite3
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
    if eventId == events.ids.NEWDAY:
        curs.execute("DELETE FROM Events WHERE timestamp <= date('now', '-7 day')") # Flush all events older than a week to avoid filling database
# end of EventHandler

def NewEvent(devIdx, item, value):
    global curs, flushDB
    latest = GetLatestEvent(devIdx, item)
    if latest != value: # Only update on change
        curs.execute("INSERT INTO Events VALUES(datetime('now'),(?), (?), (?))", (item, value, devIdx))  # Insert event with timestamp
        flushDB = True # Batch up the commits

def GetLatestEvent(devIdx, item):
    global curs
    curs.execute("SELECT value FROM Events WHERE item=(?) AND devIdx=(?) ORDER BY TIMESTAMP DESC LIMIT 1", (item, devIdx));  # Get latest event of correct type and device
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def GetDevicesCount():
    global curs
    curs.execute("SELECT COUNT(*) FROM Devices") # Get number of devices
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return 0

def GetDeviceItem(devIdx, item):
    global curs
    curs.execute("SELECT "+item+" FROM Devices WHERE devIdx="+str(devIdx));
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetDeviceItem(devIdx, item, value):
    UpdateDeviceUsingDevIdx(devIdx, item, value)
    flushDB = True # Batch up the commits

def GetDevIdx(item, value):
    global curs
    curs.execute("SELECT devIdx FROM Devices WHERE "+item+"=\""+value+"\"");
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def NewDevice(devId):
    global curs
    numDevs = GetDevicesCount()
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    rowId = numDevs +1
    if devId != None:
        UpdateDevice(rowId, "devIdx", rowId-1) # Because we want devIdx to start from 0, not 1 as rowId does
        UpdateDevice(rowId, "nwkId", devId)
    flushDB = True # Batch up the commits
    return rowId    # Return new devIdx for newly added device

def UpdateDevice(rowId, item, value):
    global curs
    if type(value) is str:
        curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE rowid="+str(rowId))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Devices SET "+item+"="+str(value)+" WHERE rowid="+str(rowId))

def UpdateDeviceUsingDevIdx(devIdx, item, value):
    rowId = GetRowIdFromItem("devIdx", devIdx)
    UpdateDevice(rowId, item, value)

def GetRowIdFromItem(name, value):
    global curs
    if type(value) is str:
        curs.execute("SELECT rowid FROM Devices WHERE "+name+"="+value)
    else: # Assume number (Integer or Float)
        curs.execute("SELECT rowid FROM Devices WHERE "+name+"="+str(value))
    rows = curs.fetchone()
    return rows[0]
    #if rows != None:
    #    return rows[0]
    #return None

