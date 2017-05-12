from grab import Grab
import json
from datetime import datetime, timedelta
import re



CONFIRMED = "confirmed"
NEW_GATE = "new gate"
ON_TIME = "on time"

SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"



CLOSED = "closed"
FINAL_CALL = "final call"


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

        CLOSED: OUTGATE,
        FINAL_CALL: BOARDING,
        NEW_GATE: BOARDING,
        CONFIRMED: EXPECTED
    }.get(status, "")

def getFullDate(hourMinute, justToday=False):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    if justToday == False:
        if h < nowTime.hour or (h == nowTime.hour and m < nowTime.minute):
            correctDate += timedelta(days=1)

    notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

departures = []
arrivals = []
g = Grab(connect_timeout=195, timeout=195)

datePattern = "%Y-%m-%d"
nowTime = datetime.now()
formatedNowTime = nowTime.strftime(datePattern)

urlCNXArrived = "http://chiangmaiairportthai.com/en/278-passenger-arrivals?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
resp = g.go(urlCNXArrived)

def getDataFromDocument(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    gate = ""

    try:
        flightno = str(el.select('.//td[2]').text())
        if len(flightno) <= 0:
            return -1
    except:
        return -1

    try:
        rawScheduled = str(el.select('.//td[3]').text())
        #print rawScheduled
        scheduled = getFullDate(rawScheduled, True)
    except:
        scheduled = ""

    try:
        estiActialTime = str(el.select('.//td[4]').text())
        estiActialTime = getFullDate(estiActialTime, True)
    except:
        estiActialTime = ""

    try:
        gateTerminal = str(el.select('.//td[6]').text())
        m = re.search("Gate(\d{2}) Terminal \w?", gateTerminal)
        if m:
            gate = str.lower(m.groups()[0])
    except:
        gate = ""

    try:
        rawStatus = str(el.select('.//td[7]/span').text())
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)

        if len(rawStatus) > 0:
            if rawStatus == CONFIRMED:
                estimated = estiActialTime
            elif rawStatus == DELAYED:
                estimated = estiActialTime
            if estimated == "":
                actual = estiActialTime
    except:
        status = ""
        rawStatus = ""
        actual = ""
        estimated = ""

    if len(status) <= 0:
        status = SCHEDULED

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus
    }
    if gate != "":
        result["gate"] = gate
    if estimated != "":
        result["estimated"] = estimated
    if actual != "":
        result["actual"] = actual

    return result

urlCNXArrived = "http://chiangmaiairportthai.com/en/278-passenger-arrivals?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
resp = g.go(urlCNXArrived)

for el in g.doc.select('//*[@id="mid-container"]//table/tbody/tr'):
    arrival = getDataFromDocument(el)
    if arrival != -1:
        arrivals.append(arrival)

urlCNXDepartured = "http://www.chiangmaiairportthai.com/en/279-passenger-departures?after_search=1&page=&date=" + formatedNowTime + "&airport=0&flight_no=&start_time=00%3A00&end_time=23%3A59&airline=0"
resp = g.go(urlCNXDepartured)

for el in g.doc.select('//*[@id="mid-container"]//table/tbody/tr'):
    departure = getDataFromDocument(el)
    if departure != -1:
        departures.append(departure)

resultCNX = {}
resultCNX["airport_id"] = "CNX"
resultCNX["departures"] = departures
resultCNX["arrivals"] = arrivals
jsonResultCNX = json.dumps(resultCNX)
print jsonResultCNX

