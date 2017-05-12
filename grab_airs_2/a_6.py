# -*- coding: utf-8 -*-

#15-20
from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=90, timeout=90)
departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
dateParamsPattern = "%d.%m.%y"
nowTime = datetime.now()

CLOSED = "closed"
UNKNOWN = "unknown"
OPENING = "opening"
WAITING = "waiting"
ON_TIME = "on time"
CHECK_IN = "check in"
DELAY = "delay"

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

        CLOSED:BOARDING,
        DELAY:DELAYED,
        WAITING:SCHEDULED,
        OPENING:CHECKIN,
        CHECK_IN:CHECKIN,
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED,
        "":SCHEDULED
    }.get(status, UNKNOWN)


def getFullDate(hourMinute, day):

    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentPQC(el , day, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    check_in_desks = ""

    try:
        flightno = str(el.select('.//td[5]').text())
    except:
        flightno = ""

    try:
        rawStatus = el.select('.//td[7]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        rawScheduled = str(el.select('.//td[1]').text())
        scheduled = getFullDate(rawScheduled, day)
    except:
        scheduled = ""

    try:
        if status == LANDED or status == DEPARTED:
            rawActual = str(el.select('.//td[2]').text())
            actual = getFullDate(rawActual, day)
        else:
            rawEstimated = str(el.select('.//td[2]').text())
            estimated = getFullDate(rawEstimated, day)
    except:
        actual = ""
        estimated = ""

    if isDeparture:
        try:
            check_in_desks = str(el.select('.//td[6]').text())
        except:
            check_in_desks = ""

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
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    return result

datePatternFromPage = "%d/%m/%Y"
urlPQC = "http://phuquocairport.vn/en/flight-scheduled"
resp = g.go(urlPQC)

time = g.doc.select('//*[@id="leftContent_lbtoday"]').text()
todayDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="tabc2"]/table/tbody/tr'):
    arrival = getDataFromDocumentPQC(el, todayDateTime.day)
    arrivals.append(arrival)

for el in g.doc.select('//*[@id="tabc1"]/table/tbody/tr'):
    departure = getDataFromDocumentPQC(el, todayDateTime.day, True)
    departures.append(departure)

time = g.doc.select('//*[@id="leftContent_lbtoday1"]').text()
tomorrowDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="tabc4"]/table/tbody/tr'):
    arrival = getDataFromDocumentPQC(el, tomorrowDateTime.day)
    arrivals.append(arrival)

for el in g.doc.select('//*[@id="tabc3"]/table/tbody/tr'):
    departure = getDataFromDocumentPQC(el, tomorrowDateTime.day, True)
    departures.append(departure)

resultPQC = {}
resultPQC["airport_id"] = "PQC"
resultPQC["departures"] = departures
resultPQC["arrivals"] = arrivals

jsonResult = json.dumps(resultPQC)
#print jsonResult