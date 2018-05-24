import os, json
from Lib.ParameterChecking import checkType, checkRegex, checkInteger, checkAttr
from Lib.FileTools import readFile
from Constants import VARIABLE_LENGTH, pen_alias
from FieldSpecifier import FieldSpecifier
from TemplateRecord import TemplateRecord

class TemplatesCatalog(object):
    
    def __init__(self):
        self.__templates = {}
    
    @staticmethod
    def checkConfiguration(config):
        checkType('config', (dict,), config)

        templatesDefinitionsFile = checkAttr('definitionsFile', config)
        if(not os.path.isfile(templatesDefinitionsFile)):
            raise Exception('templatesDefinitionsFile(%s) does not exist' % templatesDefinitionsFile)
        templatesDefinitions = json.loads(readFile(templatesDefinitionsFile))

        for strTemplateId,templateAttr in templatesDefinitions.iteritems():
            checkRegex('templateId', '[0-9]+', strTemplateId)
            checkInteger('templateId', int(strTemplateId), 256, 65535)
            checkType('templateAttr', (dict,), templateAttr)
            
            fields = checkAttr('fields', templateAttr)
            checkType('fields', (list,), fields)
            for field in fields:
                checkType('field', (dict,), field)
                name = checkAttr('name', field)
                checkRegex('name', '[a-zA-Z0-9]+', name)
                enterprise = checkAttr('enterprise', field)
                checkRegex('enterprise', '[a-zA-Z0-9]+', enterprise)
                pen = pen_alias.get(enterprise)
                length = field.get('length')
                checkInteger('length', length, minValue=1, maxValue=VARIABLE_LENGTH, allowNone=True)
                if(pen is None): raise Exception('Unknown Enterprise Alias(%s)' % enterprise)
                if(pen == -1):
                    FieldSpecifier.newIANA(name, length)
                else:
                    FieldSpecifier.newEnterprise(name, pen, length)

    def configure(self, config):
        TemplatesCatalog.checkConfiguration(config)
        
        templatesDefinitions = json.loads(readFile(config.get('definitionsFile')))

        self.__templates = {}
        for strTemplateId,templateAttr in templatesDefinitions.iteritems():
            templateId = int(strTemplateId)
            
            fields = []
            for field in templateAttr['fields']:
                name = field.get('name')
                pen = pen_alias.get(field.get('enterprise'))
                length = field.get('length')
                if(pen == -1):
                    fields.append(FieldSpecifier.newIANA(name, length))
                else:
                    fields.append(FieldSpecifier.newEnterprise(name, pen, length))

            self.__templates[templateId] = TemplateRecord.create(templateId, fields)
    
    def getTemplateIds(self): return(self.__templates.keys())
    
    def getTemplate(self, templateId):
        template = self.__templates.get(templateId)
        if(template is None): raise Exception('Template(%s) not defined' % str(templateId))
        return(template)

    def injectAllTemplates(self, entity, obsDomainId=None, templateIds=None, doRefreshTemplates=True):
        from Exporter import Exporter
        from Collector import Collector
        if(not isinstance(entity, (Exporter, Collector))): raise Exception('Invalid entity')
        
        session = entity.getSession()
        obsDomainIds = session.getDomainIds()
        if(len(obsDomainIds) == 0):
            raise Exception('No domain has been configured')
        
        if(obsDomainId is not None):
            if(obsDomainId not in obsDomainIds): return
            obsDomainIds = [obsDomainId]

        if(templateIds is None):
            templateIds = self.getTemplateIds()
        else:
            if(not isinstance(templateIds, (list, set))): raise Exception('Invalid templateIds')
            requestedTemplateIds = set(list(templateIds)) # remove duplicate templateIds
            availableTemplateIds = self.getTemplateIds()
            unavailableTemplateIds = list(requestedTemplateIds.difference(availableTemplateIds))
            if(len(unavailableTemplateIds) > 0): raise Exception('Unknown TemplateIds(%s)' % str(unavailableTemplateIds))
            templateIds = requestedTemplateIds
        
        isExporter = isinstance(entity, (Exporter,))
        isCollector = isinstance(entity, (Collector,))
        
        for obsDomainId in obsDomainIds:
            domain = session.getDomain(obsDomainId)
            for templateId in templateIds:
                template = self.__templates.get(templateId)
                if(isExporter): domain.updateExporterTemplate(template)
                if(isCollector): domain.updateCollectorTemplate(template)
        
        if(doRefreshTemplates):
            if(isCollector):
                raise Exception('Templates cannot be refreshed in Collector')
            if(not entity.isRunning()):
                raise Exception('Templates cannot be refreshed since Exporter is not running')
            entity.refreshTemplates(obsDomainId)
