from grab import Grab
from datetime import datetime, timedelta
import json

g = Grab(connect_timeout=50, timeout=50)

urlAOIArrivals = "http://www.aeroportomarche.it/en/Passengers/Flights-info/Real-time-flights"

resp = g.go(urlAOIArrivals)

def getFullDate(hourMinute, justToday=False):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    if justToday == False:
        if h < nowTime.hour or (h == nowTime.hour and m < nowTime.minute):
            correctDate += timedelta(days=1)

    notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

LANDED = "landed"
DEPARTED = "departed"
ATTERRATO = "atterrato"
PARTITO = "partito"
SCHEDULED = "scheduled"
BOARDING = "boarding"
IMBARCO = "imbarco"
CANCELLATO = "cancellato"
CANCELLED = "cancelled"

departures = []
arrivals = []

def fixStatus(status):
    return {
        ATTERRATO: LANDED,
        PARTITO: DEPARTED,
        IMBARCO:BOARDING,
        CANCELLATO:CANCELLED
    }.get(status, "")


def getDataFromDocumentAOI(xPath):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""

    try:
        flightno = g.doc.select(xPath + '//td[3]').text()
    except:
        flightno = ""
    try:
        scheduled = getFullDate(g.doc.select(xPath + '//td[4]').text(), True)
    except:
        scheduled = ""
    try:
        estimated = getFullDate(g.doc.select(xPath + '//td[5]').text(), True)
    except:
        estimated = ""
    try:
        rawStatus = str.lower(g.doc.select(xPath + '//td[6]').text())
        status = fixStatus(rawStatus)
    except:
        status = ""
        rawStatus = ""

    if len(status) <= 0:
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        result["estimated"] = estimated

    return result


theEnd = False
i = 1
while not theEnd:
    xPath = '//*[@id="voliPartenze"]/thead/following-sibling::tr[' + str(i) + ']'
    try:
        trHtml = g.doc.select(xPath).html()
        i += 1
        arrival = getDataFromDocumentAOI(xPath)
        arrivals.append(arrival)
    except:
        theEnd = True
        break


theEnd = False
i = 1
while not theEnd:
    xPath = '//*[@id="dnn_ctr752_ModuleContent"]//table/thead/following-sibling::tr[' + str(i) + ']'
    try:
        trHtml = g.doc.select(xPath).html()
        i += 1
        departure = getDataFromDocumentAOI(xPath)
        departures.append(departure)
    except:
        theEnd = True
        break


result = {}
result["airport_id"] = "AOI"
result["departures"] = departures
result["arrivals"] = arrivals
jsonResult = json.dumps(result)
print jsonResult