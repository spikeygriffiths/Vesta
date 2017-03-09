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
    if eventId == events.ids.INFO:
        print("Whole db\n")
        for row in curs.execute("SELECT * FROM events"):
            print(row)
# end of EventHandler

def NewEvent(devIdx, item, value):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(date('now'), time('now'), (?), (?), (?))", (item, value, devIdx+1))  # Insert event
    flushDB = True # Batch up the commits

def ClearDevices():
    global curs
    curs.execute("DELETE FROM Devices")

def NewDevice(devId):
    global curs
    curs.execute("SELECT COUNT(*) FROM Devices") # Get number of rows before adding new one
    rows = curs.fetchone()
    print("Rows in devices: ", rows[0]) 
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    rowId = rows[0] +1
    if devId != None:
        UpdateDevice(rowId, "nwkId", devId)
    return rowId    # Return new devIdx for newly added device

def UpdateDevice(rowId, item, value):
    global curs
    print ("UpdateDevice, item="+item+", value="+value+" @rowId="+str(rowId))
    #curs.execute("UPDATE Devices SET (?)=(?) WHERE rowid=(?)", (item, value, rowId))
    curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE rowid="+str(rowId))

def UpdateDeviceUsingDevIdx(devIdx, item, value):
    rowId = devIdx + 2  # devIdx values start at 0, sqlite starts at 1.  First item is hub, hence +2
    UpdateDevice(rowId, item, value)

def GetRowIdFromItem(name, value):
    global curs
    curs.execute("SELECT * FROM Devices WHERE (?)=(?)", (name, value))
    rows = curs.fetchone()
    return rows[0]

