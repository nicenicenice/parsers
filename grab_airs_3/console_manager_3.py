import sys

def getFileByAirCode(code):
    code = str.lower(code)
    return {
        'khv': "a_1",
        'krr': "a_2",
        'kuf': "a_3",
        'svx': "a_4",
        'vvo': "a_5",
        'arh': "a_6",
        'bkk': "a_7"
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