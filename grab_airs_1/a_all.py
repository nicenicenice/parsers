import sys
import json

arResult = []

importedFile1 = __import__("a_1")
importedFile2 = __import__("a_2")
importedFile2 = __import__("a_2")
importedFile3 = __import__("a_3")
importedFile4 = __import__("a_4")
importedFile5 = __import__("a_5")
importedFile6 = __import__("a_6")
importedFile7 = __import__("a_7")
importedFile8 = __import__("a_8")
importedFile9 = __import__("a_9")
importedFile10 = __import__("a_10")

arResult.append(importedFile1.jsonResult)
arResult.append(importedFile2.jsonResult)
arResult.append(importedFile3.jsonResult)
arResult.append(importedFile4.jsonResult)
arResult.append(importedFile5.jsonResult)
arResult.append(importedFile6.jsonResult)
arResult.append(importedFile7.jsonResult)
arResult.append(importedFile8.jsonResult)
arResult.append(importedFile9.jsonResult)
arResult.append(importedFile10.jsonResult)

print json.dumps(arResult)