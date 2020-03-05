class Cache(object):
    def __init__(self,extraCacheLine=0):
        self.cachelineSize = 512 + extraCacheLine
        self.cacheline = [[0]*8]*self.cachelineSize
        self.states = [0]*self.cachelineSize
        self.tags = [-1]*self.cachelineSize

class Processor (object):
    def __init__(self,name,extraCacheLine=0):
        self.name = name
        self.cache = Cache(extraCacheLine)
        self.neighbours = []
        self.finishCache = False
        self.missType = 0 #missType = [0,1,2,3] means cache [Hit,Invalid,RdMiss,WtMiss]
        self.WtBackMdshare = 0 # WtBackMdShare = [0,1,2] means no back, back and md share
        self.replaceAddress = -1

    def show_name(self):
        print(self.name)

    def setNeighbours(self,n1,n2):
        self.neighbours.append(n1)
        self.neighbours.append(n2)
   
    def cacheProbe(self,operationType,address):
        mappingAdd = self.mappingCacheAddress(address)
        mappingTag = int(address / self.cache.cachelineSize)
        usingTag = self.cache.tags[mappingAdd]
        latency = 1
        mappingMissType = self.getMissType(operationType)
        self.WtBackMdshare = 0
        if self.cache.states[mappingAdd] == 0: # cache state is invalid
            self.missType = mappingMissType
        elif self.cache.states[mappingAdd] == 1: # cache state is share
            if usingTag != mappingTag and usingTag != -1:
                self.missType = mappingMissType
                self.WtBackMdshare = 2 # Mdshare
            elif operationType == 'R':
                self.missType = 0
            else:
                self.missType = 3
        elif self.cache.states[mappingAdd] == 2: # cache state is modified
            if usingTag != mappingTag and usingTag != -1:
                self.missType = mappingMissType
                self.WtBackMdshare = 1 # WtBack
            else:
                self.missType = 0
        self.cache.tags[mappingAdd] = mappingTag
        self.getRepalceAddress(usingTag,mappingAdd)
        return latency
    
    def getMissType(self,operationType):
        if operationType == 'R':
            return 2
        elif operationType == 'W':
            return 3
    
    def getRepalceAddress(self,usingTag,mappingAdd):
        if usingTag == -1:
            self.replaceAddress = -1
        else:
            self.replaceAddress = mappingAdd+usingTag*self.cache.cachelineSize

    def operation(self,operationType,address):
        latency = self.cacheProbe(operationType,address)
        if self.missType == 0:
            latency += self.getDataFromCache()
        return latency
    
    def getDataFromCache(self):
        latency = 1
        return latency
    
    def sendMessageToProcessor(self,processor):
        if processor in self.neighbours:
            latency = 3
        else:
            latency = 6
        return latency
    
    def sendMessageToMemory(self):
        latency = 3
        return latency
    
    def getProcessorId(self):
        return int(self.name[-1])
    
    def updateCacheState(self,address,newState):
        self.cache.states[self.mappingCacheAddress(address)] = newState
    
    def getCacheState(self,address):
        return self.cache.states[self.mappingCacheAddress(address)]
    
    def getNeighborId(self):
        neighbourId = []
        for each in self.neighbours:
            neighbourId.append(each.getProcessorId())
        return neighbourId
    
    def mappingCacheAddress(self,address):
        return address % self.cache.cachelineSize
    
    def getCacheStatePresent(self,stateNum):
        if stateNum == 0:
            return 'I'
        elif stateNum == 1:
            return 'S'
        elif stateNum == 2:
            return 'M'
    
    def showCacheContent(self):
        self.show_name()
        for index in range(self.cache.cachelineSize):
            tag = self.cache.tags[index]
            state = self.getCacheStatePresent(self.cache.states[index])
            print(index," ",tag," ",state)
  

class Directory(object):
    def __init__(self):
        self.block = [0]*17000
        self.states = [0]*17000
        self.shares = [[0] * 4 for _ in range(17000)]

class Memory(object):
    def __init__(self):
        self.memory = []
        self.directory = Directory()
    
    def getMemoryState(self,address):
        return self.directory.states[address]
    
    def getDataFromMemeory(self):
        latency = 10
        return latency
    
    def setDataToMemory(self):
        latency = 10
        return latency
    
    def forwardData(self): #data forward
        latency = 3
        return latency
    
    def updateDirectoryState(self,address,newState):
        self.directory.states[address] = newState
    
    def updateSharers(self,processor,address,isAdd,exclusive = False):
        if exclusive:
            for index in range(0,4):
                self.directory.shares[address][index] = 0
        self.directory.shares[address][processor.getProcessorId()] = (isAdd if (isAdd == 1) else 0)
    
    def handleReplace(self,processor):
        latency = 0
        if processor.replaceAddress == -1:
            pass
        elif processor.WtBackMdshare == 2:
            self.directory.shares[processor.replaceAddress][processor.getProcessorId()] = 0
            if 1 not in self.directory.shares[processor.replaceAddress]:
                self.directory.states[processor.replaceAddress] = 0
        else:          
            self.directory.shares[processor.replaceAddress][processor.getProcessorId()] = 0
            self.directory.states[processor.replaceAddress] = 0
            latency = self.getDataFromMemeory()
        return latency
    
    def getClosestAndFarSharers(self,processor,address,topology):
        neighbourId = processor.getNeighborId()
        shareVector = self.directory.shares[address]
        farSharers = []
        closestSharer = []
        closest = None
        for index in range(0,len(shareVector)):
            if index == processor.getProcessorId():
                continue
            if shareVector[index] != 0:
                if index in neighbourId:
                    closestSharer.append(topology['P'+str(index)])
                else:
                    farSharers.append(topology['P'+str(index)])
        if len(closestSharer) == 0 and len(farSharers) != 0:
            closest = farSharers[0]
            farSharers.remove(closest)
        elif len(closestSharer) != 0:
            closest = closestSharer[0]
            closestSharer.remove(closest)
            farSharers = farSharers + closestSharer
        return closest,farSharers
    
    def sendMessageToSharersAndRequester(self):
        return 3
    
    def getOwner(self,address,topology):
        vec = self.directory.shares[address]
        for i in range(0,len(vec)):
            if vec[i] == 1:
                return topology['P'+str(i)]  


class ProcessorOptimization(Processor):
    def __init__(self, name, extraCacheLine=0):
        super().__init__(name, extraCacheLine=extraCacheLine)
        self.content = {}
        self.inCache = False
        self.instructionQueue = [] # task list
    
    def mappingCacheAddress(self, address):
        self.inCache = False
        if address in self.content.keys(): # the address has already been in the cache
            self.inCache = True
            return self.content[address]
        for index in range(0,self.cache.cachelineSize): # it is a new address and get an empty address
            if self.cache.tags[index] == -1:
                return index
        return -1 # cache is full
    
    def cacheProbe(self,operationType,address):
        mappingAdd = self.mappingCacheAddress(address)#mapping belongs to range [0,511]
        replaceAdd = -1
        missingHit = False
        if mappingAdd == -1:
            missingHit = True
            replaceAdd = self.instructionQueue[0]
            mappingAdd = self.content[replaceAdd]

        self.content[address] = mappingAdd
        self.cache.tags[mappingAdd] = 1
        if not self.inCache:
            self.instructionQueue.append(address)
        self.WtBackMdshare = 0
        latency = 1
        mappingMissType = self.getMissType(operationType)
        if self.cache.states[mappingAdd] == 0: # cache state is invalid
            self.missType = mappingMissType
        elif self.cache.states[mappingAdd] == 1: # cache state is share
            if missingHit:
                self.WtBackMdshare = 2
            elif operationType == 'R':
                self.missType = 0
            else:
                self.missType = 3
        elif self.cache.states[mappingAdd] == 2: # cache state is modified
            if missingHit:
                self.WtBackMdshare = 1
            self.missType = 0
        self.getRepalceAddress(replaceAdd,mappingAdd)
        return latency
    
    def operation(self, operationType, address):
        return super().operation(operationType, address)+1 #extra SRAM latency 1 cycle
    
    def getRepalceAddress(self, usingTag, mappingAdd):
        self.replaceAddress = usingTag # in this sub class usingTag stands replaceAdd
    