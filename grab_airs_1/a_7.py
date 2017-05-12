from grab import Grab
import json
from datetime import datetime, timedelta
import re

#17:20 - 19:20
g = Grab(connect_timeout=90, timeout=90)
g.setup(headers={"X-Requested-With":"XMLHttpRequest"})

CHECK_IN = "check-in"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CANCELED = "canceled"
AIRBORNE = "airborne"
ESTIMSTED = "estimated"

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
        ESTIMSTED:EXPECTED,
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



def getFormatedCheckinDesks(checkinStr):
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

def getSecondPardOfData(data):
    matched = re.search("[a-zA-Z]+([ a-zA-Z]+)?\: ([\d\:\, \.A-Z]+)", data)
    if matched:
        return matched.groups()[1]

def getDataFromDocumentOVB(el, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    terminal = ""
    gate = ""
    check_in_desks = ""
    luggage = ""

    try:
        rawFlightno = el.select('.//div[1]/span[1]').text()
        flightno = rawFlightno.encode("utf-8")
    except:
        flightno = ""

    try:
        rawScheduled = getSecondPardOfData(str(el.select('.//div[2]/ul[1]/li[2]').text()))
        rawScheduled = rawScheduled + "." + str(nowTime.year)
        rawDateTime = datetime.strptime(rawScheduled, '%H:%M, %d.%m.%Y')
        scheduled = rawDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        rawEstimated = getSecondPardOfData(str(el.select('.//div[2]/ul[1]/li[3]').text()))
        rawEstimated = rawEstimated + "." + str(nowTime.year)
        rawDateTime = datetime.strptime(rawEstimated, '%H:%M, %d.%m.%Y')
        estimated = rawDateTime.strftime(datePattern)
    except:
        estimated = ""

    try:
        terminal = getSecondPardOfData(str(el.select('.//div[2]/ul[1]/li[4]').text()))
    except:
        terminal = ""

    if not isDeparture:
        try:
            luggage = getSecondPardOfData(str(el.select('.//div[2]/ul[2]/li[3]').text()))
        except:
            luggage = ""

    if isDeparture:
        try:
            rawCheckInDesks = getSecondPardOfData(str(el.select('.//div[2]/ul[2]/li[3]').text()))
            check_in_desks = getFormatedCheckinDesks(rawCheckInDesks)
        except:
            check_in_desks = ""

    try:
        gate = getSecondPardOfData(str(el.select('.//div[2]/ul[3]/li[3]').text()))
    except:
        gate = ""

    try:
        rawStatus = el.select('.//div[1]/span[6]').text()
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
    if luggage != "":
        result["luggage"] = luggage
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    if estimated != "":
        result["estimated"] = estimated
    if gate != "":
        result["gate"] = gate
    if terminal != "":
        result["terminal"] = terminal
    return result

#if rel is departure then div with arrive article will has unvisible attr
urlOVB = "http://eng.tolmachevo.ru/ajax/ttable.php"
# ARRIVE

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayParams = {
        "day": "yesterday",
        "items_count": 0,
        "rel": "departure"
    }
    resp = g.go(urlOVB, post=yesterdayParams)

    for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
        arrival = getDataFromDocumentOVB(el)
        arrivals.append(arrival)

#today
todayParams = {
    "day": "today",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlOVB, post=todayParams)

for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
    arrival = getDataFromDocumentOVB(el)
    arrivals.append(arrival)

# tommorow
tommorowParams = {
    "day": "tomorrow",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlOVB, post=tommorowParams)

for el in g.doc.select("//section/div/div/div[contains(@class, 'unvisible')]/div/div/article"):
    arrival = getDataFromDocumentOVB(el)
    arrivals.append(arrival)


# DEPARTURE

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayParams = {
        "day": "yesterday",
        "items_count": 0,
        "rel": "departure"
    }
    resp = g.go(urlOVB, post=yesterdayParams)

    for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
        departure = getDataFromDocumentOVB(el, True)
        departures.append(departure)

#today
todayParams = {
    "day": "today",
    "items_count": 0,
    "rel": "departure"
}
resp = g.go(urlOVB, post=todayParams)

for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
    departure = getDataFromDocumentOVB(el, True)
    departures.append(departure)

# tommorow
tommorowParams = {
    "day": "tomorrow",
    "items_count": 0,
    "rel": "departure"
}

resp = g.go(urlOVB, post=tommorowParams)

for el in g.doc.select("//section/div/div/div[not(contains(@class, 'unvisible'))]/div/div/article"):
    departure = getDataFromDocumentOVB(el, True)
    departures.append(departure)

resultOVB = {}
resultOVB["airport_id"] = "OVB"
resultOVB["departures"] = departures
resultOVB["arrivals"] = arrivals

jsonResult = json.dumps(resultOVB)
#print jsonResult