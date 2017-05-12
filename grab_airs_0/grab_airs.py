import sys


def getFileByAirCode(code):
    code = str.lower(code)
    return {
        'abz': "air_1",
        'aba': "air_2",
        'aes': "air_3",
        'alg': "air_4",
        'amm': "air_5",
        'aio': "air_6",
        'arn': "air_7",
        'ath': "air_8",
        'cmn': "air_9",
        'cnx': "air_10",
    }.get(code, "all_air")


if len(sys.argv) > 1:
    secondArg = sys.argv[1]
    if len(secondArg) > 0:
        fileName = getFileByAirCode(secondArg)
        importedFile = __import__(fileName)
else:
    importedFile = __import__("all_air")