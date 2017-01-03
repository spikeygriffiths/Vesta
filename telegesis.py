#!telegesis.py

# Standard Python modules
import serial
from collections import deque
# App-specific Python modules
import log
import events
import hubapp
ser = 0
expRsp = ""
txBuf = deque([])    # Nothing to transmit initially

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    global ser, expRsp
    if eventId == events.ids.INIT:
        ser = serial.Serial('/dev/ttyUSB0',19200, timeout=1) # Could get these TTY settings from a "settings.txt" file?
        ser.flushInput()
        expRsp = ""
        TxCmd("ATS63=0007") # Request RSSI & LQI on every received message, also disable automatic checkIn responses
        #TxCmd("AT+N") # Get network information, to see whether to start new network or use existing one
    elif eventId == events.ids.SECONDS:
        if ser.inWaiting():
            Parse(str(ser.readline(),'utf-8').rstrip('\r\n'))
        elif expRsp == "" and len(txBuf):
            atCmd, expRsp = txBuf.popleft()
            log.log("Pop>"+atCmd)
            atCmd = atCmd + "\r\n"
            ser.write(atCmd.encode())
    elif eventId == events.ids.RXERROR:
        # Ignore error for now, but should probably handle it at some point
        expRsp = ""
    elif eventId == events.ids.RXEXPRSP:
        # Could handle multi-line responses here, meaning expRsp might not be empty
        expRsp = ""
    # end eventId handler

def Parse(atLine):
    global expRsp
    if atLine == "":
        return # Ignore blank lines
    if atLine[0:2] == 'AT':
        return # Exit immediately if line starts with AT, indicating an echo
    log.log("Parsing:"+ atLine)
    atLine = atLine.replace(':',',') # Replace colons with commas
    atList = atLine.split(',') # Split on commas
    #log.log("Processed line into "+ atList)
    if expRsp != "":  # We're expecting a response, so see if this matches
        if expRsp in atList:
            log.log("Found expected response of "+ expRsp+ " in "+ str(atList))
            events.Issue(events.ids.RXEXPRSP, atList)
        expRsp = ""
    # Not expecting any response, or it didn't match, so this must be spontaneous
    if atList[0] == 'OK':
        return
    elif atList[0] == "ERROR":
        events.Issue(events.ids.RXERROR, int(atList[1],16)) # See if anyone cares about the error
    elif atList[0] == "SED" or atList[0] == "FFD" or atList[0] == "ZED":
        events.Issue(events.ids.NEWDEV, atList) # Tell system that new device has (re-)arrived        
    elif atList[0] == 'CHECKIN':
        events.Issue(events.ids.CHECKIN, atList) # Tell system
    elif atList[0] == 'TOGGLE' or atList[0] == 'ON' or atList[0] == 'OFF':
        events.Issue(events.ids.BUTTON, atList) # Tell rules engine
    elif atList[0] == 'ZONESTATUS':
        events.Issue(events.ids.TRIGGER, atList) # Tell rules engine
    else:
        events.Issue(events.ids.RXMSG, atList)
    # end Parse

def TxCmd(atCmd, expRsp="OK"):
    cmdRsp = (atCmd, expRsp)
    txBuf.append(cmdRsp)  # Append command and associated response as one item
    log.log("Pushing Cmd:"+atCmd)

def ReadAttr(devId, ep, clstrId, attrId): # NB All args as hex strings
    return "AT+READATR:"+devId+","+ep+",0,"+clstrId+","+attrId

