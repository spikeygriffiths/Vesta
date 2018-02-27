# database.py

import sqlite3
from datetime import datetime
import os
import os.path
import shutil   # For file copying of database
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
        db = sqlite3.connect("vesta.db")    # This will create a new database for us if it didn't previously exist
        curs = db.cursor()
        InitAll(db, curs)   # Add any new entries to database here
        Backup()
        flushDB = True # Batch up the commits
    if eventId == events.ids.SECONDS:
        if flushDB:
            try:
                db.commit() # Flush events to disk
                flushDB = False
            except:
                log.fault("Database couldn't commit")
    if eventId == events.ids.NEWDAY:
        Backup()
        FlushOldEvents()    # Flush old events to avoid database getting too big and slow
        FlushOldLoggedItems()
        GarbageCollect("BatteryPercentage")
        GarbageCollect("TemperatureCelsius")
        GarbageCollect("SignalPercentage")
        GarbageCollect("Presence")
        GarbageCollect("PowerReadingW")
        GarbageCollect("EnergyConsumedWh")
        GarbageCollect("EnergyGeneratedWh")
        GarbageCollect("Events")
        Defragment()    # Compact the database now that we've flushed the old items
        flushDB = True
    if eventId == events.ids.SHUTDOWN:
        db.commit() # Flush events to disk prior to shutdown
# end of EventHandler

def InitCore(db, curs):
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Devices (
    devKey INTEGER,
    userName TEXT,
    modelName TEXT,
    manufName TEXT,
    nwkId TEXT,
    eui64 TEXT,
    devType TEXT,
    endPoints TEXT,
    inClusters TEXT,
    outClusters TEXT,
    binding TEXT,
    reporting TEXT,
    iasZoneType TEXT,
    Unused INTEGER,
    firmwareVersion TEXT,
    batteryReporting TEXT,
    temperatureReporting TEXT,
    powerReporting TEXT,
    energyConsumedReporting TEXT,
    energyGeneratedReporting TEXT,
    checkInFrequency TEXT,
    pirSensitivity TEXT)""")
    # Check that we have new entries to Devices above
    if TableHasColumn(curs, "Devices", "batteryReporting") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN batteryReporting TEXT")    # Format of all xxxReporting is <minS>,<maxS>,<delta>
    if TableHasColumn(curs, "Devices", "temperatureReporting") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN temperatureReporting TEXT")
    if TableHasColumn(curs, "Devices", "powerReporting") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN powerReporting TEXT")
    if TableHasColumn(curs, "Devices", "energyConsumedReporting") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN energyConsumedReporting TEXT")
    if TableHasColumn(curs, "Devices", "energyGeneratedReporting") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN energyGeneratedReporting TEXT")
    if TableHasColumn(curs, "Devices", "checkInFrequency") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN checkInFrequency TEXT")
    if TableHasColumn(curs, "Devices", "pirSensitivity") == False:
        curs.execute("ALTER TABLE Devices ADD COLUMN pirSensitivity TEXT")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Groups (
    userName TEXT,
    devKeyList TEXT)""")
    curs.execute("CREATE TABLE IF NOT EXISTS Rules (rule TEXT)")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY,
    name varchar(64),
    passwordHash varchar(255),
    email varchar(64))""")
    curs.execute("CREATE UNIQUE INDEX IF NOT EXISTS name_UNIQUE ON users (name ASC)")
    curs.execute("CREATE UNIQUE INDEX IF NOT EXISTS email_UNIQUE ON users (email ASC)")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Config (
    item TEXT,
    value TEXT)""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Schedules (
    type TEXT,
    day TEXT,
    dailySchedule TEXT)""")

def InitAll(db, curs):
    InitCore(db, curs)  # Central tables of database
    # Now create all the logs of past actions, values and events
    curs.execute("""
    CREATE TABLE IF NOT EXISTS BatteryPercentage (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS TemperatureCelsius (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS SignalPercentage (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Presence (
    timestamp DATETIME, value TEXT, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS PowerReadingW (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS EnergyConsumedWh (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS EnergyGeneratedWh (
    timestamp DATETIME, value INTEGER, devKey INTEGER,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Events (
    timestamp DATETIME, event TEXT, devKey INTEGER, reason TEXT,
    FOREIGN KEY(devKey) REFERENCES Devices(devKey))""")
    curs.execute("""
    CREATE TABLE IF NOT EXISTS Variables (
    name TEXT, value TEXT, timestamp DATETIME)""")
    curs.execute("CREATE TABLE IF NOT EXISTS AppState (Name TEXT PRIMARY KEY, Value TEXT)")
    if TableHasColumn(curs, "Events", "reason") == False:
        curs.execute("ALTER TABLE Events ADD COLUMN reason TEXT")

def Backup():
    global curs # Main db
    shutil.copyfile("vesta.db", "backup.db")    # Firstly, backup whole database using filing system (from shutil module)
    if os.path.isfile("core.db"):
        os.unlink("core.db")    # Remove old copy while we build the new one, since we're INSERTing entries in copy_table()
    dbCore = sqlite3.connect("core.db")    # This will create a new database if it didn't previously exist
    cursCore = dbCore.cursor()
    InitCore(dbCore, cursCore)
    # Now copy all the entries in the core tables.  See www.snipplr.com/view/18471/
    copy_table("Devices", curs, cursCore)
    copy_table("Groups", curs, cursCore)
    copy_table("Rules", curs, cursCore)
    copy_table("Users", curs, cursCore)
    dbCore.commit() # Flush newly created database to filing system

def TableHasColumn(curs, table, column):
    curs.execute("PRAGMA table_info("+table+")")
    cols = curs.fetchall()
    for col in cols:
        #log.debug("col.name = " + str(col[1]))
        if col[1] == column:    # name is second item, after column number
            return True
    log.debug("Failed to find " + column + " in " + str(cols))
    return False

def GarbageCollect(table):
    global curs
    keyList = GetAllDevKeys()
    itemList = GetAllItemsFromTable("*", table)
    for item in itemList:
        if item != None and len(item) > 2:
            devKey = item[2]
            if devKey not in keyList:
                log.debug("Found unused devKey of "+str(devKey)+" in "+table)
                curs.execute("DELETE FROM "+table+" WHERE devKey=" + str(devKey))
                keyList.append(devKey)  # To avoid deleting it for all the other entries

# From http://snipplr.com/view/18471/
type_str = type('str')
type_datetime = type(datetime.now())
type_int = type(1)
type_float = type(1.0)
type_None = type(None)
 
def convert2str(record):
    res = []
    for item in record:
        if type(item)==type_None:
            res.append('NULL')
        elif type(item)==type_str:
            res.append('"'+item+'"')
        elif type(item)==type_datetime:
            res.append('"'+str(item)+'"')
        else:  # for numeric values
            res.append(str(item))
    return ','.join(res)
 
def copy_table(tab_name, src_cursor, dst_cursor):
    sql = 'select * from %s'%tab_name
    src_cursor.execute(sql)
    res = src_cursor.fetchall()
    for record in res:
        val_str = convert2str(record)
        try:
            sql = 'insert into %s values(%s)'%(tab_name, val_str)
            dst_cursor.execute(sql)
        except:
            log.debug("Couldn't copy table with value: "+val_str)

# === Miscellaneous ===
def GetFileSize():
    return os.stat("vesta.db").st_size

def Defragment():
    global curs
    curs.execute("VACUUM")  # Rebuild database in order to compress its file size
    flushDB = True # Commit newly-built table 

def GetAllItemsFromTable(item, table, condition = None):
    global curs
    itemList = []
    if condition == None:
        curs.execute("SELECT "+item+" FROM "+table)
    else:
        curs.execute("SELECT "+item+" FROM "+table+" WHERE "+condition)
    for row in curs:
        itemList.append(row[0])
    return itemList

# === Logged items ===

def LogItem(devKey, item, value):
    global curs, flushDB
    previousValue = GetLatestLoggedValue(devKey, item)
    if previousValue == None:
        if rules.isNumber(value):
            previousValue = value + 1    # Force values to be different
        else:
            previousvalue = "Not"+value  # Force values to be different
    if rules.isNumber(value):
        strVal = str(value)
    else:   # Assume string
        strVal = "\""+str(value)+"\""
    if previousValue != value:  # Only log the item if it has changed since last time.  Not a good idea for presence!
        log.debug("Setting "+item+" with "+str(value)+" for "+str(devKey)+" (changed from "+str(previousValue))
        dbCmd = "INSERT INTO "+item+" VALUES (datetime('now', 'localtime'),"+strVal+","+str(devKey)+")"
    else:  # Value unchanged, so update timestamp of the latest entry
        dbCmd = "UPDATE "+item+" SET timestamp=datetime('now', 'localtime') WHERE devKey="+str(devKey)+" ORDER BY timestamp DESC LIMIT 1"
    log.debug(dbCmd)
    curs.execute(dbCmd)
    flushDB = True # Batch up the commits.  Commit table for web access

def UpdateLoggedItem(devKey, item, value):
    global curs, flushDB
    previousValue = GetLatestLoggedValue(devKey, item)
    if rules.isNumber(value):
        strVal = str(value)
    else:   # Assume string
        strVal = "\""+str(value)+"\""
    if previousValue == None: # Ensure we have a value for later updating
        log.debug("Initialising "+item+" with "+str(value)+" for "+str(devKey))
        dbCmd = "INSERT INTO "+item+" VALUES (datetime('now', 'localtime'),"+strVal+","+str(devKey)+")"
    else:
        dbCmd = "UPDATE "+item+" SET timestamp=datetime('now', 'localtime'), value="+strVal+" WHERE devKey="+str(devKey)
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

def GetLatestLoggedTime(devKey, item):
    entry = GetLatestLoggedItem(devKey, item)
    if entry != None:
        return entry[1] # Just the timestamp
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
def NewEvent(devKey, event, reason=None):
    global curs, flushDB
    curs.execute("INSERT INTO Events VALUES(datetime('now', 'localtime'),(?), (?), (?))", (event, devKey, reason))  # Insert event with local timestamp
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
        if rows[0] != None:
            return rows[0]
        if defVal != None:
            SetDeviceItem(devKey, item, defVal) # If no entry, then update database...
            return defVal   # ... and return that default
    return None # Means no device entry found for this devKey, or no default supplied

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
    SetDeviceItem(devKey, "devType",devType)    # SED, FFD or ZED
    SetDeviceItem(devKey, "eui64",eui64)
    SetDeviceItem(devKey, "binding", "[]")
    db.commit() # Flush db to disk immediately
    return devKey    # Return new devKey for newly added device

def RemoveDevice(devKey):
    global curs, db
    #curs.execute("DELETE FROM Groups WHERE devKey="+str(devKey)) # This has to remove devKey from within each group's devKeyList
    userName = GetDeviceItem(devKey, "userName")
    curs.execute("DELETE FROM Rules WHERE rule LIKE '%"+userName+"%'")  # Remove all rules associated with device - Assumes names don't contain other names! (eg "TopLandingPir" contains "LandingPir")
    curs.execute("DELETE FROM BatteryPercentage WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM SignalPercentage WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM TemperatureCelsius WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Presence WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM PowerReadingW WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM EnergyConsumedWh WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM EnergyGeneratedWh WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Events WHERE devKey="+str(devKey))
    curs.execute("DELETE FROM Devices WHERE devKey="+str(devKey))
    Defragment()    # Compact the database now that we've removed everything
    db.commit() # Flush db to disk immediately

# === Rules ===
def GetRules(item):
    global curs
    ruleList = []
    curs.execute("SELECT Rowid,* FROM Rules WHERE rule LIKE '%"+item+"%'") # NB LIKE is already case-insensitive, so no need for COLLATE NOCASE
    ruleList = curs.fetchall()
    #for row in curs:
    #    ruleList.append(row[0]) # Build a list of all rules that mention item
    return ruleList

# === Config ===
def GetConfig(item):
    global curs
    curs.execute("SELECT Value FROM Config WHERE item=\""+item+"\" COLLATE NOCASE")
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetConfig(item, value):
    global curs, flushDB
    curs.execute("INSERT OR REPLACE INTO Config VALUES(\""+item+"\",\""+value+"\"")
    flushDB = True # Batch up the commits

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

# === Variables ===
def GetVarVal(name):
    global curs
    curs.execute("SELECT value FROM Variables WHERE name=\""+name+"\" COLLATE NOCASE")
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def GetVarTime(name):
    global curs
    curs.execute("SELECT timestamp FROM Variables WHERE name=\""+name+"\" COLLATE NOCASE")
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetVar(name, val):
    global curs, flushDB
    if GetVarVal(name) == None:
        log.debug("New variable "+name+" set to "+val)
        curs.execute("INSERT INTO Variables VALUES(\""+name+"\", \""+val+"\", datetime('now', 'localtime'))") # Create new
        newVal = GetVarVal(name)
        if newVal != None:
            log.debug(name+" from database holds "+val)
        else:
            log.debug(name+" wasn't set in database!")
    else:
        log.debug("Existing variable "+name+" set to "+val)
        curs.execute("UPDATE Variables SET value=\""+val+"\", timestamp=datetime('now', 'localtime') WHERE name=\""+name+"\" COLLATE NOCASE") # Update existing
    flushDB = True # Batch up the commits

def DelVar(name):
    global curs, flushDB
    log.debug("Removing "+name+" from database")
    curs.execute("DELETE FROM Variables WHERE name=\""+name+"\" COLLATE NOCASE")
    flushDB = True # Batch up the commits

# === Schedules ===
def GetSchedule(type, dow):
    global curs
    curs.execute("SELECT dailySchedule FROM Schedules WHERE type=\""+type+"\" and day=\""+dow+"\" COLLATE NOCASE")
    rows = curs.fetchone()
    if rows != None:
        return rows[0]
    return None

def SetSchedule(type, dow, schedule):
    global curs, flushDB
    if GetSchedule(type, dow) == None:
        log.debug("New schedule "+type+" "+dow+" set to "+schedule)
        curs.execute("INSERT INTO Schedules VALUES(\""+type+"\", \""+dow+"\", \""+schedule+"\")") # Create new schedule
    else:
        log.debug("Existing schedule "+type+" "+dow+" set to "+schedule)
        curs.execute("UPDATE Schedules SET dailySchedule=\""+schedule+"\" WHERE type=\""+type+"\" and day=\""+dow+"\" COLLATE NOCASE") # Update$
    flushDB = True # Batch up the commits
