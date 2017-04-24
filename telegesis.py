#!telegesis.py

# Standard Python modules
import serial
from collections import deque
# App-specific Python modules
import devices
import queue
import log
import events
import database
import config

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
    telegesisInLine = str(ser.readline(),'utf-8').rstrip('\r\n')    # Rely on timeout=0 to return imemdiately,either with a line or with None
    if telegesisInLine != None:
        rxBuf.append(telegesisInLine)  # Buffer this for subsequent processing in main thread
    if len(txBuf):
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
        queue.EnqueueCmd(0, ["ATS63=0007", "OK"]) # Request RSSI & LQI on every received message, also disable automatic checkIn responses
        if database.GetDeviceItem(0, "modelName") == None:
            queue.EnqueueCmd(0, ["ATI", "OK"]) # Request our EUI, as well as our Telegesis version
        queue.EnqueueCmd(0, ["AT+N", "OK"]) # Get network information, to see whether to start new network or use existing one
    elif eventId == events.ids.SECONDS:
        HandleSerial(ser)
        if len(rxBuf):
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
        events.Issue(events.ids.RXERROR, int(atList[1],16)) # See if anyone cares about the error
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
    else:
        events.Issue(events.ids.RXMSG, atList)
    # end Parse

def TxCmd(cmd):  # Takes command to send
    txBuf.append(cmd)  # Append command

def ReadAttr(devId, ep, clstrId, attrId): # NB All args as hex strings
    return ("AT+READATR:"+devId+","+ep+",0,"+clstrId+","+attrId, "RESPATTR")

