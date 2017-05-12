from grab import Grab
import json
from datetime import datetime, timedelta

#14%05
g = Grab(connect_timeout=90, timeout=90)

UNKNOWN = "unknown"
ON_TIME = "on time"
CHECK_IN = "check in"

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
        ON_TIME:SCHEDULED,
        GATE_CLOSED:OUTGATE,
        FINAL_CALL:BOARDING,
        GATE_OPEN:BOARDING,
        ARRIVED:LANDED,
        LATE: DELAYED,
        "":SCHEDULED
    }.get(status, UNKNOWN)

def getFullDate(hourMinute, day):

    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

departures = []
arrivals = []
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()

def getDataFromDocumentKHH(el, day, isArrival=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        flightno = str(el.select('.//div[4]/div[2]').text())
    except:
        flightno = ""

    try:
        rawStatus = el.select('.//div[8]/div[2]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        rawScheduled = str(el.select('.//div[1]/div[2]').text())
        scheduled = getFullDate(rawScheduled, day)
    except:
        scheduled = ""

    try:
        if status == LANDED or status == DEPARTED:
            rawActual = str(el.select('.//div[2]/div[2]').text())
            actual = getFullDate(rawActual, day)
        else:
            rawEstimated = str(el.select('.//div[2]/div[2]').text())
            estimated = getFullDate(rawEstimated, day)
    except:
        actual = ""
        estimated = ""

    if not isArrival:
        try:
            gate = str(el.select('.//div[7]/div[2]').text())
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
    if actual != "":
        result["actual"] = actual
    if gate != "":
        result["gate"] = gate
    return result

datePatternFromPage = "%Y/%m/%d"
# YESTERDAY

timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:
    # arrivals
    urlKHHArrival = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=2&AirLineDate=3&All=1"
    resp = g.go(urlKHHArrival)

    time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
    yesterdayDateTime = datetime.strptime(time, datePatternFromPage)

    for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
        arrival = getDataFromDocumentKHH(el, yesterdayDateTime.day, True)
        arrivals.append(arrival)

    # departures
    urlKHHDepartures = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=1&AirLineDate=3&All=1"
    resp = g.go(urlKHHDepartures)

    time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
    yesterdayDateTime = datetime.strptime(time, datePatternFromPage)

    for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
        departure = getDataFromDocumentKHH(el, yesterdayDateTime.day)
        departures.append(departure)

# NOW
# arrivals
urlKHHArrival = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=2&AirLineDate=1&All=1"
resp = g.go(urlKHHArrival)

time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
nowDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
    arrival = getDataFromDocumentKHH(el, nowDateTime.day, True)
    arrivals.append(arrival)

# departures
urlKHHDepartures = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=1&AirLineDate=1&All=1"
resp = g.go(urlKHHDepartures)

time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
nowDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
    departure = getDataFromDocumentKHH(el, nowDateTime.day)
    departures.append(departure)

# TOMORROW

# arrivals
urlKHHArrival = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=2&AirLineDate=2&All=1"
resp = g.go(urlKHHArrival)

time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
tomorrowDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
    arrival = getDataFromDocumentKHH(el, tomorrowDateTime.day, True)
    arrivals.append(arrival)

# departures
urlKHHDepartures = "http://www.kia.gov.tw/English/InstantScheduleE006110.aspx?ArrDep=1&AirLineDate=2&All=1"
resp = g.go(urlKHHDepartures)

time = g.doc.select('//*[@id="block"]/div[3]/div[1]/p/span').text()
tomorrowDateTime = datetime.strptime(time, datePatternFromPage)

for el in g.doc.select('//*[@id="block"]/div[3]/div[2]/div[2]/div'):
    departure = getDataFromDocumentKHH(el, tomorrowDateTime.day)
    departures.append(departure)

resultKHH = {}
resultKHH["airport_id"] = "KHH"
resultKHH["departures"] = departures
resultKHH["arrivals"] = arrivals

jsonResult = json.dumps(resultKHH)
#print jsonResult