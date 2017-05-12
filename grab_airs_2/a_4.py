from grab import Grab
import json
from datetime import datetime, timedelta
import re
import time

g = Grab(connect_timeout=90, timeout=90)
g.setup(headers={
    "Accept":"application/json, text/plain, */*",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
})

datePattern = "%Y-%m-%d %H:%M:%S"

nowTime = datetime.now()
departures = []
arrivals = []

GO_TO_GATE = "go to gate"
CHECK_IN = "check-in"
BOARD_SOON = "board soon"
ARRIVING = "arriving"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
DELAY = "delay"
UNKNOWN = "unknown"
SCHEDULE_CHANGE = "schedule change"

ON_TIME = "on time"
ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"
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
        DELAY:DELAYED,
        SCHEDULE_CHANGE:EXPECTED,
        ON_TIME:SCHEDULED,
        BOARD_SOON:SCHEDULED,
        ARRIVING:EXPECTED,
        CHECK_IN:CHECKIN,
        GO_TO_GATE:BOARDING,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED,
        "":SCHEDULED
    }.get(status, UNKNOWN)

def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

def getFitFlightsWithCodeShares(arFlights):
    result = []
    for i in range(0, len(arFlights) - 1):

        if i > 0:
            lastIdxResult = len(result) - 1

            if arFlights[i]["scheduled"] == result[lastIdxResult]["scheduled"] and \
                            arFlights[i]["status"] == result[lastIdxResult]["status"] and \
                            arFlights[i]["raw_status"] == result[lastIdxResult]["raw_status"] and \
                            arFlights[i]["terminal"] == result[lastIdxResult]["terminal"]:
                if arFlights[i].has_key("actual") and result[lastIdxResult].has_key("actual"):
                    if arFlights[i]["actual"] == result[lastIdxResult]["actual"]:
                        if not result[lastIdxResult].has_key("codeshares"):
                            result[lastIdxResult]["codeshares"] = []
                        result[lastIdxResult]["codeshares"].append(arFlights[i]["flightno"])
                        continue
                if arFlights[i].has_key("estimated") and result[lastIdxResult].has_key("estimated"):
                    if arFlights[i]["estimated"] == result[lastIdxResult]["estimated"]:
                        if not result[lastIdxResult].has_key("codeshares"):
                            result[lastIdxResult]["codeshares"] = []
                        result[lastIdxResult]["codeshares"].append(arFlights[i]["flightno"])
                        continue
            result.append(arFlights[i])
        else:
            result.append(arFlights[i])
    return result

def getDataFromDocumentTPE(flight, isDeparture=False, isCargo=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    terminal = ""
    luggage = ""
    gate = ""
    check_in_desks = ""

    try:
        rawScheduled = str(flight['ODate'] + " " + flight['OTime'])
        scheduled = rawScheduled.replace("/", "-")
    except:
        scheduled = ""

    try:
        rawStatus = flight['Memo']
        rawStatus = rawStatus.encode("utf-8")

        m = re.search("([a-zA-Z ]+)", rawStatus)
        if m:
            rawStatus = str.lower(m.groups()[0]).strip()

        if status == "":
            status = fixStatus(rawStatus)
    except:
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        flightno = flight['ACode'] + "-" + flight['FlightNo']
    except:
        flightno = ""

    try:
        rawAddTime = str(flight['RDate'] + " " + flight['RTime'])
        addTime = rawAddTime.replace("/", "-")
        if status == LANDED or status == DEPARTED:
            actual = addTime
        else:
            estimated = addTime
        try:
            if rawStatus == SCHEDULE_CHANGE:
                scheduleDateTime = datetime.strptime(scheduled, datePattern)
                scheduleTimeStamp = getTimeStampFromDateTime(scheduleDateTime)
                estimatedDateTime = datetime.strptime(estimated, datePattern)
                estimatedTimeStamp = getTimeStampFromDateTime(estimatedDateTime)
                diff = estimatedTimeStamp - scheduleTimeStamp
                if diff >= 0 and diff >= 15 * 60:
                    status = DELAYED
                else:
                    status = SCHEDULED
        except:
            pass
    except:
        actual = ""
        estimated = ""
        addTime = ""

    try:
        terminal = "T" + str(flight['BNo'])
    except:
        terminal = ""

    if not isDeparture and not isCargo:
        try:
            luggage = str(flight['StopCode'])
        except:
            luggage = ""

    if isDeparture:
        try:
            gate = flight['Gate']
        except:
            gate = ""
        if not isCargo:
            try:
                check_in_desks = flight['CheckIn']
            except:
                check_in_desks = ""


    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }

    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    if terminal != "":
        result["terminal"] = terminal
    if luggage != "":
        result["luggage"] = luggage
    if gate != "":
        result["gate"] = gate
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual
    return result


fullDateUrlPattern = "%Y/%m/%d %H:%M:%S"
shortDateUrlPattern = "%Y/%m/%d"

fourHoursAgoDateTime = nowTime - timedelta(hours=4)
fourHoursAgoFormatedFullTime = fourHoursAgoDateTime.strftime(fullDateUrlPattern)

curFormatedFullTime = nowTime.strftime(fullDateUrlPattern)
curFormatedShortTime = nowTime.strftime(shortDateUrlPattern)

tomorrowDateTime = nowTime + timedelta(days=1)
tomorrowFormatedFullTime = tomorrowDateTime.strftime(fullDateUrlPattern)

postParams = {
    #"ACode":{"originalObject: {}},
    "BNo":"0",
    #"CityName":{"originalObject": {}},
    "EndDT":tomorrowFormatedFullTime,
    "ODate":curFormatedShortTime,
    "StartDT":fourHoursAgoFormatedFullTime,
    #"airname":{"originalObject": {}}
}


urlTPEArrivals = "http://www.taoyuan-airport.com/api/english/Flight/Arrival"
resp = g.go(urlTPEArrivals, post=postParams)

jsonResponse = json.loads(resp.body)
for flight in jsonResponse["Data"]:
    arrival = getDataFromDocumentTPE(flight)
    arrivals.append(arrival)

urlTPEDepartures = "http://www.taoyuan-airport.com/api/english/Flight/Departure"
resp = g.go(urlTPEDepartures, post=postParams)
jsonResponse = json.loads(resp.body)

for flight in jsonResponse["Data"]:
    departure = getDataFromDocumentTPE(flight, True)
    departures.append(departure)


# Cargo flights
urlTPECargoArrivals = "http://www.taoyuan-airport.com/api/english/Flight/CargoArrival"
resp = g.go(urlTPECargoArrivals, post=postParams)

jsonResponse = json.loads(resp.body)
for flight in jsonResponse["Data"]:
    arrival = getDataFromDocumentTPE(flight, False, True)
    arrivals.append(arrival)


urlTPEDepartures = "http://www.taoyuan-airport.com/api/english/Flight/CargoDeparture"
resp = g.go(urlTPEDepartures, post=postParams)
jsonResponse = json.loads(resp.body)

for flight in jsonResponse["Data"]:
    departure = getDataFromDocumentTPE(flight, True, True)
    departures.append(departure)

resultTPE = {}
resultTPE["airport_id"] = "TPE"
resultTPE["arrivals"] = getFitFlightsWithCodeShares(arrivals)
resultTPE["departures"] = getFitFlightsWithCodeShares(departures)
jsonResult = json.dumps(resultTPE)
#print jsonResult

