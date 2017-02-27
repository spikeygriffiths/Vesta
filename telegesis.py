#!telegesis.py

# Standard Python modules
import serial
from collections import deque
# App-specific Python modules
import log
import events
import hubapp

ser = 0
expRsp = None
expRspTimeoutS = 0
expectOurEui = False
txBuf = deque([])    # Nothing to transmit initially
ourVersion = "Unknown"
ourSoc = "Unknown"
ourEui = "Unknown"
ourChannel = "Unknown"
ourPowLvl = "Unknown"
ourPan = "Unknown"
ourExtPan = "Unknown"

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, eventArg):
    global ser, expRsp, expRspTimeoutS
    if eventId == events.ids.INIT:
        ser = serial.Serial('/dev/ttyUSB0',19200, timeout=1) # Could get these TTY settings from a "settings.txt" file?
        ser.flushInput()
        expRsp = ""
        TxCmd(["ATS63=0007",  "OK"]) # Request RSSI & LQI on every received message, also disable automatic checkIn responses
        TxCmd(["ATI",  "OK"]) # Request our EUI, as well as our Telegesis version
        TxCmd(["AT+N", "OK"]) # Get network information, to see whether to start new network or use existing one
    elif eventId == events.ids.SECONDS:
        try:
            inWait = ser.inWaiting()
        except OSError: # Has given   File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 435, in inWaiting, s = fcntl.ioctl(self.fd, TIOCINQ, TIOCM_zero_str), OSError: [Errno 5] Input/output error
            inWait = False
            log.fault("ser.inWaiting() has failed")
        except serial:  # Has given:   File "/usr/lib/python3/dist-packages/serial/serialposix.py", line 460, in read raise SerialException('device reports readiness to read but returned no data (device disconnected?)') serial.serialutil.SerialException: device reports readiness to read but returned no data (device disconnected?)
            inWait = False
            log.fault("ser.inWaiting() has failed")
        if inWait:
            #try:
            Parse(str(ser.readline(),'utf-8').rstrip('\r\n'))
            #except:
            #    log.fault("ser.readline() failed")
        elif expRsp == "" and len(txBuf):
            atCmd, expRsp = txBuf.popleft()
            log.log("Tx>"+atCmd)
            expRspTimeoutS = 10
            atCmd = atCmd + "\r\n"
            ser.write(atCmd.encode())
        if expRsp != "" and expRspTimeoutS > 0:
            expRspTimeoutS = expRspTimeoutS - eventArg  # Expect eventArg to be 0.1
            if expRspTimeoutS <= 0:
                expRsp = ""
    elif eventId == events.ids.RXERROR:
        if ourEui == "Unknown":
            TxCmd(["ATI",  "OK"]) # Request our EUI, as well as our Telegesis version
        expRsp = ""
    elif eventId == events.ids.RXEXPRSP:
        expRsp = ""
    elif eventId == events.ids.INFO:
        if IsIdle == False:
            print("Telegesis: Not idle, waiting for expRsp:", expRsp)
        else:
            print("Telegesis: IsIdle")
            print("TxBuf: ", str(txBuf))
            print("expRsp: \""+ expRsp + "\"")
            if expRsp != "":
                print("expRspTimeoutS: ", expRspTimeoutS)
    # end eventId handler

def Parse(atLine):
    global expRsp, expectOurEui
    global ourVersion, ourSoc, ourEui
    global ourChannel, ourPowLvl, ourPan, ourExtPan
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
    # Not expecting any response, or it didn't match, so this must be spontaneous
    if expectOurEui == True and len(atList[0])==16: # If we're expecting an EUI and it looks plausible length
        ourEui = atList[0]
        log.log("Our EUI: "+ourEui)
        expectOurEui = False
    if atList[0] == 'OK':
        return
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
        ourSoc = atList[0]
        expectOurEui = True # Sometimes EUI follows Telegesis line directly
    elif 0 == atList[0].find("CICIE"):
        ourVersion = atList[0]
        log.log("Our version: "+ourVersion)
        expectOurEui = True # Following EUI has no prefix - we just have to know that it follows the CICIE line
    elif atList[0] == "+N=COO":
        ourChannel = atList[1]
        ourPowLvl = atList[2]
        ourPan = atList[3]
        ourExtPan = atList[4]
    else:
        events.Issue(events.ids.RXMSG, atList)
    # end Parse

def IsIdle():
    if ser.inWaiting() == 0 and expRsp == "" and len(txBuf) == 0:
        return True
    else:
        return False

def TxCmd(cmdRsp):  # Takes a list with two elements - command to send, and first word of last response to expect
    txBuf.append(cmdRsp)  # Append command and associated response as one item
    #log.log("Pushing Cmd:"+str(cmdRsp))

def ReadAttr(devId, ep, clstrId, attrId): # NB All args as hex strings
    return ("AT+READATR:"+devId+","+ep+",0,"+clstrId+","+attrId, "RESPATTR")

