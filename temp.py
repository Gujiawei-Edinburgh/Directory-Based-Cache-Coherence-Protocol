# mappingAdd = self.mappingCacheAddress(address)
#         mappingTag = int(address / self.cache.cachelineSize)
#         usingTag = self.cache.tags[mappingAdd]
#         latency = 1
#         mappingMissType = self.getMissType(operationType)
#         self.WtBackMdshare = 0
#         if self.cache.states[mappingAdd] == 0: # cache state is invalid
#             self.missType = mappingMissType
#         elif self.cache.states[mappingAdd] == 1: # cache state is share
#             if usingTag != mappingTag and usingTag != -1:
#                 self.missType = mappingMissType
#                 self.WtBackMdshare = 2 # Mdshare
#             elif operationType == 'R':
#                 self.missType = 0
#             else:
#                 self.missType = 3
#         elif self.cache.states[mappingAdd] == 2: # cache state is modified
#             if usingTag != mappingTag and usingTag != -1:
#                 self.missType = mappingMissType
#                 self.WtBackMdshare = 1 # WtBack
#             else:
#                 self.missType = 0
#         self.cache.tags[mappingAdd] = mappingTag
#         self.getRepalceAddress(usingTag,mappingAdd)