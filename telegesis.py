# ./telegesis

# Standard Python modules
import serial
# App-specific Python modules
import events
import hubapp
ser = 0
expRsp = ""

if __name__ == "__main__":
    hubapp.main()

def EventHandler(eventId, arg):
    global ser
    if eventId == events.ids.INIT:
        ser = serial.Serial('/dev/ttyUSB0',19200, timeout=1)
    elif eventId == events.ids.SECONDS:
        numChars = ser.inWaiting()
        if numChars:
            Parse(str(ser.readline(),'utf-8').rstrip('\r\n'))
    # end eventId handler


def Parse(atLine):
    global expRsp
    if atLine == "":
        return # Ignore blank lines
    print ("Parsing:", atLine)
    if atLine[0:2] == 'AT':
        return # Exit immediately if line starts with AT, indicating an echo
    atLine = atLine.replace(':',',') # Replace colons with commas
    atList = atLine.split(',') # Split on commas
    #print("Processed line into ", atList)
    if expRsp != "":  # We're expecting a response, so see if this matches
        if atList.find(expRsp):
            print("Found expected response of ", expRsp, " in ", atList)
        expRsp = ""
    # Not expecting any response, or it didn't match, so this must be spontaneous
    if atList[0] == 'OK':
        return
    elif atList[0] == 'CHECKIN':
        events.Issue(events.ids.CHECKIN, atList) # Tell system
    elif atList[0] == 'TOGGLE':
        events.Issue(events.ids.BUTTON, atList) # Tell rules engine
    elif atList[0] == 'ZONESTATUS':
        events.Issue(events.ids.TRIGGER, atList) # Tell rules engine
    # end Parse

def TxCmd(atCmd):
    ser.writeLine(atCmd)
    expRsp = "OK"
