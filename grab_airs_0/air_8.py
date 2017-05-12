from grab import Grab
import time
import json
from datetime import datetime, timedelta

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

        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED
    }.get(status, "")

departures = []
arrivals = []

g = Grab(connect_timeout=50, timeout=50)

currentTimestamp = int(round(time.time() * 1000))
urlATH = "https://www.aia.gr/handlers/rtfi.ashx?action=getRtfiJson&cultureId=50&bringRecent=1&timeStampFormat=Fyyyy-FMM-dd+HH-mm&allRecs=1&airportId=&airlineId=&flightNo=&_=" + str(currentTimestamp)
resp = g.go(urlATH)
jsonResponseAIA = json.loads(resp.body)

def getDataFromDocumentATH(chunk):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    gate = ""

    try:
        flightno = chunk['FlightNo']
    except:
        flightno = ""
    try:
        rawScheduled = chunk['ScheduledTime']
        scheduled = datetime.strptime(rawScheduled, '%d/%m/%Y %H:%M')
        scheduled = scheduled.strftime(datePattern)
    except:
        scheduled = ""
    try:
        rawEstimated = chunk['EstimatedTime']
        estimated = datetime.strptime(rawEstimated, '%d/%m/%Y %H:%M')
        estimated = estimated.strftime(datePattern)
    except:
        estimated = ""
    try:
        rawStatus = str(chunk['FlightStateName'])
        lowerRawStatus = str.lower(rawStatus)
        status = fixStatus(lowerRawStatus)
    except:
        status = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        gate = str(chunk['Gate'])
    except:
        gate = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if estimated != "":
        result["estimated"] = estimated
    if len(gate) > 0:
        result["gate"] = gate
    return result


for flight in jsonResponseAIA['arrivals']:
    try:
        if len(flight['data']) <= 0:
            continue
    except:
        continue

    for chunk in flight['data']:
        arrival = getDataFromDocumentATH(chunk)
        arrivals.append(arrival)

for flight in jsonResponseAIA['departures']:

    if len(flight['data']) <= 0:
        continue

    for chunk in flight['data']:
        departure = getDataFromDocumentATH(chunk)
        departures.append(departure)

resultATH = {}
resultATH["airport_id"] = "ATH"
resultATH["departures"] = departures
resultATH["arrivals"] = arrivals
jsonResultATH = json.dumps(resultATH)
print jsonResultATH