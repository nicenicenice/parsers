import sys

def getFileByAirCode(code):
    code = str.lower(code)
    return {
        'mrv': "a_1",
        'msq': "a_2",
        'nux': "a_3",
        'ods': "a_4",
        'oms': "a_5",
        'oss': "a_6",
        'ovb': "a_7",
        'pee': "a_8",
        'pkc': "a_9",
        'rov': "a_10",
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
