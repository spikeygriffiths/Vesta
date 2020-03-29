#!WifiSocket.py

import events
import report
import socket
import sys
import log

def EventHandler(eventId, eventArg):
    global s
    if events.ids.INIT == eventId:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = ''  #socket.gethostname()
        port = 12346 # One beyond command port of 12345
        s.bind((host, port))
        s.listen()
        log.debug("Listening on port" + str(port))
        s.setblocking(0) # Non-blocking socket
    if events.ids.SECONDS == eventId:
        try:
            client, addr = s.accept()
        except:
            return # Ignore any error, since that just means the client hasn't contacted us this time
        else:
            clientReq = client.recv(100).decode("utf-8")  # Let client tell us who they are, then use that to make up the report.  100 bytes for inbound text
            clientCmd = clientReq.split()
            log.debug("Received " + clientReq)
            if clientCmd[0] == "Get": # First item is always the text indicating what it wants the server to do
                dictText = report.MakeText(clientCmd[1]) # Keep time, etc. up to date
                if dictText:
                    log.debug("WiFi sending:" + dictText)
                    client.send(bytes(dictText, "utf-8"))
            # Allow for client sending "Cmd", to override boiler, etc.
            # Could send an events.ids.SOCKETCMD with clientCmd[1] as the arg
            client.close()
