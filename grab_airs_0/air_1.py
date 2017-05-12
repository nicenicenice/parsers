from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=50, timeout=50)

urlABZ = "https://www.aberdeenairport.com/flight-information/"
resp = g.go(urlABZ)

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
ARRIVES = "arrives"
DELAYED_UNTIL = "delayed until"

SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"

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


datePattern = "%Y-%m-%d %H:%M:%S"

for el in g.doc.select('//*[@id="arrivals-departures__arrivals"]/ul/li'):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    summaryFullTime = ""
    rawStatus = ""
    numGate = -1


    try:
        status = el.select('.//div[contains(@class, "summary")]//div//span').text()
        rawStatus = str.lower(status)

        status = fixStatus(rawStatus)
        if status == "":
            status = rawStatus

        if status == GO_TO_GATE:
            status = BOARDING
            numGate = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()
        else:
            try:
                summaryShortTime = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()

                h = int(summaryShortTime[:2])
                m = int(summaryShortTime[3:])

                nowTime = datetime.now()
                isFlightWillTommorow = False

                if len(arrivals) > 0:
                    if nowTime.hour > 16 and arrivals[0]["status"] == SCHEDULED:
                        isFlightWillTommorow = True
                elif nowTime.hour > 16 and status == SCHEDULED:
                    isFlightWillTommorow = True

                flightTime = nowTime.replace(hour=h, minute=m, second=0)
                if isFlightWillTommorow:
                    flightTime += timedelta(days=1)

                summaryFullTime = flightTime.strftime(datePattern)
            except:
                summaryFullTime = ""

        if status == LANDED:
            actual = summaryFullTime
        elif status == EXPECTED:
            estimated = summaryFullTime
        elif status == DEPARTED:
            actual = summaryFullTime

    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        scheduledShortTime = el.select('.//div[contains(@class, "time")]/div/p/text()').text()
        h = int(scheduledShortTime[:2])
        m = int(scheduledShortTime[3:])

        nowTime = datetime.now()
        isFlightWillTommorow = False

        if len(arrivals) > 0:
            if nowTime.hour > 16 and arrivals[0]["status"] == SCHEDULED:
                isFlightWillTommorow = True
        elif nowTime.hour > 16 and status == SCHEDULED:
            isFlightWillTommorow = True

        flightTime = nowTime.replace(hour=h, minute=m, second=0)
        if isFlightWillTommorow:
            flightTime += timedelta(days=1)

        scheduled = flightTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        flightno = el.select('.//div[contains(@class, "carrier")]//span').text()
    except:
        flightno = ""

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
    if numGate >= 0:
        arrival["gate"] = numGate
    arrivals.append(arrival)

for el in g.doc.select('//*[@id="arrivals-departures__departures"]/ul/li'):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    summaryFullTime = ""
    rawStatus = ""
    numGate = -1

    try:
        status = el.select('.//div[contains(@class, "summary")]//div//span').text()
        rawStatus = str.lower(status)

        status = fixStatus(rawStatus)
        if status == "":
            status = rawStatus

        if status == GO_TO_GATE:
            status = BOARDING
            numGate = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()
        else:
            try:
                summaryShortTime = el.select('.//div[contains(@class, "summary")]//div/p/text()').text()

                h = int(summaryShortTime[:2])
                m = int(summaryShortTime[3:])

                nowTime = datetime.now()
                isFlightWillTommorow = False

                if len(departures) > 0:
                    if nowTime.hour > 16 and departures[0]["status"] == SCHEDULED:
                        isFlightWillTommorow = True
                elif nowTime.hour > 16 and status == SCHEDULED:
                    isFlightWillTommorow = True

                flightTime = nowTime.replace(hour=h, minute=m, second=0)
                if isFlightWillTommorow:
                    flightTime += timedelta(days=1)

                summaryFullTime = flightTime.strftime(datePattern)
            except:
                summaryFullTime = ""

        if status == LANDED:
            actual = summaryFullTime
        elif status == EXPECTED:
            estimated = summaryFullTime
        elif status == DEPARTED:
            actual = summaryFullTime

    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        scheduledShortTime = el.select('.//div[contains(@class, "time")]/div/p/text()').text()
        h = int(scheduledShortTime[:2])
        m = int(scheduledShortTime[3:])

        nowTime = datetime.now()
        isFlightWillTommorow = False

        if len(departures) > 0:
            if nowTime.hour > 16 and departures[0]["status"] == SCHEDULED:
                isFlightWillTommorow = True
        elif nowTime.hour > 16 and status == SCHEDULED:
            isFlightWillTommorow = True

        flightTime = nowTime.replace(hour=h, minute=m, second=0)
        if isFlightWillTommorow:
            flightTime += timedelta(days=1)

        scheduled = flightTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        flightno = el.select('.//div[contains(@class, "carrier")]//span').text()
    except:
        flightno = ""

    departure = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        departure["estimated"] = estimated
    if actual != "":
        departure["actual"] = actual
    if numGate >= 0:
        departure["gate"] = numGate
    departures.append(departure)

result = {}
result["airport_id"] = "ABZ"
result["departures"] = departures
result["arrivals"] = arrivals

jsonResult = json.dumps(result)
print jsonResult