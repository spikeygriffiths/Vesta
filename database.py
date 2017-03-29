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
    #if eventId == events.ids.NEWDAY:
    #    curs.execute("DELETE FROM Events WHERE timestamp <= date('now', '-7 day')") # Flush all events older than a week to avoid filling database
# end of EventHandler

# === Status ===
def KillStatus():
    global curs
    curs.execute("DROP TABLE IF EXISTS Status")
    curs.execute("CREATE TABLE Status (devIdx INTEGER,battery INTEGER, battery_time DATETIME,temperature INTEGER, temperature_time DATETIME,signal INTEGER, signal_time DATETIME,presence TEXT, presence_time DATETIME,FOREIGN KEY(devIdx) REFERENCES Devices(devIdx))")

def InitStatus(devIdx):
    global curs, flushDB
    curs.execute("SELECT presence FROM Status WHERE devIdx="+ str(devIdx))
    rows = curs.fetchone()
    if rows == None:    # If row doesn't exist, create it now
        curs.execute("INSERT INTO Status DEFAULT VALUES")  # Insert blank row for status
        rowId = devIdx + 1  # NB Rely on Status table being created alongside Device, or at least in sequential order
        curs.execute("UPDATE Status SET devIdx="+str(devIdx)+" WHERE rowId="+str(rowId))
    flushDB = True # Batch up the commits

def SetStatus(devIdx, item, value):
    global curs, flushDB
    log.debug("Setting status for "+item+" with "+str(value)+" for "+str(devIdx))
    curs.execute("UPDATE Status SET "+item+"_time=datetime('now', 'localtime') WHERE devIdx="+str(devIdx))
    if type(value) is str:
        curs.execute("UPDATE Status SET "+item+"=\""+value+"\" WHERE devIdx="+str(devIdx))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Status SET "+item+"="+str(value)+" WHERE devIdx="+str(devIdx))
    flushDB = True # Batch up the commits.  Commit status table for web access

def GetStatus(devIdx, item): 
    global curs
    curs.execute("SELECT "+item+" FROM Status WHERE devIdx="+str(devIdx))
    rows = curs.fetchone()
    if rows != None:
        value = rows[0]
        curs.execute("SELECT "+item+"_time FROM Status WHERE devIdx="+str(devIdx))
        rows = curs.fetchone()
        time = datetime.strptime(rows[0], "%Y-%m-%d %H:%M:%S")
        #log.debug("value="+value+", time="+str(time))
        return value, time # Return value, time
    return None

# === Events ===
def NewEvent(devIdx, event):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(datetime('now', 'localtime'),(?), (?))", (event, devIdx))  # Insert event with local timestamp
    flushDB = True # Batch up the commits

def GetLatestEvent(devIdx):
    global curs
    curs.execute("SELECT value FROM Events devIdx=(?) ORDER BY TIMESTAMP DESC LIMIT 1", (devIdx));  # Get latest event of device
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

# === Groups === (Not implemented yet)
def GetGroupDevs(grpIdx):
    global curs
    curs.execute("SELECT devList FROM Groups WHERE grpIdx="+str(grpIdx));
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

# === Devices ===
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
    global curs
    if type(value) is str:
        curs.execute("UPDATE Devices SET "+item+"=\""+value+"\" WHERE devIdx="+str(devIdx))
    else: # Assume number (Integer or Float)
        curs.execute("UPDATE Devices SET "+item+"="+str(value)+" WHERE devIdx="+str(devIdx))
    flushDB = True # Batch up the commits

def GetDevIdx(item, value):
    global curs
    curs.execute("SELECT devIdx FROM Devices WHERE "+item+"=\""+value+"\"");
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def NewDevice():
    global curs
    numDevs = GetDevicesCount()
    curs.execute("INSERT INTO Devices DEFAULT VALUES")  # Insert blank row
    devIdx = numDevs # Because we want devIdx to start from 0, not 1 as rowId does
    rowId = numDevs +1
    curs.execute("UPDATE Devices SET devIdx="+str(devIdx)+" WHERE rowId="+str(rowId))
    InitStatus(devIdx)
    flushDB = True # Batch up the commits
    return devIdx    # Return new devIdx for newly added device

