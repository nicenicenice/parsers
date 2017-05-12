import sys

def getFileByAirCode(code):
    code = str.lower(code)
    return {
        'ngo': "a_1",
        'kul': "a_2",
        'akl': "a_3",
        'tpe': "a_4",
        'khh': "a_5",
        'pqc': "a_6",
        'adl': "a_7"
    }.get(code, "a_all")


if len(sys.argv) > 1:
    secondArg = sys.argv[1]
    if len(secondArg) > 0:
        fileName = getFileByAirCode(secondArg)
        importedFile = __import__(fileName)
        if fileName != "a_all":
            print importedFile.jsonResult
else:
    importedFile = __import__("a_all")