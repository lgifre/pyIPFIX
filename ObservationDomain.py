import time #, logging
from Lib.ParameterChecking import checkInteger, checkType
from OptionTemplateRecord import OptionTemplateRecord
from TemplateRecord import TemplateRecord


class Sequentiation(object):
    def __init__(self):
        self.reset()

    def check(self, sequenceNumber, exportTimeUTC):
        #logger = logging.getLogger(__name__)
        #if(sequenceNumber != self.nextSequenceNumber):
        #    logger.warning('Unexpected Sequence Number. Got=%d Expected=%d' % (sequenceNumber, self.nextSequenceNumber))
        #if(exportTimeUTC < self.lastExportTimeUTC):
        #    logger.warning('Invalid Export Time. Got="%s" Expected>="%s"' % (
        #                    time.strftime('%Y/%m/%d %H:%M:%S', exportTimeUTC), time.strftime('%Y/%m/%d %H:%M:%S', self.lastExportTimeUTC)))
        pass

    def get(self): return(self.nextSequenceNumber, self.lastExportTimeUTC)

    def update(self, numRecords, exportTimeUTC):
        self.nextSequenceNumber += numRecords
        self.lastExportTimeUTC = exportTimeUTC
    
    def reset(self):
        self.nextSequenceNumber = 1
        self.lastExportTimeUTC = time.gmtime(0)

class ObservationDomain(object):
    def __init__(self, obsDomainId):
        checkInteger('obsDomainId', obsDomainId, 0)
        self.obsDomainId = obsDomainId
        self.collectorSeq = Sequentiation()
        self.collectorTemplates = {}
        self.collectorOptionTemplates = {}
        self.exporterSeq = Sequentiation()
        self.exporterTemplates = {}
        self.exporterOptionTemplates = {}
    
    def getId(self): return(self.obsDomainId)
    def getCollectorSequentiation(self): return(self.collectorSeq)
    def getExporterSequentiation(self): return(self.exporterSeq)
    
    def updateCollectorTemplate(self, template):
        checkType('template', (TemplateRecord,), template)
        if(self.collectorOptionTemplates.has_key(template.templateId)):
            raise Exception('Collector TemplateId(%d) is already defined as a Collector OptionTemplate' % (template.templateId))
        self.collectorTemplates[template.templateId] = template

    def updateCollectorOptionTemplate(self, optionTemplate):
        checkType('optionTemplate', (OptionTemplateRecord,), optionTemplate)
        if(self.collectorTemplates.has_key(optionTemplate.templateId)):
            raise Exception('Collector TemplateId(%d) is already defined as a Collector Template' % (optionTemplate.templateId))
        self.collectorOptionTemplates[optionTemplate.templateId] = optionTemplate

    def removeCollectorTemplate(self, templateId, exceptIfNotExists=False):
        checkInteger('templateId', templateId, 1)
        if(not self.collectorTemplates.has_key(templateId)):
            if(exceptIfNotExists):
                raise Exception('Collector TemplateId(%d) is not defined' % (templateId))
        else:
            del self.collectorTemplates[templateId]

    def removeCollectorOptionTemplate(self, optionTemplateId, exceptIfNotExists=False):
        checkInteger('optionTemplateId', optionTemplateId, 1)
        if(not self.collectorOptionTemplates.has_key(optionTemplateId)):
            if(exceptIfNotExists):
                raise Exception('Collector Option TemplateId(%d) is not defined' % (optionTemplateId))
        else:
            del self.collectorOptionTemplates[optionTemplateId]

    def hasCollectorTemplate(self, templateId):
        return(self.collectorTemplates.has_key(templateId))

    def hasCollectorOptionTemplate(self, optionTemplateId):
        return(self.collectorOptionTemplates.has_key(optionTemplateId))
    
    def getCollectorTemplate(self, templateId):
        if(not self.collectorTemplates.has_key(templateId)):
            raise Exception('Domain(%d) does not contain Collector Template with Id(%d)' % (self.obsDomainId, templateId))
        return(self.collectorTemplates[templateId])

    def getCollectorOptionTemplate(self, optionTemplateId):
        if(not self.collectorOptionTemplates.has_key(optionTemplateId)):
            raise Exception('Domain(%d) does not contain Collector OptionTemplate with Id(%d)' % (self.obsDomainId, optionTemplateId))
        return(self.collectorOptionTemplates[optionTemplateId])

    def getCollectorTemplateIds(self):
        return(self.collectorTemplates.keys())

    def getCollectorOptionTemplateIds(self):
        return(self.collectorOptionTemplates.keys())

    def updateCollectorTemplates(self, message):
        newTemplates = []
        for set_ in message.templateSets:
            for record in set_.records:
                self.updateCollectorTemplate(record)
                newTemplates.append(record)
        return(newTemplates)
    
    def updateCollectorOptionTemplates(self, message):
        newOptionTemplates = []
        for set_ in message.optionTemplateSets:
            for record in set_.records:
                self.updateCollectorOptionTemplate(record)
                newOptionTemplates.append(record)
        return(newOptionTemplates)

    def updateExporterTemplate(self, template):
        checkType('template', (TemplateRecord,), template)
        if(self.exporterOptionTemplates.has_key(template.templateId)):
            raise Exception('Exporter TemplateId(%d) is already defined as a Exporter OptionTemplate' % (template.templateId))
        self.exporterTemplates[template.templateId] = template

    def updateExporterOptionTemplate(self, optionTemplate):
        checkType('optionTemplate', (OptionTemplateRecord,), optionTemplate)
        if(self.exporterTemplates.has_key(optionTemplate.templateId)):
            raise Exception('Exporter TemplateId(%d) is already defined as a Exporter Template' % (optionTemplate.templateId))
        self.exporterOptionTemplates[optionTemplate.templateId] = optionTemplate
    
    def removeExporterTemplate(self, templateId, exceptIfNotExists=False):
        checkInteger('templateId', templateId, 1)
        if(not self.exporterTemplates.has_key(templateId)):
            if(exceptIfNotExists):
                raise Exception('Exporter TemplateId(%d) is not defined' % (templateId))
        else:
            del self.exporterTemplates[templateId]

    def removeExporterOptionTemplate(self, optionTemplateId, exceptIfNotExists=False):
        checkInteger('optionTemplateId', optionTemplateId, 1)
        if(not self.exporterOptionTemplates.has_key(optionTemplateId)):
            if(exceptIfNotExists):
                raise Exception('Exporter Option TemplateId(%d) is not defined' % (optionTemplateId))
        else:
            del self.exporterOptionTemplates[optionTemplateId]

    
    def hasExporterTemplate(self, templateId):
        return(self.exporterTemplates.has_key(templateId))

    def hasExporterOptionTemplate(self, optionTemplateId):
        return(self.exporterOptionTemplates.has_key(optionTemplateId))
    
    def getExporterTemplate(self, templateId):
        if(not self.exporterTemplates.has_key(templateId)):
            raise Exception('Domain(%d) does not contain Exporter Template with Id(%d)' % (self.obsDomainId, templateId))
        return(self.exporterTemplates[templateId])

    def getExporterOptionTemplate(self, optionTemplateId):
        if(not self.exporterOptionTemplates.has_key(optionTemplateId)):
            raise Exception('Domain(%d) does not contain Exporter OptionTemplate with Id(%d)' % (self.obsDomainId, optionTemplateId))
        return(self.exporterOptionTemplates[optionTemplateId])

    def getExporterTemplateIds(self):
        return(self.exporterTemplates.keys())

    def getExporterOptionTemplateIds(self):
        return(self.exporterOptionTemplates.keys())

    def updateExporterTemplates(self, message):
        newTemplates = []
        for set_ in message.templateSets:
            for record in set_.records:
                self.updateExporterTemplate(record)
                newTemplates.append(record)
        return(newTemplates)
    
    def updateExporterOptionTemplates(self, message):
        newOptionTemplates = []
        for set_ in message.optionTemplateSets:
            for record in set_.records:
                self.updateExporterOptionTemplate(record)
                newOptionTemplates.append(record)
        return(newOptionTemplates)
