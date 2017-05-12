from grab import Grab
import json

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

def getDataFromDocumentAMM(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""

    try:
        flightno = el.select('.//td[1]').text()
    except:
        flightno = ""
    try:
        scheduled = el.select('.//td[3]').text() + ":00"
    except:
        scheduled = "'"
    try:
        estimated = el.select('.//td[4]').text() + ":00"
    except:
        estimated = ""
    try:
        rawStatus = str.lower(el.select('.//td[5]').text())
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""

    if status == "":
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "estimated": estimated,
        "status": status,
        "raw_status": rawStatus
    }
    return result


g = Grab(connect_timeout=50, timeout=50)

urlAMMArrivals = "http://www.qaiairport.com/en/flights_schedule/arrivals?type=arrivals&from_city=&date=&flight_number=&airline="
resp = g.go(urlAMMArrivals)

for el in g.doc.select('//*[@id="block-system-main"]//tbody/tr'):
    arrival = getDataFromDocumentAMM(el)
    arrivals.append(arrival)


urlAMMDepature = "http://www.qaiairport.com/en/flights_schedule/departures?type=departures&from_city=&date=&flight_number=&airline="
resp = g.go(urlAMMDepature)

for el in g.doc.select('//*[@id="block-system-main"]//tbody/tr'):
    departure = getDataFromDocumentAMM(el)
    departures.append(departure)

result = {}
result["airport_id"] = "AMM"
result["departures"] = departures
result["arrivals"] = arrivals
jsonResult = json.dumps(result)
print jsonResult