from grab import Grab
import json
from datetime import datetime, timedelta
import re
import time

g = Grab(connect_timeout=50, timeout=50)

departures = []
arrivals = []

GATE_CLOSED = "gate closed"
FINALL_CALL = "final call"
GO_TO = "go to"
GATE_OPEN = "gate open"

ARRIVES = "arrives"
DELAYED_UNTIL = "delayed until"

ARRIVED = "arrived"
ESTIMATED = "estimated"
GO_TO_GATE = "go to gate"
AIRBORNE = "airborne"
GATE = "gate"
TAXIED = "taxied"
EARLIER = "earlier"
ON_TIME = "on time"
LAST_CALL = "last call"
NEW_TIME = "new time"
APPROACH = "approach"
NEW_DEPT = "new dept"

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
        NEW_DEPT:BOARDING,

        GATE_CLOSED:OUTGATE,
        FINALL_CALL:BOARDING,
        GO_TO: BOARDING,
        GATE_OPEN:BOARDING,

        APPROACH:EXPECTED,
        ESTIMATED: EXPECTED,
        AIRBORNE: DEPARTED,
        GATE: OUTGATE,
        TAXIED: OUTGATE,
        EARLIER: SCHEDULED,
        ARRIVED: LANDED,
        ON_TIME: SCHEDULED,
        LAST_CALL: BOARDING,
        ARRIVES: EXPECTED,
        DELAYED_UNTIL: DELAYED
    }.get(status, "")

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

datePatternUrl = "%Y%m%d"
nowTimeUrl = datetime.now()
tommorowTimeUrl = nowTimeUrl + timedelta(days=1)

formatedNowTimeUrl = nowTimeUrl.strftime(datePatternUrl)
formatedTommorowTimeUrl = tommorowTimeUrl.strftime(datePatternUrl)



urlARNArrivals = "https://www.swedavia.com/services/publicflightsboard/arrivals/en/ARN/" + formatedNowTimeUrl
urlARNArrivalsTommorow = "https://www.swedavia.com/services/publicflightsboard/arrivals/en/ARN/" + formatedTommorowTimeUrl

resp = g.go(urlARNArrivals)
jsonResponseARN = json.loads(resp.body)

resp = g.go(urlARNArrivalsTommorow)
jsonResponseARNTommorow = json.loads(resp.body)

jsonResponseARN['Flights'] = jsonResponseARN['Flights'] + jsonResponseARNTommorow['Flights']

for flight in jsonResponseARN['Flights']:

    try:
        flight['ArrivalDateTime']
    except:
        continue

    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""

    codeShares = []

    try:
        scheduled = flight['ArrivalDateTime']
        scheduled = scheduled.replace("T", " ")
    except:
        scheduled = ""

    try:
        datePattern = "%Y-%m-%d %H:%M:%S"

        actual = getFullDate(flight['ActualTime'], True)
        actualDateTime = datetime.strptime(actual, datePattern)
        scheduledDateTime = datetime.strptime(scheduled, datePattern)

        actualDateTime = actualDateTime.replace(day=scheduledDateTime.day)
        yesterdayDateTime = actualDateTime - timedelta(days=1)

        scheduledTimeStampe = time.mktime(scheduledDateTime.timetuple())
        actualTimeStampe = time.mktime(actualDateTime.timetuple())
        actualYesterdayTimeStampe = time.mktime(yesterdayDateTime.timetuple())

        diffScheduleWithActual = abs(scheduledTimeStampe - actualTimeStampe)
        diffScheduleWithYesterdayActual = abs(scheduledTimeStampe - actualYesterdayTimeStampe)

        if diffScheduleWithActual < diffScheduleWithYesterdayActual:
            actual = actualDateTime.strftime(datePattern)
        else:
            actual = yesterdayDateTime.strftime(datePattern)
    except:
        actual = ""

    try:
        estimated = flight['ProbableTime']
        estimated = estimated.replace("T", " ")
    except:
        estimated = ""

    try:
        flightno = flight['FlightNumber']
    except:
        flightno = ""

    try:
        rawStatusString = str(flight['Remark']['RemarkText'])
        m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
        if m:
            rawStatus = str.lower(m.groups()[0])
            status = fixStatus(rawStatus)
    except:
        try:
            rawStatusString = str(flight["GateStatus"]["GateStatusText"])
            m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
            if m:
                rawStatus = str.lower(m.groups()[0])
                status = fixStatus(rawStatus)
        except:
            rawStatus = ""
            status = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        if len(flight['CodeShares']) > 0:
            for codeShare in flight['CodeShares']:
                codeShares.append(codeShare["FlightNumber"])
    except:
        codeShares = []

    arrival = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        arrival["estimated"] = estimated
    if actual != "":
        arrival["actual"] = actual

    arrivals.append(arrival)


urlARNDepartures = "https://www.swedavia.com/services/publicflightsboard/departures/en/ARN/" + formatedNowTimeUrl
urlARNDeparturesTommorow = "https://www.swedavia.com/services/publicflightsboard/departures/en/ARN/" + formatedTommorowTimeUrl

resp = g.go(urlARNDepartures)
jsonResponseARN = json.loads(resp.body)

resp = g.go(urlARNDeparturesTommorow)
jsonResponseARNTommorow = json.loads(resp.body)

jsonResponseARN['Flights'] = jsonResponseARN['Flights'] + jsonResponseARNTommorow['Flights']

for flight in jsonResponseARN['Flights']:

    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    numGate = -1
    checkInDesk = ""

    try:
        scheduled = flight['DepartureDateTime']
        scheduled = scheduled.replace("T", " ")
    except:
        scheduled = ""

    try:
        datePattern = "%Y-%m-%d %H:%M:%S"

        actual = getFullDate(flight['ActualTime'], True)
        actualDateTime = datetime.strptime(actual, datePattern)
        scheduledDateTime = datetime.strptime(scheduled, datePattern)

        actualDateTime = actualDateTime.replace(day=scheduledDateTime.day)
        yesterdayDateTime = actualDateTime - timedelta(days=1)

        scheduledTimeStampe = time.mktime(scheduledDateTime.timetuple())
        actualTimeStampe = time.mktime(actualDateTime.timetuple())
        actualYesterdayTimeStampe = time.mktime(yesterdayDateTime.timetuple())

        diffScheduleWithActual = abs(scheduledTimeStampe - actualTimeStampe)
        diffScheduleWithYesterdayActual = abs(scheduledTimeStampe - actualYesterdayTimeStampe)

        if diffScheduleWithActual < diffScheduleWithYesterdayActual:
            actual = actualDateTime.strftime(datePattern)
        else:
            actual = yesterdayDateTime.strftime(datePattern)
    except:
        actual = ""

    try:
        estimated = flight['ProbableTime'] #2017-04-16 23:46:00
        estimated = estimated.replace("T", " ")
    except:
        estimated = ""

    try:
        numGate = flight['Gate']
    except:
        numGate = -1

    try:
        flightno = flight['FlightNumber']

    except:
        flightno = ""

    try:
        rawStatusString = str(flight['Remark']['RemarkText'])
        m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
        if m:
            rawStatus = str.lower(m.groups()[0])
            status = fixStatus(rawStatus)
    except:
        try:
            rawStatusString = str(flight["GateStatus"]["GateStatusText"])
            m = re.search("([a-zA-Z]+( [a-zA-Z]+)?)?\s?(\d{2}[\:]\d{2})?", rawStatusString)
            if m:
                rawStatus = str.lower(m.groups()[0])
                status = fixStatus(rawStatus)
        except:
            rawStatus = ""
            status = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        checkInDesk = flight['Amendments']["CheckInDesk"]
    except:
        checkInDesk = ""

    try:
        if len(flight['CodeShares']) > 0:
            for codeShare in flight['CodeShares']:
                codeShares.append(codeShare["FlightNumber"])
    except:
        codeShares = []

    departure = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if str(numGate) != str(-1):
        departure["gate"] = numGate
    if estimated != "":
        departure["estimated"] = estimated
    if actual != "":
        departure["actual"] = actual
    if checkInDesk != "":
        departure["check_in_desks"] = checkInDesk

    departures.append(departure)

resultARN = {}
resultARN["airport_id"] = "ARN"
resultARN["departures"] = departures
resultARN["arrivals"] = arrivals
jsonResultARN = json.dumps(resultARN)
print jsonResultARN

