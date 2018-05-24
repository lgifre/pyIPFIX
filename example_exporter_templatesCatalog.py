import argparse, logging, signal, sys, json
from Lib._Configuration import _Configuration
from Lib.ParameterChecking import checkType, checkAttr
from Lib.LoggerConfigurator import LoggerConfigurator
from Protocols.IPFIX.Session import Session
from Protocols.IPFIX.Exporter import Exporter
from Protocols.IPFIX.Message import Message
from Protocols.IPFIX.TemplatesCatalog import TemplatesCatalog
from Protocols.IPFIX.DataRecord import DataRecord

class Configuration(_Configuration):
    def _validate(self):
        checkType('config', (dict,), self.data)
        LoggerConfigurator.checkConfiguration(checkAttr('logger', self.data))
        TemplatesCatalog.checkConfiguration(checkAttr('templatesCatalog', self.data))
        Exporter.checkConfiguration(checkAttr('ipfixExporter', self.data))

ipfixExporter = None

def stop():
    global ipfixExporter
    logging.getLogger(__name__).info('Terminating IPFIX Exporter...')
    if(ipfixExporter is not None): ipfixExporter.stop()

def signalHandler(signal, frame):
    logging.getLogger(__name__).info('[signalHandler] You pressed Ctrl+C!')
    stop()

def main():
    global ipfixExporter
    signal.signal(signal.SIGINT, signalHandler)
    signal.signal(signal.SIGTERM, signalHandler)

    loggerConfig = LoggerConfigurator()
    try:
        # ----- Read Configuration ---------------------------------------------------
        parser = argparse.ArgumentParser(description='IPFIXExporter')
        parser.add_argument('config', metavar='config', type=argparse.FileType('r'), help='configuration file')
        args = parser.parse_args()
        config = Configuration.createFromString(args.config.read()).get()

        # ----- Configure Logger -----------------------------------------------------
        loggerConfig.configure(config['logger'])
        logger = logging.getLogger(__name__)
        logger.info('Starting IPFIX Exporter...')

        # ----- Configure Templates Catalog ------------------------------------------
        templatesCatalog = TemplatesCatalog()
        templatesCatalog.configure(config['templatesCatalog'])

        # ----- Prepare IPFIX Exporter -----------------------------------------------
        obsDomainId = 0
        ipfixSession = Session()
        ipfixSession.getDomain(obsDomainId)
        ipfixExporter = Exporter(ipfixSession)
        ipfixExporter.configure(config['ipfixExporter'])
        ipfixExporter.start()
        templatesCatalog.injectAllTemplates(ipfixExporter)

        
        logging.getLogger(__name__).info('Terminating IPFIX Exporter...')
        ipfixExporter.stop()
    except Exception as e:
        stop()
        logging.getLogger(__name__).exception(e)
        return(1)

    return(0)

if(__name__ == '__main__'):
    sys.exit(main())
