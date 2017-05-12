#MEL Melbourne Airport Melbourne http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=DA


from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=70, timeout=70)
g.setup(headers={"X-Requested-With":"XMLHttpRequest"})

UNKNOWN = "unknown"
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
        LATE: DELAYED,
        "":SCHEDULED
    }.get(status, UNKNOWN)


def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
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

def getDataFromDocumentMEL(el, isDeparted=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    terminal = ""
    gate = ""
    dayMonthDateTime = ""

    try:
        dayMonthOfFlight = el.select('.//td[1]').text()
        dayMonthDateTime = datetime.strptime(dayMonthOfFlight, "%d/%m")
    except:
        dayMonthDateTime = ""

    try:
        flightno = el.select('.//td[2]').text()
    except:
        flightno = ""

    try:
        rawStatus = el.select('.//td[8]/img/@alt').text()
        rawStatus = str.lower(rawStatus)
        if rawStatus != "":
            status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    try:
        rawScheduled = str(el.select('.//td[4]').text())
        h = int(rawScheduled[:2])
        m = int(rawScheduled[3:])
        scheduledDateTime = nowTime.replace(day=dayMonthDateTime.day, month=dayMonthDateTime.month, hour=h, minute=m, second=0)

        scheduled = scheduledDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        rawAddTime = str(el.select('.//td[5]').text())
        addTime = getFullDate(rawAddTime, scheduledDateTime)
        if status == LANDED or status == DEPARTED:
            actual = addTime
        elif status != CANCELLED:
            estimated = addTime
    except:
        estimated = ""
        actual = ""

    try:
        terminal = el.select('.//td[6]').text()
    except:
        terminal = ""

    if isDeparted:
        try:
            gate = el.select('.//td[7]').text()
        except:
            gate = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if terminal != "":
        result["terminal"] = terminal
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    if gate != "":
        result["gate"] = gate
    return result


rootUrl = "http://melbourneairport.com.au"

# Today
todayUrlIA = "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=IA&airline="

# ARRIVE INTERNATIONAL

theEnd = False
while not theEnd:
    resp = g.go(todayUrlIA)
    i = 0
    for el in g.doc.select('//*[@id="resultTable"]/tbody/tr'):
        i += 1
        if i == 1:
            continue
        arrival = getDataFromDocumentMEL(el)
        if arrival['flightno'].find("(") >= 0:
            codeshareToFlight = arrival['flightno'][arrival['flightno'].find("(") + 1 : arrival['flightno'].find(")")].strip()
            codeshare = arrival['flightno'][: arrival['flightno'].find("(")].strip()
            lastIdxOfArrivals = len(arrivals) - 1
            if lastIdxOfArrivals >= 0 and arrivals[lastIdxOfArrivals]["flightno"] == codeshareToFlight:
                if not arrivals[lastIdxOfArrivals].has_key("codeshares"):
                    arrivals[lastIdxOfArrivals]["codeshares"] = []
                arrivals[lastIdxOfArrivals]["codeshares"].append(codeshare)
                continue
        arrivals.append(arrival)
    try:
        todayUrlIA = ""
        for el in g.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
            try:
                altText = el.select('./a/img/@alt').text()
                if altText == "Next Page":
                    todayUrlIA = rootUrl + el.select('./a/@href').text()
            except:
                pass
        if todayUrlIA == "":
            theEnd = True
            break
    except:
        theEnd = True
        break

todayUrlDA = "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=DA"
# ARRIVE DOMESTIC
resp = g.go(todayUrlDA)

theEnd = False
while not theEnd:
    resp = g.go(todayUrlDA)
    i = 0
    for el in g.doc.select('//*[@id="resultTable"]/tbody/tr'):
        i += 1
        if i == 1:
            continue
        arrival = getDataFromDocumentMEL(el)
        if arrival['flightno'].find("(") >= 0:
            codeshareToFlight = arrival['flightno'][arrival['flightno'].find("(") + 1 : arrival['flightno'].find(")")].strip()
            codeshare = arrival['flightno'][: arrival['flightno'].find("(")].strip()
            lastIdxOfArrivals = len(arrivals) - 1
            if lastIdxOfArrivals >= 0 and arrivals[lastIdxOfArrivals]["flightno"] == codeshareToFlight:
                if not arrivals[lastIdxOfArrivals].has_key("codeshares"):
                    arrivals[lastIdxOfArrivals]["codeshares"] = []
                arrivals[lastIdxOfArrivals]["codeshares"].append(codeshare)
                continue
        arrivals.append(arrival)
    try:
        todayUrlDA = ""
        for el in g.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
            try:
                altText = el.select('./a/img/@alt').text()
                if altText == "Next Page":
                    todayUrlDA = rootUrl + el.select('./a/@href').text()
            except:
                pass
        if todayUrlDA == "":
            theEnd = True
            break
    except:
        theEnd = True
        break

# DEPARTURE INTERNATIONAL

todayUrlID = "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=ID"
resp = g.go(todayUrlID)

theEnd = False
while not theEnd:
    resp = g.go(todayUrlID)
    i = 0
    for el in g.doc.select('//*[@id="resultTable"]/tbody/tr'):
        i += 1
        if i == 1:
            continue
        departure = getDataFromDocumentMEL(el, True)
        if departure['flightno'].find("(") >= 0:
            codeshareToFlight = departure['flightno'][departure['flightno'].find("(") + 1 : departure['flightno'].find(")")].strip()
            codeshare = departure['flightno'][: departure['flightno'].find("(")].strip()
            lastIdxOfDepartures = len(departures) - 1
            if lastIdxOfDepartures >= 0 and departures[lastIdxOfDepartures]["flightno"] == codeshareToFlight:
                if not departures[lastIdxOfDepartures].has_key("codeshares"):
                    departures[lastIdxOfDepartures]["codeshares"] = []
                departures[lastIdxOfDepartures]["codeshares"].append(codeshare)
                continue
        departures.append(departure)
    try:
        todayUrlID = ""
        for el in g.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
            try:
                altText = el.select('./a/img/@alt').text()
                if altText == "Next Page":
                    todayUrlID = rootUrl + el.select('./a/@href').text()
            except:
                pass
        if todayUrlID == "":
            theEnd = True
            break
    except:
        theEnd = True
        break

# DEPARTURE DOMESTIC
todayUrlDD = "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=DD&airline="
resp = g.go(todayUrlDD)

theEnd = False
while not theEnd:
    resp = g.go(todayUrlDD)
    i = 0
    for el in g.doc.select('//*[@id="resultTable"]/tbody/tr'):
        i += 1
        if i == 1:
            continue
        departure = getDataFromDocumentMEL(el, True)
        if departure['flightno'].find("(") >= 0:
            codeshareToFlight = departure['flightno'][departure['flightno'].find("(") + 1 : departure['flightno'].find(")")].strip()
            codeshare = departure['flightno'][: departure['flightno'].find("(")].strip()
            lastIdxOfDepartures = len(departures) - 1
            if lastIdxOfDepartures >= 0 and departures[lastIdxOfDepartures]["flightno"] == codeshareToFlight:
                if not departures[lastIdxOfDepartures].has_key("codeshares"):
                    departures[lastIdxOfDepartures]["codeshares"] = []
                departures[lastIdxOfDepartures]["codeshares"].append(codeshare)
                continue
        departures.append(departure)
    try:
        todayUrlDD = ""
        for el in g.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
            try:
                altText = el.select('./a/img/@alt').text()
                if altText == "Next Page":
                    todayUrlDD = rootUrl + el.select('./a/@href').text()
            except:
                pass
        if todayUrlDD == "":
            theEnd = True
            break
    except:
        theEnd = True
        break

resultMEL = {}
resultMEL["airport_id"] = "MEL"
resultMEL["departures"] = departures
resultMEL["arrivals"] = arrivals

jsonResult = json.dumps(resultMEL)
print jsonResult
