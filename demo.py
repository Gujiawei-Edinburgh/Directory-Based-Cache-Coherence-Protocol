import sys
from component import Processor
from component import Memory
from component import ProcessorOptimization

def showCacheContent(topology):
    for key in topology.keys():
        topology[key].showCacheContent()

def main(argv):
    topology = {}
    # if len(argv) != 1:
    if len(argv) != 2:
        topology['P0'] = ProcessorOptimization("P0");topology['P1'] = ProcessorOptimization("P1")
        topology['P2'] = ProcessorOptimization("P2");topology['P3'] = ProcessorOptimization("P3")
    else:
        topology['P0'] = Processor("P0");topology['P1'] = Processor("P1")
        topology['P2'] = Processor("P2");topology['P3'] = Processor("P3")

    topology['P0'].setNeighbours(topology['P1'],topology['P3'])
    topology['P1'].setNeighbours(topology['P0'],topology['P2'])
    topology['P2'].setNeighbours(topology['P1'],topology['P3'])
    topology['P3'].setNeighbours(topology['P0'],topology['P2'])

    memory = Memory()
    UNCACHE = 0; SHARED = 1;EXCLUSIVE = 2 #block states
    Hit = 0; Invalid = 1; RdMiss = 2; WtMiss = 3 #miss type
    cacheInvalid = 0; cacheShared = 1; cacheModified = 2#cache states
    ADD = 1;REMOVE = 0

    file = open(argv[1])
    line = file.readline()
    #---statistics information---#
    latencyList = []
    totalAccess = 0
    privateAccess = 0
    remoteAccess = 0
    offChipAccess = 0
    repalcementWt = 0
    coherenceWt = 0
    invalidationSent = 0
    privateLatency = 0
    remoteLatency = 0
    offChipLatency = 0
    processorAccess = [0]*4
    processorRequest = [0]*4
    #---showState---#
    showExplanation = False
    while line:
        line = line.strip()
        if line == 'V' or line == 'v':
            showExplanation = bool(1-showExplanation)
            if showExplanation:
                print("switch on line-by-line explanation")
            else:
                print("switch off line-by-line explanation")
            line = file.readline()
            continue
        if line == 'P' or line == 'p':
            showCacheContent(topology)
            line = file.readline()
            continue
        if line == 'H' or line == 'h':
            print("Hit rate:","%.2f"%(privateAccess/totalAccess))
            line = file.readline()
            continue
        info = line.split()
        processor = topology[info[0]]
        operationType = info[1]
        address = int(info[2])
        if showExplanation:
            readOrWrite = 'read'
            if operationType == 'W':
                readOrWrite = 'write'
            print("a "+readOrWrite+" by "+processor.name+" to word "+str(address))
        latency = processor.operation(operationType,address)
        processorRequest[processor.getProcessorId()] += 1
        
        if processor.missType != Hit:
            latency += processor.sendMessageToMemory()
            temp =  memory.handleReplace(processor)
            if temp != 0:
                repalcementWt += 1
            latency += temp
            blockState = memory.getMemoryState(address)
            if blockState == UNCACHE:
                offChipAccess += 1
                if processor.missType == RdMiss:
                    memory.updateDirectoryState(address,SHARED)
                    memory.updateSharers(processor,address,ADD)
                    processor.updateCacheState(address,cacheShared)
                elif processor.missType == WtMiss:
                    memory.updateDirectoryState(address,EXCLUSIVE)
                    memory.updateSharers(processor,address,ADD,True)
                    processor.updateCacheState(address,cacheModified)

                latency += memory.getDataFromMemeory()
                latency += memory.forwardData()
                latency += processor.getDataFromCache()
                offChipLatency += latency

            elif blockState == SHARED:
                remoteAccess += 1
                if processor.missType == RdMiss:
                    memory.updateSharers(processor,address,ADD)
                    closest,farSharers = memory.getClosestAndFarSharers(processor,address,topology)
                    latency += memory.sendMessageToSharersAndRequester()
                    latency += 2 #closest's processor probe and forward data
                    latency += closest.sendMessageToProcessor(processor)
                    latency += processor.getDataFromCache()
                    processor.updateCacheState(address,cacheShared)
                elif processor.missType == WtMiss:
                    memory.updateDirectoryState(address,EXCLUSIVE)
                    closest,farSharers = memory.getClosestAndFarSharers(processor,address,topology)
                    memory.updateSharers(processor,address,ADD,True)
                    latency += memory.sendMessageToSharersAndRequester()
                    timeConsume = [0]*(len(farSharers) + 1)
                    jobList = [closest]+farSharers
                    if jobList[0] is not None:
                        for i in range(0,len(jobList)):
                            if i == 0 and processor.getCacheState(address) == cacheInvalid:
                                timeConsume[i] = 2
                            else:
                                timeConsume[i] = 1
                            jobList[i].updateCacheState(address,cacheInvalid)
                            timeConsume[i] += jobList[i].sendMessageToProcessor(processor)
                    invalidationSent += len(jobList)
                    latency += max(timeConsume)+processor.getDataFromCache()
                    processor.updateCacheState(address,cacheModified)
                remoteLatency += latency
            else:
                remoteAccess += 1
                if processor.missType == RdMiss:
                    owner = memory.getOwner(address,topology)
                    memory.updateDirectoryState(address,SHARED)
                    memory.updateSharers(processor,address,ADD)
                    latency += memory.sendMessageToSharersAndRequester()
                    latency += 2 # owner probe cache and access cache
                    owner.updateCacheState(address,cacheShared)
                    latency += owner.sendMessageToProcessor(processor)
                    latency += processor.getDataFromCache()
                    processor.updateCacheState(address,cacheShared)
                    latency += processor.sendMessageToMemory()
                    latency += memory.setDataToMemory()
                    coherenceWt += 1
                elif processor.missType == WtMiss:
                    owner = memory.getOwner(address,topology)
                    memory.updateSharers(processor,address,ADD,True)
                    latency += memory.sendMessageToSharersAndRequester()
                    latency += 1 # owner cache probe
                    owner.updateCacheState(address,cacheInvalid)
                    latency += owner.sendMessageToProcessor(processor)
                    latency += processor.getDataFromCache()
                    processor.updateCacheState(address,cacheModified)
                    invalidationSent += 1
                remoteLatency += latency
        else:
            privateAccess += 1
            privateLatency += latency
            processorAccess[processor.getProcessorId()] += 1
        totalAccess += 1
        latencyList.append(latency)
        line = file.readline()
    totalLatency = sum(latencyList)
    fileName = 'out_'+argv[1]
    file = open(fileName,'w')
    file.write("Private-accesses:"+str(privateAccess)+'\n')
    file.write("Remote-accesses:"+str(remoteAccess)+'\n')
    file.write("Off-chip-accesses:"+str(offChipAccess)+'\n')
    file.write("Total-accesses:"+str(totalAccess)+'\n')
    file.write("Replacement-writebacks:"+str(repalcementWt)+'\n')
    file.write("Coherence-writebacks:"+str(coherenceWt)+'\n')
    file.write("Invalidations-sent:"+str(invalidationSent)+'\n')
    file.write("Average-latency:"+str(totalLatency/len(latencyList))+'\n')
    if privateAccess != 0:
        file.write("Priv-average-latency:"+str(privateLatency/privateAccess)+'\n')
    else:
        file.write("Priv-average-latency:"+"infinite"+'\n')
    if remoteAccess != 0:
        file.write("Rem-average-latency:"+str(remoteLatency/remoteAccess)+'\n')
    else:
        file.write("Rem-average-latency:"+"infinite"+'\n')
    if offChipAccess != 0:
        file.write("Off-chip-average-latency:"+str(offChipLatency/offChipAccess)+'\n')
    else:
        file.write("Off-chip-average-latency:"+"infinite"+'\n')
    file.write("Total-latency:"+str(totalLatency)+'\n')
    file.close()

if __name__ == "__main__":
    main(sys.argv)