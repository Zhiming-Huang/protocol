
# state : CLOSED, LISTEN, CTL_SEND, CTL_RCVD, HALF_CONNECTED, CONNECTED, CLOSE_SENT, CLOSE_RCVD
# event : startup, 
class state(object):
    def __init__(self, event = None, entity = None):
        pass

class CLOSED(state):
    def __init__(self, event = None, entity):
        if event == "build_a_connect":
            entity.fsmstate = "CTL_SENT"
            nextstate = CTL_SENT(entity)
            return nextstate
        elif event == "listen":
            entity.fsmstate = "LISTEN"
            nextstate = LISTEN(entity)
            return nextstate

class LISTEN(state):
    def __init__(self, event = None, entity):
        if entity.getpacket == "ctl packet":
            # if got an ctl packet, send ack to establish a half connection
            
            entity.fsmstate = "CTL_SENT"

class CTL_SENT(state):
    def handle(self, event = None, entity):
        if event == "build_a_connect":
            entity.fsmstate = "CTL_SENT"
