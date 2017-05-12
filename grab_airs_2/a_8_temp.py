from grab import Grab
import json
from datetime import datetime, timedelta
import re
import time

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

datePattern = "%Y-%m-%d %H:%M:%S"
departures = []
arrivals = []

def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

def getDetailFlightInfoByPreview(previewFlights):
    result = []
    for preFlight in previewFlights:
        flight = getDataFromDocumentBNE(preFlight)
        if flight != -1:
            result.append(flight)
    return result

def getDataFromDocumentBNE(preview):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    luggage = ""
    codeshares = ""
    rawStatus = ""
    gate = ""

    try:
        resp = g.go(preview["urlOfFlight"])
    except:
        return -1

    try:
        rawStatus = g.doc.select('//div/div[1]/div[3]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status

    if status == "":
        status = SCHEDULED

    try:
        scheduled = g.doc.select('//div/div[2]/div[1]').text()
    except:
        scheduled

    try:
        gate = g.doc.select('//div/div[2]/div[4]/div/following-sibling::text()[1]').text()
        if gate.find(" ") >= 0:
            gate = ""
    except:
        gate = ""

    try:
        luggage = g.doc.select('//div/div[2]/div[5]/div/following-sibling::text()[1]').text()
        if luggage.find(" ") >= 0:
            luggage = ""
    except:
        luggage = ""

    try:
        actual = g.doc.select('//div/div[1]/div[4]').text()
    except:
        actual = ""

    result = {
        "flightno": preview["flightno"],
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if preview.has_key("codeshares") and len(preview["codeshares"]) > 0:
        result["codeshares"] = codeshares
    if luggage != "":
        result["luggage"] = luggage
    if actual != "":
        result["actual"] = actual
    if gate != "":
        result["gate"] = gate
    return result

nowTime = datetime.now()
fourHoursAgoDateTime = nowTime - timedelta(days=1)
tomorrowDateTime = nowTime + timedelta(days=1)
timeStampFrom = str(getTimeStampFromDateTime(fourHoursAgoDateTime))
timeStampTo = str(getTimeStampFromDateTime(tomorrowDateTime))
currentTimeStamp = str(getTimeStampFromDateTime(nowTime))

urlArrDomestic = "http://www.bne.com.au/sites/all/custom/flight/?range=D&leg=A&date_from=" + \
      timeStampFrom + "&date_to=" \
      + timeStampTo + "&_=" + currentTimeStamp
urlDepDomestic = "http://www.bne.com.au/sites/all/custom/flight/?range=D&leg=D&date_from=" + \
      timeStampFrom + "&date_to=" \
      + timeStampTo + "&_=" + currentTimeStamp
urlArrInter = "http://www.bne.com.au/sites/all/custom/flight/?range=I&leg=A&date_from=" + \
      timeStampFrom + "&date_to=" \
      + timeStampTo + "&_=" + currentTimeStamp
urlDepInter = "http://www.bne.com.au/sites/all/custom/flight/?range=I&leg=D&date_from=" + \
      timeStampFrom + "&date_to=" \
      + timeStampTo + "&_=" + currentTimeStamp


g = Grab(connect_timeout=90, timeout=90)

# ARRIVAL DOMESTIC
resp = g.go(urlArrDomestic)

pre_arrivals1 = []

for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
    flightno = el.select('.//@data-flight-number').text()
    dateFlight = el.select('.//@data-date').text()
    groupId = el.select('.//@data-row-id').text()
    urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

    lastIdx = len(pre_arrivals1) - 1
    if lastIdx >= 0:
        if groupId == pre_arrivals1[lastIdx]["groupId"]:
            if not pre_arrivals1[lastIdx].has_key("codeshares"):
                pre_arrivals1[lastIdx]["codeshares"] = []
            pre_arrivals1[lastIdx]["codeshares"].append(flightno)
            continue
    flight = {
        "flightno" : flightno,
        "dateFlight" : dateFlight,
        "urlOfFlight" : urlOfFlight,
        "groupId" : groupId
    }
    pre_arrivals1.append(flight)

# ARRIVAL INTERNATIONAL
resp = g.go(urlArrInter)
pre_arrivals2 = []

for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
    flightno = el.select('.//@data-flight-number').text()
    dateFlight = el.select('.//@data-date').text()
    groupId = el.select('.//@data-row-id').text()
    urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

    lastIdx = len(pre_arrivals2) - 1
    if lastIdx >= 0:
        if groupId == pre_arrivals2[lastIdx]["groupId"]:
            if not pre_arrivals2[lastIdx].has_key("codeshares"):
                pre_arrivals2[lastIdx]["codeshares"] = []
            pre_arrivals2[lastIdx]["codeshares"].append(flightno)
            continue
    flight = {
        "flightno" : flightno,
        "dateFlight" : dateFlight,
        "urlOfFlight" : urlOfFlight,
        "groupId" : groupId
    }
    pre_arrivals2.append(flight)

pre_arrivals = pre_arrivals1 = pre_arrivals2
#arrivals = arrivals + getDetailFlightInfoByPreview(pre_arrivals)

# DEPARTURE DOMESTIC
resp = g.go(urlDepDomestic)
pre_departures1 = []

for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
    flightno = el.select('.//@data-flight-number').text()
    dateFlight = el.select('.//@data-date').text()
    groupId = el.select('.//@data-row-id').text()
    urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

    lastIdx = len(pre_departures1) - 1
    if lastIdx >= 0:
        if groupId == pre_departures1[lastIdx]["groupId"]:
            if not pre_departures1[lastIdx].has_key("codeshares"):
                pre_departures1[lastIdx]["codeshares"] = []
            pre_departures1[lastIdx]["codeshares"].append(flightno)
            continue
    flight = {
        "flightno": flightno,
        "dateFlight": dateFlight,
        "urlOfFlight": urlOfFlight,
        "groupId": groupId
    }
    pre_departures1.append(flight)

# DEPARTURE INTERNATIONAL
resp = g.go(urlDepInter)
pre_departures2 = []

for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
    flightno = el.select('.//@data-flight-number').text()
    dateFlight = el.select('.//@data-date').text()
    groupId = el.select('.//@data-row-id').text()
    urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

    lastIdx = len(pre_departures2) - 1
    if lastIdx >= 0:
        if groupId == pre_departures2[lastIdx]["groupId"]:
            if not pre_departures2[lastIdx].has_key("codeshares"):
                pre_departures2[lastIdx]["codeshares"] = []
            pre_departures2[lastIdx]["codeshares"].append(flightno)
            continue
    flight = {
        "flightno": flightno,
        "dateFlight": dateFlight,
        "urlOfFlight": urlOfFlight,
        "groupId": groupId
    }
    pre_departures2.append(flight)

pre_departures = pre_departures1 = pre_departures2
#departures = departures + getDetailFlightInfoByPreview(pre_departures)

resultBNE = {}
resultBNE["airport_id"] = "BNE"
resultBNE["departures"] = departures
resultBNE["arrivals"] = arrivals

jsonResult = json.dumps(resultBNE)
print jsonResult
