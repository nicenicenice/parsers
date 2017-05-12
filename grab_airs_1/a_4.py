from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=90, timeout=90)

BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CHECKIN_OPEN = "check-in open"
FLIES = "flies"

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

        FLIES:EXPECTED,
        CHECKIN_OPEN:CHECKIN,
        BOARDING_CLOSED:OUTGATE,
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")


datePattern = "%Y-%m-%d %H:%M:%S"

def getDataFromDocumentODS(el, day):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        flightno = str(el.select('.//td[1]').text())
    except:
        flightno = ""
    try:
        rawScheduledString = str(el.select('.//td[3]').text())

        matched = re.search("(\d{2}\:\d{2})\(?(\d{1,2}\.\d{2}\.\d{4})?\)?", rawScheduledString)
        if matched:

            newScheduleDate = ""
            rawScheduled = str.lower(matched.groups()[0])
            dateTimeToCorrect = nowTime

            h = int(rawScheduled[:2])
            m = int(rawScheduled[3:])

            scheduleDateTime = dateTimeToCorrect.replace(day=day, hour=h, minute=m, second=0)


            if matched.groups()[1] is not None:
                dateOfSchedule = matched.groups()[1]
                newScheduleDate = datetime.strptime(dateOfSchedule, '%d.%m.%Y')

            if newScheduleDate != "":
                scheduleDateTime = scheduleDateTime.replace(day=newScheduleDate.day)

            scheduled = scheduleDateTime.strftime(datePattern)
    except:
        scheduled = ""
    try:
        rawActual = str(el.select('.//td[4]').text())
        if rawActual != "":

            dateTimeToCorrect = nowTime
            h = int(rawActual[:2])
            m = int(rawActual[3:])

            if newScheduleDate != "":
                day = newScheduleDate.day
            actualDateTime = dateTimeToCorrect.replace(day=day, hour=h, minute=m, second=0)
            actual = actualDateTime.strftime(datePattern)
    except:
        actual = ""

    try:
        rawStatus = el.select('.//td[5]').text()
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
    if actual != "":
        result["actual"] = actual
    return result


departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()

urlODS = "http://www.odessa.aero/en/iboard"
resp = g.go(urlODS)

# arrive

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:
    urlODSYesterday = "http://www.odessa.aero/en/iboard?day=yesterday"
    resp = g.go(urlODSYesterday)

    for el in g.doc.select('//*[@id="iboard"]/div[2]/div[1]/table/tbody/tr'):
        arrival = getDataFromDocumentODS(el, timeFourHourAgo.day)
        arrivals.append(arrival)

#now
for el in g.doc.select('//*[@id="iboard"]/div[2]/div[1]/table/tbody/tr'):
    arrival = getDataFromDocumentODS(el, nowTime.day)
    arrivals.append(arrival)

# departure

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:
    urlODSYesterday = "http://www.odessa.aero/en/iboard?day=yesterday"
    resp = g.go(urlODSYesterday)

    for el in g.doc.select('//*[@id="iboard"]/div[2]/div[2]/table/tbody/tr'):
        departure = getDataFromDocumentODS(el, timeFourHourAgo.day)
        departures.append(departure)


for el in g.doc.select('//*[@id="iboard"]/div[2]/div[2]/table/tbody/tr'):
    departure = getDataFromDocumentODS(el, nowTime.day)
    departures.append(departure)

resultODS = {}
resultODS["airport_id"] = "ODS"
resultODS["departures"] = departures
resultODS["arrivals"] = arrivals

jsonResult = json.dumps(resultODS)
#print jsonResultODS
