from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=90, timeout=90)


CHECK_IN = "check-in"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CANCELED = "canceled"
AIRBORNE = "airborne"
EN_ROUTE = "en route"

ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
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

datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

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

        CHECK_IN:CHECKIN,
        EN_ROUTE:EXPECTED,
        AIRBORNE: DEPARTED,
        CANCELED:CANCELLED,
        BOARDING_CLOSED:OUTGATE,
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")

def getFullDate(hourMinute, scheduleHour, day):

    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    if scheduleHour < 5 and h > 20:
        notFormatedTime -= timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()

def getDataFromDocumentOMS(el, isArrival=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    day = ""

    try:
        dayOfFlight = str(el.select('.//td[1]').text())
        dayOfFlight = int(dayOfFlight[:2])
    except:
        dayOfFlight = ""
    if dayOfFlight != "":
        day = dayOfFlight
    else:
        day = nowTime.day

    try:
        flightno = el.select('.//td[3]').text()
        flightno = flightno.encode("utf-8")
    except:
        flightno = ""

    if isArrival:
        try:
            rawScheduled = str(el.select('.//td[5]').text())
            scheduled = getFullDate(rawScheduled, rawScheduled[:2], day)
        except:
            scheduled = ""

        try:
            rawEstimated = str(el.select('.//td[6]').text())
            estimated = getFullDate(rawEstimated, rawScheduled[:2], day)
        except:
            estimated = ""

        try:
            rawActual = str(el.select('.//td[7]').text())
            actual = getFullDate(rawActual, rawScheduled[:2], day)
        except:
            actual = ""
    else:
        try:
            rawScheduled = str(el.select('.//td[6]').text())
            scheduled = getFullDate(rawScheduled, rawScheduled[:2], day)
        except:
            scheduled = ""

        try:
            rawActual = str(el.select('.//td[7]').text())
            actual = getFullDate(rawActual, rawScheduled[:2], day)
        except:
            actual = ""

    try:
        rawStatus = el.select('.//td[8]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    return result


urlOMSArrive = "http://oms.aero/media/en_arr.html"
resp = g.go(urlOMSArrive)

# arrivel

i = 0
for el in g.doc.select('//table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    arrival = getDataFromDocumentOMS(el, True)
    arrivals.append(arrival)


urlOMSDeparture = "http://oms.aero/media/en_dep.html"
resp = g.go(urlOMSDeparture)

i = 0
for el in g.doc.select('//table/tbody/tr'):
    i += 1
    if i == 1:
        continue
    departure = getDataFromDocumentOMS(el)
    departures.append(departure)

resultOMS = {}
resultOMS["airport_id"] = "OMS"
resultOMS["departures"] = departures
resultOMS["arrivals"] = arrivals

jsonResult = json.dumps(resultOMS)
#print jsonResult