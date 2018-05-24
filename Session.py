import logging
from Lib.Handlers.Callbacks import Callbacks as CallbacksHandler
from ObservationDomain import ObservationDomain
from Lib.ParameterChecking import checkType

class Session(CallbacksHandler):
    CALLBACK_RECEIVED_MESSAGE = 'receivedMessage'
    CALLBACK_KINDS = [
        CALLBACK_RECEIVED_MESSAGE
    ]
    
    def __init__(self):
        CallbacksHandler.__init__(self, Session.CALLBACK_KINDS)
        self.obsDomains = {}
    
    def hasDomain(self, obsDomainId):
        return(self.obsDomains.has_key(obsDomainId))
    
    def getDomain(self, obsDomainId):
        if(not self.obsDomains.has_key(obsDomainId)):
            self.obsDomains[obsDomainId] = ObservationDomain(obsDomainId)
        return(self.obsDomains[obsDomainId])

    def getDomainIds(self):
        return(self.obsDomains.keys())
    
    def readMessage(self, rawData, clientAddress=None, clientPort=None):
        from Message import Message
        logger = logging.getLogger(__name__)
        message = None
        try:
            message = Message.read(self, rawData)
            domain = self.getDomain(message.observationDomainId)
            domain.updateCollectorTemplates(message)
            domain.updateCollectorOptionTemplates(message)
            self._runCallbacks(Session.CALLBACK_RECEIVED_MESSAGE, domain, message,
                               clientAddress, clientPort)
        except Exception as e:
            logger.exception(e)
        return(message)
    
    def writeMessage(self, message, rawData):
        from Message import Message
        logger = logging.getLogger(__name__)
        try:
            checkType('message', (Message,), message)
            message.write(rawData)
        except Exception as e:
            logger.exception(e)
        return(message)
