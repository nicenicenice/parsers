from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=50, timeout=50)

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
GATE_CLOSED = "gate closed"

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

        GATE_CLOSED:OUTGATE,
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


def getDataFromDocumentAES(flight, isDeparture):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    gateNumber = -1
    codeShares = []

    try:
        dateFromJson = str(flight['Date'] + " " + flight['ScheduledTime'])
        dateTimeFromJson = datetime.strptime(dateFromJson, '%Y%m%d %H:%M')
        datePattern = "%Y-%m-%d %H:%M:%S"
        scheduled = dateTimeFromJson.strftime(datePattern)
    except:
        scheduled = ""

    try:
        flightno = flight['FlightId']
    except:
        flightno = ""

    if isDeparture:
        try:
            gateNumber = flight['Gate']
        except:
            gateNumber = -1

    try:
        rawStatusString = str(flight['Status'])

        m = re.search("([a-zA-Z]+\s[a-zA-Z]*)\s?(\d{2}[:]\d{2})?", rawStatusString)

        if m:
            rawStatus = str.lower(m.groups()[0]).strip()
            statusTime = ""

            if m.groups()[1] is not None:
                dateFromJson = flight['Date'] + " " + m.groups()[1]
                dateTimeFromJson = datetime.strptime(dateFromJson, '%Y%m%d %H:%M')
                datePattern = "%Y-%m-%d %H:%M:%S"
                statusTime = dateTimeFromJson.strftime(datePattern)

            if rawStatus == NEW_TIME:
                status = EXPECTED
                estimated = statusTime

            if rawStatus == ARRIVED:
                status = LANDED
                actual = statusTime

            if rawStatus == DEPARTED:
                status = DEPARTED
                actual = statusTime

            if len(status) <= 0:
                status = fixStatus(rawStatus)
    except:
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""

    if len(status) <= 0:
        status = SCHEDULED

    try:
        if len(flight['CodeShares']) > 0:
            codeShares = flight['CodeShares']
    except:
        codeShares = []

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
    if gateNumber >= 0:
        result["gate"] = gateNumber
    return result


datePatternUrl = "%Y-%m-%dT%H:%M"
tommotowTimeUrl = datetime.now() + timedelta(days=1)
fourHoursAgoTimesUrl = datetime.now() - timedelta(hours=5)

formatedTommotowTimeUrl = tommotowTimeUrl.strftime(datePatternUrl)
formatedFourHoursAgoTimesUrl = fourHoursAgoTimesUrl.strftime(datePatternUrl)

## Arrivals
urlAESArrivals = "https://avinor.no/Api/Flights/Airport/AES?direction=a&start="\
                 + formatedFourHoursAgoTimesUrl + "&end=" + formatedTommotowTimeUrl + "&language=en"
resp = g.go(urlAESArrivals)

jsonResponse = json.loads(resp.body)

for flight in jsonResponse['Flights']:
    arrival = getDataFromDocumentAES(flight, False)
    arrivals.append(arrival)


## Departures
urlAESDepartures = "https://avinor.no/Api/Flights/Airport/AES?direction=d&start=" \
                   + formatedFourHoursAgoTimesUrl + "&end=" + formatedTommotowTimeUrl + "&language=en"

resp = g.go(urlAESDepartures)
jsonResponse = json.loads(resp.body)
for flight in jsonResponse['Flights']:
    departure = getDataFromDocumentAES(flight, True)
    departures.append(departure)


result = {}
result["airport_id"] = "AES"
result["departures"] = departures
result["arrivals"] = arrivals
jsonResult = json.dumps(result)
print jsonResult