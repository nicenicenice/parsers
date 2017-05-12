# -*- coding: utf-8 -*-

from grab import Grab
import json
from datetime import datetime, timedelta
import time

g = Grab(connect_timeout=90, timeout=90)

datePattern = "%Y-%m-%d %H:%M:%S"
dateUrlPattern = "%Y-%m-%d"
nowTime = datetime.now()
departures = []
arrivals = []

CHECK_IN_OPENNING_SOON = "check in opening soon"
CHECK_IN_CLOSED = "check in closed"
CHECK_IN_GO_SECURITY = "check in & go to security"
CHECK_IN_CLOSING = "check in closing"
CHECK_IN_NOT_OPEN_YET = "check in not open yet"
FINAL_CALL = "final call"

RESCHEDULED = "rescheduled"
NEW_TIME = "new time"
FLIGHT_CLOSED = "flight closed"
DEPARTING = "departing"

EARLY = "early"
GO_TO_GATE = "go to gate"
ON_TIME = "on time"
PROCESSING = "processing"
CHECK_IN = "check in"
CLOSED = "closed"

UNKNOWN = "unknown"
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
        PROCESSING:LANDED,
        ON_TIME:SCHEDULED,
        CHECK_IN:CHECKIN,
        GO_TO_GATE:BOARDING,
        CHECK_IN_CLOSED:BOARDING,
        CHECK_IN_GO_SECURITY:CHECKIN,
        CHECK_IN_CLOSING:CHECKIN,
        CHECK_IN_NOT_OPEN_YET:SCHEDULED,
        CHECK_IN_OPENNING_SOON:SCHEDULED,

        DEPARTING:OUTGATE,
        FLIGHT_CLOSED:BOARDING,
        CLOSED:BOARDING,
        FINAL_CALL:BOARDING,
        EARLY:SCHEDULED,
        NEW_TIME:DELAYED,
        RESCHEDULED:SCHEDULED,
        SCHEDULED: SCHEDULED,
        DELAYED: DELAYED,
        CANCELLED: CANCELLED,
        CHECKIN: CHECKIN,
        BOARDING: BOARDING,
        OUTGATE: OUTGATE,
        DEPARTED: DEPARTED,
        EXPECTED: EXPECTED,
        LANDED: LANDED,
        "":SCHEDULED
    }.get(status, UNKNOWN)

def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

def getDataFromDocumentAKL(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    day = ""
    dayString = ""

    try:
        flightnoString = str(el.select('.//td/div/div/div/div[2]/p[2]').text())
        idxComma = flightnoString.find(",")
        idxFirstSpace = flightnoString.find(" ")
        flightno = flightnoString[idxFirstSpace + 1:idxComma]
    except:
        flightno = ""

    try:
        rawScheduled = str(el.select('.//td/div/div/div/div[2]/div[1]/div[1]/span').text()) + " " + str(nowTime.year)
        rawDateTime = datetime.strptime(rawScheduled, '%I:%M%p %a, %d %b %Y')
        scheduled = rawDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
    #
        rawStatus = str.lower(el.select('.//td/div/div/div/div[2]/div[2]/div[1]/span').text())
        if rawStatus.find("check in opens at") >= 0 \
                or rawStatus.find("check in open in") >= 0 \
                or rawStatus.find("checkin opens") >= 0 \
                or rawStatus.find("check in opens") >= 0:
            status = SCHEDULED

        if status == "":
            status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED
    try:
        rawEstimated = str(el.select('.//td/div/div/div/div[2]/div[1]/div[2]/span').text())
        rawEstimated = rawEstimated + " " + str(rawDateTime.weekday()) + ", " \
                       + str(rawDateTime.day) \
                       + " " + str(rawDateTime.month) \
                       + " " + str(rawDateTime.year)
        rawDateTime = datetime.strptime(rawEstimated, '%I:%M%p %w, %d %m %Y')
        estimated = rawDateTime.strftime(datePattern)

        if rawStatus == NEW_TIME:
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            scheduleTimeStamp = getTimeStampFromDateTime(scheduleDateTime)
            estimatedDateTime = datetime.strptime(estimated, datePattern)
            estimatedTimeStamp = getTimeStampFromDateTime(estimatedDateTime)
            diff = abs(scheduleTimeStamp - estimatedTimeStamp)
            if diff >= 15 * 60:
                status = DELAYED
            else:
                status = SCHEDULED

        if status == LANDED or status == DEPARTED:
            actual = estimated
            estimated = ""
    except:
        estimated = ""
        actual = ""

    try:
        if el.select('.//td/div/div/div/div[2]/div[2]/div[2]/p').text() == "Gate":
            gate = el.select('.//td/div/div/div/div[2]/div[2]/div[2]/span').text()
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
    if gate != "":
        result["gate"] = gate
    return result


g = Grab(connect_timeout=70, timeout=70)
g.setup(headers={"X-Requested-With":"XMLHttpRequest"})
urlAKL = "https://www.aucklandairport.co.nz/ajax/AIA/Flight/FlightTable"
datePatternUrl = "%a, %d %b %y"

#ARRIVALS


#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayUrlDateParam = timeFourHourAgo.strftime(datePatternUrl)

    ADParams = {
        "leg": "Arrivals",
        "query": "",
        "board": "Domestic",
        "date": yesterdayUrlDateParam,
        "X-Requested-With": "XMLHttpRequest"
    }
    AIParams = {
        "leg": "Arrivals",
        "query": "",
        "board": "International",
        "date": yesterdayUrlDateParam,
        "X-Requested-With": "XMLHttpRequest"
    }

    resp = g.go(urlAKL, post=ADParams)
    for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
        arrival = getDataFromDocumentAKL(el)
        arrivals.append(arrival)
    resp = g.go(urlAKL, post=AIParams)
    for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
        arrival = getDataFromDocumentAKL(el)
        arrivals.append(arrival)


#now
urlDateParam = nowTime.strftime(datePatternUrl)
ADParams = {
    "leg": "Arrivals",
    "query": "",
    "board": "Domestic",
    "date": urlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}
AIParams = {
    "leg": "Arrivals",
    "query": "",
    "board": "International",
    "date": urlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}

resp = g.go(urlAKL, post=ADParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    arrival = getDataFromDocumentAKL(el)
    arrivals.append(arrival)
resp = g.go(urlAKL, post=AIParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    arrival = getDataFromDocumentAKL(el)
    arrivals.append(arrival)

#tomorrow
tomorrowTime = nowTime + timedelta(days=1)
tomorrowUrlDateParam = tomorrowTime.strftime(datePatternUrl)

ADParams = {
    "leg": "Arrivals",
    "query": "",
    "board": "Domestic",
    "date": tomorrowUrlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}
AIParams = {
    "leg": "Arrivals",
    "query": "",
    "board": "International",
    "date": tomorrowUrlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}

resp = g.go(urlAKL, post=ADParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    arrival = getDataFromDocumentAKL(el)
    arrivals.append(arrival)
resp = g.go(urlAKL, post=AIParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    arrival = getDataFromDocumentAKL(el)
    arrivals.append(arrival)




# DEPARTURES

# four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayUrlDateParam = timeFourHourAgo.strftime(datePatternUrl)

    DDParams = {
        "leg": "Departures",
        "query": "",
        "board": "Domestic",
        "date": yesterdayUrlDateParam,
        "X-Requested-With": "XMLHttpRequest"
    }
    DIParams = {
        "leg": "Departures",
        "query": "",
        "board": "International",
        "date": yesterdayUrlDateParam,
        "X-Requested-With": "XMLHttpRequest"
    }

    resp = g.go(urlAKL, post=DDParams)
    for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
        departure = getDataFromDocumentAKL(el)
        departures.append(departure)
    resp = g.go(urlAKL, post=DIParams)
    for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
        departure = getDataFromDocumentAKL(el)
        departures.append(departure)

# now
urlDateParam = nowTime.strftime(datePatternUrl)
DDParams = {
    "leg": "Departures",
    "query": "",
    "board": "Domestic",
    "date": urlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}
DIParams = {
    "leg": "Departures",
    "query": "",
    "board": "International",
    "date": urlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}

resp = g.go(urlAKL, post=DDParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    departure = getDataFromDocumentAKL(el)
    departures.append(departure)
resp = g.go(urlAKL, post=DIParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    departure = getDataFromDocumentAKL(el)
    departures.append(departure)

# tomorrow
tomorrowTime = nowTime + timedelta(days=1)
tomorrowUrlDateParam = tomorrowTime.strftime(datePatternUrl)

DDParams = {
    "leg": "Departures",
    "query": "",
    "board": "Domestic",
    "date": tomorrowUrlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}
DIParams = {
    "leg": "Departures",
    "query": "",
    "board": "International",
    "date": tomorrowUrlDateParam,
    "X-Requested-With": "XMLHttpRequest"
}



resp = g.go(urlAKL, post=DDParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    departure = getDataFromDocumentAKL(el)
    departures.append(departure)
resp = g.go(urlAKL, post=DIParams)
for el in g.doc.select("//table/tbody/tr[contains(@class, 'flight-detail')]"):
    departure = getDataFromDocumentAKL(el)
    departures.append(departure)

resultAKL = {}
resultAKL["airport_id"] = "AKL"
resultAKL["departures"] = departures
resultAKL["arrivals"] = arrivals

jsonResult = json.dumps(resultAKL)
#print jsonResult

