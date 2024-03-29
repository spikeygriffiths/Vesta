#!telegesis.py

# Standard Python modules
import serial
from datetime import datetime
import time
from collections import deque
# App-specific Python modules
import vesta
import devices
import myqueue
import iottime
import log
import events
import database
import config
import zcl

ser = 0
expectOurEui = False
txBuf = deque([])    # Nothing to transmit initially
rxBuf = deque([])
ourChannel = "Unknown"
ourPowLvl = "Unknown"
ourPan = "Unknown"
ourExtPan = "Unknown"

def HandleSerial(ser):
    global txBuf, rxBuf
    while ser.inWaiting():
        try:
            telegesisInLine = str(ser.readline(),'utf-8').rstrip('\r\n')    # Rely on timeout=0 to return immediately, either with a line or with None
        except:
            database.NewEvent(0, "Serial port problem")
            vesta.Restart()
        rxBuf.append(telegesisInLine)  # Buffer this for subsequent processing in main thread
    while len(txBuf):
        atCmd = txBuf.popleft()
        wrAtCmd = atCmd + "\r\n"
        ser.write(wrAtCmd.encode())
        log.debug("Tx>"+atCmd)

def EventHandler(eventId, eventArg):
    global ser, txBuf, rxBuf
    if eventId == events.ids.INIT:
        serPort = config.Get("tty", '/dev/ttyUSB0')
        serSpeed = config.Get("baud", '19200')
        ser = serial.Serial(serPort, int(serSpeed), timeout=0)
        ser.flushInput()
        if database.GetDevicesCount()==0: # If we have no devices yet, then...
            devices.Add("0000", "N/A", "COO") # ...make sure we add this device as the first item before we try to use it!
        myqueue.EnqueueCmd(0, ["ATS63=0007", "OK"]) # Request RSSI & LQI on every received message, also disable automatic checkIn responses
        myqueue.EnqueueCmd(0, ["ATS0F=0400", "OK"]) # Use 0600 to set bit 9 (bit 10 already set) to get rawzcl responses so we can see schedule responses from thermostat
        if database.GetDeviceItem(0, "modelName") == None:
            myqueue.EnqueueCmd(0, ["ATI", "OK"]) # Request our EUI, as well as our Telegesis version
        myqueue.EnqueueCmd(0, ["AT+N", "OK"]) # Get network information, to see whether to start new network or use existing one
    elif eventId == events.ids.SECONDS:
        HandleSerial(ser)
        while len(rxBuf):
            Parse(rxBuf.popleft())
    elif eventId == events.ids.RADIO_INFO:
        print(ourChannel+","+ourPowLvl+","+ourPan+","+ourExtPan) # Formatted to make it easy to extract in php
    elif eventId == events.ids.INFO:
        print("TxBuf: ", str(txBuf))
    # end eventId handler

def Parse(atLine):
    global expectOurEui
    global ourChannel, ourPowLvl, ourPan, ourExtPan
    if atLine == "":
        return # Ignore blank lines
    if atLine[0:2] == 'AT':
        return # Exit immediately if line starts with AT, indicating an echo
    log.debug("Parsing:"+ atLine)
    atLine = atLine.replace(':',',') # Replace colons with commas
    atList = atLine.split(',') # Split on commas
    if atList[0] == 'OK':
        events.Issue(events.ids.RXOK)
    elif expectOurEui == True and len(atList[0])==16: # If we're expecting an EUI and it's the correct length
        database.SetDeviceItem(0, "eui64", atList[0])
        expectOurEui = False
    elif atList[0] == "ERROR":
        errNo = None
        if len(atList) > 1:
            try:
                errNo = int(atList[1],16)   # Might be junk - have seen all sorts of nonsense from Telegesis stick here
            except ValueError:
                pass    # Just use default value of errNo
        events.Issue(events.ids.RXERROR, errNo) # See if anyone cares about the error
    elif atList[0] == "SED" or atList[0] == "FFD" or atList[0] == "ZED":
        events.Issue(events.ids.DEVICE_ANNOUNCE, atList) # Tell system that device has (re-)joined        
    elif atList[0] == 'CHECKIN':
        events.Issue(events.ids.CHECKIN, atList) # Tell devices that device is about to poll for data
    elif atList[0] == 'TOGGLE' or atList[0] == 'ON' or atList[0] == 'OFF':
        events.Issue(events.ids.BUTTON, atList) # Tell rules engine
    elif atList[0] == 'ZONESTATUS':
        events.Issue(events.ids.TRIGGER, atList) # Tell rules engine
    elif 0 == atList[0].find("Telegesis"):
        database.SetDeviceItem(0, "manufName", atList[0])
    elif 0 == atList[0].find("CICIE"):
        database.SetDeviceItem(0, "modelName", atList[0])
        expectOurEui = True # Following EUI has no prefix - we just have to know that it follows the CICIE line
    elif atList[0] == "+N=COO":
        ourChannel = atList[1]
        ourPowLvl = atList[2]
        ourPan = atList[3]
        ourExtPan = atList[4]
    elif atList[0] == "+N=NoPAN": # No PAN means we need to set up the network and add ourselves
        myqueue.EnqueueCmd(0, ["AT+EN", "OK"]) # Start new network
    elif atList[0] == "JPAN":  # After Establish Network (AT+EN) has finished
        ourChannel = atList[1]
        ourPan = atList[2]
        ourExtPan = atList[3]
    else:
        events.Issue(events.ids.RXMSG, atList)
    # end Parse

def ByteSwap(val): # Assumes val is 16-bit int for now
    loVal = val & 0xff
    hiVal = val >> 8
    return hiVal + (256 * loVal) # Correct endianess when reading or writing raw Zigbee

def StrByteSwap(str):   # Assume simple 4-char string (16-bit Hex)
    if len(str)==4:
        return str[2:4]+str[0:2]
    elif len(str)==8:
        return str[6:8]+str[4:6]+str[2:4]+str[0:2]
    else:
        return str # Don't know what to do here

def Leave(nwkId):    # Tell device to leave the network
    TxCmd("AT+DASSR:"+nwkId)

def TxCmd(cmd):  # Takes command to send
    txBuf.append(cmd)  # Append command

def SetTime(): # Set time up for HA devices to synchronise to
    timeVal = datetime.now()
    timeVal = time.mktime(timeVal.timetuple())
    zigBeeTime = iottime.ToZigbee(timeVal)   # Get local time in Unix epoch (1/Jan/1970) and convert it to Zigbee standard
    myqueue.EnqueueCmd(0, ["AT+SETTIME:{:08X}".format(int(zigBeeTime)), "OK"]) #  Set time in CICIE ready for setting up time server

def TxReadDevAttr(devKey, clstrId, attrId):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    ep = database.GetDeviceItem(devKey, "endPoints")
    cmdRsp = ReadAttr(nwkId, ep, clstrId, attrId)
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def TxWriteAttr(devKey, clstrId, attrId, attrType, attrVal):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    ep = database.GetDeviceItem(devKey, "endPoints")
    cmdRsp = WriteAttr(nwkId, ep, clstrId, attrId, attrType, attrVal)
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def TxReportAttr(devKey, clstrId, attrId, attrType, attrVal):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    ep = database.GetDeviceItem(devKey, "endPoints")
    cmdRsp = ReportAttr(nwkId, ep, clstrId, attrId, attrType, attrVal)
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def TxReadAttrRsp(devKey, clstrId, attrId, attrType, attrVal):
    nwkId = database.GetDeviceItem(devKey, "nwkId")
    if nwkId == None:
        return # Make sure it's a real device before continuing (it may have just been deleted)
    ep = database.GetDeviceItem(devKey, "endPoints")
    cmdRsp = ReadAttrRsp(nwkId, ep, clstrId, attrId, attrType, attrVal)
    myqueue.EnqueueCmd(devKey, cmdRsp)   # Queue up command for sending via devices.py

def ReadAttr(nwkId, ep, clstrId, attrId): # NB All args as hex strings
    return ("AT+READATR:"+nwkId+","+ep+",0,"+clstrId+","+attrId, "RESPATTR")

def WriteAttr(nwkId, ep, clstrId, attrId, attrType, attrVal):   # All args are hex strings
    return ("AT+WRITEATR:"+nwkId+","+ep+",0,"+clstrId+","+attrId+","+attrType+","+attrVal, "WRITEATTR") #  Set attribute in cluster

def ReportAttr(nwkId, ep, clstrId, attrId, attrType, attrVal):   # All args are hex strings
    frameCtl="08"
    seqId="00"
    return ("AT+RAWZCL:"+nwkId+","+ep+","+clstrId+","+frameCtl+seqId+zcl.Commands.ReportAttr+StrByteSwap(attrId)+attrType+StrByteSwap(attrVal), "DFTREP") #  Report attribute in cluster

def ReadAttrRsp(nwkId, ep, clstrId, attrId, attrType, attrVal):
    frameCtl="08"
    seqId="00"
    return ("AT+RAWZCL:"+nwkId+","+ep+","+clstrId+","+frameCtl+seqId+zcl.Commands.ReadAttrRsp+StrByteSwap(attrId)+attrType+StrByteSwap(attrVal), "DFTREP") #  Report attribute in cluster
