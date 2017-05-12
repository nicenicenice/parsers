from grab import Grab
import json
from datetime import datetime, timedelta
import re
import time


CHECKIN_OPEN = "ch-in open"
CHECKIN_CLOSE = "ch-in close"
CONFIRMED = "confirmed"

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

        CONFIRMED:SCHEDULED,
        CHECKIN_CLOSE:BOARDING,
        CHECKIN_OPEN:CHECKIN,
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

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
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

def getFormatedCheckinDesks(checkinStr):
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

def getDataFromDocumentBKK(el, dateTime):
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
        rawScheduled = el.select('.//td[3]').text()

        h = int(rawScheduled[:2])
        m = int(rawScheduled[3:])

        dateTimeToCorrect = dateTime
        scheduleDateTime = dateTimeToCorrect.replace(hour=h, minute=m, second=0)
        scheduled = scheduleDateTime.strftime(datePattern)
    except:
        return -1

    try:
        rawFlightno = el.select('.//td[2]').text()
        flightno = rawFlightno.encode("utf-8")
    except:
        flightno = ""

    try:
        rawStatus = el.select('.//td[7]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
        if status == "" and rawStatus != "":
            status = UNKNOWN
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        rawAdditionTime = el.select('.//td[4]').text()
        additionTime = getFullDate(rawAdditionTime, scheduleDateTime)
        if status == LANDED or status == DEPARTED:
            actual = additionTime
        elif rawStatus == CONFIRMED:
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            scheduleTimeStamp = getTimeStampFromDateTime(scheduleDateTime)

            additionDateTime = datetime.strptime(additionTime, datePattern)
            additionTimeStamp = getTimeStampFromDateTime(additionDateTime)
            diff = abs(scheduleTimeStamp - additionTimeStamp)
            if diff >= 15 * 60:
                status = DELAYED
            estimated = additionTime
        else:
            estimated = additionTime
    except:
        actual = ""
        estimated = ""

    try:
        addInfoString = el.select('.//td[6]').text()
        if addInfoString.find("Gate") >= 0 and status != CANCELLED:
            gate = addInfoString[addInfoString.find("Gate") + 5:addInfoString.find("Gate") + 8].strip()
        if addInfoString.find("Terminal") >= 0:
            terminal = addInfoString[addInfoString.find("Terminal") + 9:addInfoString.find("Terminal") + 11].strip()
    except:
        gate = ""
        terminal = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if actual != "":
        result["actual"] = actual
    if estimated != "":
        result["estimated"] = estimated
    if gate != "":
        result["gate"] = gate
    if terminal != "":
        result["terminal"] = terminal
    return result

def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

def getDataForMaxSec(dateTime, maxSec, isDeparture=False):
    future = time.time() + maxSec
    urlPattern = "%Y-%m-%d"
    todayDate = dateTime.strftime(urlPattern)

    while time.time() < future:
        g = Grab(connect_timeout=4 * 10, timeout=4 * 10)

        if isDeparture:
            typeOfFlight = "4-passenger-departures"
        else:
            typeOfFlight = "3-passenger-arrivals"

        try:
            urlBKK = "http://www.suvarnabhumiairport.com/en/" + typeOfFlight + "?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
            print urlBKK
            resp = g.go(urlBKK)
            return g
        except:
            pass
        pass


startTime = time.time()
# TODAY
#urlBKKArrives= "http://www.suvarnabhumiairport.com/en/3-passenger-arrivals?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
#resp = g.go(urlBKKArrives)

g = getDataForMaxSec(nowTime, 160, False)

for el in g.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
    arrival = getDataFromDocumentBKK(el, nowTime)
    if arrival == -1:
        try:
            flightno = el.select('.//td[2]').text()
        except:
            continue
        if not arrivals[len(arrivals) - 1].has_key("codeshares"):
            arrivals[len(arrivals) - 1]["codeshares"] = []
        arrivals[len(arrivals) - 1]["codeshares"].append(flightno)
    else:
        arrivals.append(arrival)


#urlBKKDepartures = "http://www.suvarnabhumiairport.com/en/4-passenger-departures?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
#resp = g.go(urlBKKDepartures)
g = getDataForMaxSec(nowTime, 160, True)

for el in g.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
    departure = getDataFromDocumentBKK(el, nowTime)
    if departure == -1:
        try:
            flightno = el.select('.//td[2]').text()
        except:
            continue
        if not departures[len(departures) - 1].has_key("codeshares"):
            departures[len(departures) - 1]["codeshares"] = []
        departures[len(departures) - 1]["codeshares"].append(flightno)
    else:
        departures.append(departure)
"""
# TOMORROW
tomorrowDateTime = nowTime + timedelta(days=1)

g = getDataForMaxSec(tomorrowDateTime, 160, False)

for el in g.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
    arrival = getDataFromDocumentBKK(el, nowTime)
    if arrival == -1:
        try:
            flightno = el.select('.//td[2]').text()
        except:
            continue
        if not arrivals[len(arrivals) - 1].has_key("codeshares"):
            arrivals[len(arrivals) - 1]["codeshares"] = []
        arrivals[len(arrivals) - 1]["codeshares"].append(flightno)
    else:
        arrivals.append(arrival)

#urlBKKDepartures = "http://www.suvarnabhumiairport.com/en/4-passenger-departures?after_search=1&page=&date=" + todayDate + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
#resp = g.go(urlBKKDepartures)
g = getDataForMaxSec(tomorrowDateTime, 160, True)

for el in g.doc.select("//*[@id='mid-container']/div/div/div[2]/div[2]/div[1]/table/tbody/tr"):
    departure = getDataFromDocumentBKK(el, nowTime)
    if departure == -1:
        try:
            flightno = el.select('.//td[2]').text()
        except:
            continue
        if not departures[len(departures) - 1].has_key("codeshares"):
            departures[len(departures) - 1]["codeshares"] = []
        departures[len(departures) - 1]["codeshares"].append(flightno)
    else:
        departures.append(departure)
"""
finishTime = time.time()
diffTime = abs(startTime - finishTime) / 60

resultBKK = {}
resultBKK["airport_id"] = "BKK"
resultBKK["departures"] = departures
resultBKK["arrivals"] = arrivals

jsonResult = json.dumps(resultBKK)
print jsonResult