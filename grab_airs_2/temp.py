#13-10

from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=50, timeout=50)
nowTime = datetime.now()
departures = []
arrivals = []
urlNGO = "http://www.centrair.jp/en/flight_information/today/result/"


GO_TO_GATE = "go to gate"
CHECK_IN = "check-in"
BOARD_SOON = "board soon"
ARRIVING = "arriving"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"


ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"

GATE_OPEN = "gate open"

SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"

def fixStatus(status):
    return {
        SCHEDULED: SCHEDULED,
        DELAYED: DELAYED,
        CANCELLED: CANCELLED,
        CHECKIN: CHECKIN,
        BOARDING: BOARDING,
        OUTGATE: OUTGATE,
        DEPARTED: DEPARTED,
        EXPECTED: EXPECTED,
        LANDED: LANDED,

        BOARD_SOON:SCHEDULED,
        ARRIVING:EXPECTED,
        CHECK_IN:CHECKIN,
        GO_TO_GATE:BOARDING,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")


def getFullDate(hourMinute):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=nowTime.day, hour=h, minute=m, second=0)

    if h < 4:
        notFormatedTime += timedelta(days=1)
    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentNGO(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        rawStatus = str(el.select('.//td[5]').text())
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""

    if status == "":
        status = SCHEDULED

    try:
        timeString = str(el.select('.//td[1]').text())
        rawScheduled = ""
        additionalTime = ""

        indexOfFirstParenthesis = timeString.find("(")
        if indexOfFirstParenthesis > 0:
            rawScheduled = timeString[:indexOfFirstParenthesis - 1]
            additionalTime = timeString[indexOfFirstParenthesis + 1:indexOfFirstParenthesis + 6]
        else:
            rawScheduled = timeString
        scheduled = getFullDate(rawScheduled)

        if additionalTime != "":
            additionalTime = getFullDate(additionalTime)
            if status == LANDED or status == DEPARTED:
                actual = additionalTime
            else:
                estimated = additionalTime
    except:
        scheduled = ""
        actual = ""
        estimated = ""

    try:
        flightno = el.select('.//td[3]/ul/li[1]/span[2]').text()

        theEnd = False
        i = 1
        while not theEnd:
            try:
                i += 1
                addFlight = el.select('.//td[3]/ul/li[' + str(i) + ']/span[2]').text()
                codeShares.append(addFlight)
            except:
                theEnd = True
                break
    except:
        flightno = ""
        codeShares = []

    try:
        gate = str(el.select('.//td[4]').text())
    except:
        gate = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if actual != "":
        result["actual"] = actual
    if estimated != "":
        result["estimated"] = estimated
    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    if gate != "":
        result["gate"] = gate
    return result



#international arrives
arrivalsInterFlightsParams  = {
    "didatype":"IA",
    "airport":0,
    "airline":0,
    "time":8888,
    "flightno":""
}
resp = g.go(urlNGO, post=arrivalsInterFlightsParams)

for el in g.doc.select('/html/body//article/table/tbody/tr'):
    arrival = getDataFromDocumentNGO(el)
    arrivals.append(arrival)


#domestic arrives
arrivalsDomesticFlightsParams  = {
    "didatype":"DA",
    "airport":0,
    "airline":0,
    "time":8888,
    "flightno":""
}
resp = g.go(urlNGO, post=arrivalsDomesticFlightsParams)

for el in g.doc.select('/html/body//article/table/tbody/tr'):
    arrival = getDataFromDocumentNGO(el)
    arrivals.append(arrival)


# international departure
departuresInterFlightsParams  = {
    "didatype":"ID",
    "airport":0,
    "airline":0,
    "time":8888,
    "flightno":""
}
resp = g.go(urlNGO, post=departuresInterFlightsParams)

for el in g.doc.select('/html/body//article/table/tbody/tr'):
    departure = getDataFromDocumentNGO(el)
    departures.append(departure)


# domestic departure
departuresDomesticFlightsParams  = {
    "didatype":"DD",
    "airport":0,
    "airline":0,
    "time":8888,
    "flightno":""
}
resp = g.go(urlNGO, post=departuresDomesticFlightsParams)

for el in g.doc.select('/html/body//article/table/tbody/tr'):
    departure = getDataFromDocumentNGO(el)
    departures.append(departure)

resultNGO = {}
resultNGO["airport_id"] = "NGO"
resultNGO["departures"] = departures
resultNGO["arrivals"] = arrivals

jsonResult = json.dumps(resultNGO)
print jsonResult