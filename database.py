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
#    if eventId == events.ids.NEWDAY:
#        curs.execute("DELETE FROM Events WHERE timestamp <= date('now', '-7 day')") # Flush all events older than a week to avoid filling database
# end of EventHandler

def NewEventUsingDevIdx(devIdx, item, value):
    NewEvent(devIdx+1, item, value)  # Insert event

def NewEvent(rowId, item, value):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(datetime('now'),(?), (?), (?))", (item, value, rowId))  # Insert event with timestamp
    flushDB = True # Batch up the commits

#def ClearDevices():
#    global curs
#    curs.execute("DELETE FROM Devices")

def GetDevicesCount():
    global curs
    curs.execute("SELECT COUNT(*) FROM Devices") # Get number of devices
    rows = curs.fetchone()
    return rows[0]

def GetDeviceItem(devIdx, item):
    global curs
    curs.execute("SELECT "+item+" FROM Devices WHERE devIdx="+str(devIdx));
    rows = curs.fetchone()
    return rows[0]  # Return value

def SetDeviceItem(devIdx, item, value):
    rowId = GetRowIdFromItem("devIdx", devIdx)
    UpdateDevice(rowId, item, value)

def GetDevIdx(item, value):
    global curs
    curs.execute("SELECT devIdx FROM Devices WHERE "+item+"="+value);
    rows = curs.fetchone()
    return rows[0]  # Return value

def NewDevice(devId):
    global curs
    numDevs = GetDevicesCount()
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    rowId = numDevs +1
    if devId != None:
        UpdateDevice(rowId, "nwkId", devId)
    return rowId    # Return new devIdx for newly added device

def UpdateDevice(rowId, item, value):
    global curs
    if type(value) is str:
        curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE rowid="+str(rowId))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Devices SET "+item+"="+str(value)+" WHERE rowid="+str(rowId))

def UpdateDeviceUsingDevIdx(devIdx, item, value):
    rowId = devIdx + 2  # devIdx values start at 0, sqlite starts at 1.  First item is hub, hence +2
    UpdateDevice(rowId, item, value)

def GetRowIdFromItem(name, value):
    global curs
    curs.execute("SELECT * FROM Devices WHERE (?)=(?)", (name, value))
    rows = curs.fetchone()
    return rows[0]

