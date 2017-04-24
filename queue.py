# queue.py

# App-specific modules
import devices
import log

txQueue = [] # Queues of outbound messages & responses for each device

def Init(devKey):
    global txQueue
    devIndex = devices.GetIndexFromKey(devKey)
    txQueue.append([])  # Just append to this and assume it's parallel with the devIndex.  ToDo - can this be fixed to make the link less tenuous?

def EnqueueCmd(devKey, cmdRsp):
    global txQueue
    if cmdRsp:
        log.debug("Queuing "+cmdRsp[0]+"  for devKey "+str(devKey))
        devIndex = devices.GetIndexFromKey(devKey)
        txQueue[devIndex].insert(0, cmdRsp)     # Insert [cmd,rsp] at the head of device's txQueue

def Jump(devKey, cmdRsp):
    global txQueue
    if cmdRsp:
        log.debug("Jump-queuing "+cmdRsp[0]+"  for devKey "+str(devKey))
        devIndex = devices.GetIndexFromKey(devKey)
        txQueue[devIndex].append(cmdRsp)     # Append [cmd,rsp] at the head (thus force to the front) of device's txQueue

def DequeueCmd(devKey):
    global txQueue
    devIndex = devices.GetIndexFromKey(devKey)
    if IsEmpty(devKey):
        return None
    else:
        log.debug("Un-queuing item for devKey "+str(devKey))
        return txQueue[devIndex].pop()    # Get last element

def IsEmpty(devKey):
    devIndex = devices.GetIndexFromKey(devKey)
    return txQueue[devIndex] == []

