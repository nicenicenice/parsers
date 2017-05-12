from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=90, timeout=90)

CHECK_IN = "check-in"

ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
GATE_OPEN = "gate open"
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
DEPARTURE = "departure"

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

        DEPARTURE:DELAYED,
        CHECK_IN:CHECKIN,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()

    correctDate = scheduleDateTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

    if scheduleDateTime.hour > 20 and h < 5:
        notFormatedTime = notFormatedTime + timedelta(days=1)
    elif scheduleDateTime.hour < 5 and h > 20:
        notFormatedTime = notFormatedTime - timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime


def getDataFromDocumentMSQ(el, dateTime, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        flightnoString = str(el.select('.//td[4]').text())
        arFlightno = flightnoString.split(" / ")
        flightno = arFlightno[0]
        if len(arFlightno) > 1:
            for i in range(1, len(arFlightno)):
                codeShares.append(arFlightno[i])
    except:
        flightno = ""
    try:
        rawScheduled = el.select('.//td[2]').text()

        h = int(rawScheduled[:2])
        m = int(rawScheduled[3:])

        dateTimeToCorrect = dateTime

        scheduleDateTime = dateTimeToCorrect.replace(hour=h, minute=m, second=0)
        scheduled = scheduleDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        actual = str(el.select('.//td[3]').text())
        actual = getFullDate(actual, scheduleDateTime)
    except:
        actual = ""

    try:
        gate = str(el.select('.//td[6]').text())
    except:
        gate = ""

    try:
        rawStatus = str.lower(el.select('.//td[7]/span[1]').text())
        m = re.search("(\d{1,2})\s([a-zA-Z]+)", rawStatus)
        if m:
            day = int(m.groups()[0])
            month = m.groups()[1]
            timeSting = str(day) + " " + str(month) + " " + str(scheduleDateTime.year)
            tempDateTime = datetime.strptime(timeSting, "%d %b %Y")

            status = SCHEDULED

            newScheduleDateTime = scheduleDateTime.replace(day=tempDateTime.day, month=tempDateTime.month)
            scheduled = getFullDate(rawScheduled, newScheduleDateTime)
            estimated = scheduled
        else:
            croppedRawStatus = ""
            idxOfWhiteSpace = rawStatus.find(" ")
            if idxOfWhiteSpace > 0:
                croppedRawStatus = rawStatus[:idxOfWhiteSpace]
            if croppedRawStatus != "":
                status = fixStatus(croppedRawStatus)
            else:
                status = fixStatus(rawStatus)
        if status == "" and len(rawStatus) > 0:
            status = UNKNOWN
    except:
        rawStatus = ""
        status = UNKNOWN

    if status == "":
        status = SCHEDULED

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

    if gate != "" and isDeparture:
        result["gate"] = gate

    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    return result

urlMSQArrial = "http://airport.by/en/timetable/online-arrival"
resp = g.go(urlMSQArrial)

for el in g.doc.select('//table/tbody/tr'):
    arrival = getDataFromDocumentMSQ(el, nowTime)

    try:
        nowRawStatus = datetime.strptime(arrival["raw_status"], "%d %b")
        nowScheduledString = arrival["scheduled"]
        nowScheduledDateTime = datetime.strptime(nowScheduledString, datePattern)
        IdxOfPreviousEl = len(arrivals) - 1
        if IdxOfPreviousEl >= 0:
            try:
                previousRawStatus = datetime.strptime(arrivals[IdxOfPreviousEl]["raw_status"], "%d %b")
            except:
                previousScheduledString = arrivals[IdxOfPreviousEl]["scheduled"]
                previousScheduledDateTime = datetime.strptime(previousScheduledString, datePattern)
                if previousScheduledDateTime.hour <= nowScheduledDateTime.hour and previousScheduledDateTime.day < nowScheduledDateTime.day:
                    previousScheduledDateTime = previousScheduledDateTime + timedelta(days=1)
                    arrivals[IdxOfPreviousEl]["scheduled"] = previousScheduledDateTime.strftime(datePattern)
    except:
        nowScheduledString = arrival["scheduled"]
        IdxOfPreviousEl = len(arrivals) - 1
        if IdxOfPreviousEl >= 0:
            nowScheduledDateTime = datetime.strptime(nowScheduledString, datePattern)
            previousScheduledString = arrivals[IdxOfPreviousEl]["scheduled"]
            previousScheduledDateTime = datetime.strptime(previousScheduledString, datePattern)
            if nowScheduledDateTime.hour < 10 and previousScheduledDateTime.hour > 20:
                previousScheduledDateTime = previousScheduledDateTime - timedelta(days=1)
                arrivals[IdxOfPreviousEl]["scheduled"] = previousScheduledDateTime.strftime(datePattern)

    arrivals.append(arrival)

urlMSQDeparture = "http://airport.by/en/timetable/online-departure"
resp = g.go(urlMSQDeparture)

for el in g.doc.select('//table/tbody/tr'):
    departure = getDataFromDocumentMSQ(el, nowTime, True)
    try:
        nowRawStatus = datetime.strptime(departure["raw_status"], "%d %b")
        nowScheduledString = departure["scheduled"]
        nowScheduledDateTime = datetime.strptime(nowScheduledString, datePattern)
        IdxOfPreviousEl = len(departures) - 1
        if IdxOfPreviousEl >= 0:
            try:
                previousRawStatus = datetime.strptime(departures[len(departures) - 1]["raw_status"], "%d %b")
            except:
                previousScheduledString = departures[IdxOfPreviousEl]["scheduled"]
                previousScheduledDateTime = datetime.strptime(previousScheduledString, datePattern)
                if previousScheduledDateTime.hour <= nowScheduledDateTime.hour and previousScheduledDateTime.day < nowScheduledDateTime.day:
                    previousScheduledDateTime = previousScheduledDateTime + timedelta(days=1)
                    departures[IdxOfPreviousEl]["scheduled"] = previousScheduledDateTime.strftime(datePattern)
    except:
        nowScheduledString = departure["scheduled"]
        IdxOfPreviousEl = len(departures) - 1
        if IdxOfPreviousEl >= 0:
            nowScheduledDateTime = datetime.strptime(nowScheduledString, datePattern)
            previousScheduledString = departures[IdxOfPreviousEl]["scheduled"]
            previousScheduledDateTime = datetime.strptime(previousScheduledString, datePattern)
            if nowScheduledDateTime.hour < 10 and previousScheduledDateTime.hour > 20:
                previousScheduledDateTime = previousScheduledDateTime - timedelta(days=1)
                departures[IdxOfPreviousEl]["scheduled"] = previousScheduledDateTime.strftime(datePattern)
    departures.append(departure)

resultMSQ = {}
resultMSQ["airport_id"] = "MSQ"
resultMSQ["departures"] = departures
resultMSQ["arrivals"] = arrivals

jsonResult = json.dumps(resultMSQ)
#print jsonResult


