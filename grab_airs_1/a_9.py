from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=90, timeout=90)

datePattern = "%Y-%m-%d %H:%M:%S"
datePatternForUrl = "%Y-%m-%d"
nowTime = datetime.now()
departures = []
arrivals = []

ON_SCHEDULE = "on schedule"

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

        ON_SCHEDULE: SCHEDULED,
        ARRIVED:LANDED
    }.get(status, "")

def getFullDate(hourMinute, day):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getDataFromDocumentPKC(el, day):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""

    try:
        flightno = str(el.select('.//td[1]').text())
        flightno = flightno.encode("utf-8")
    except:
        flightno = ""

    try:
        rawScheduled = str(el.select('.//td[3]/div[1]').text())
        scheduled = getFullDate(rawScheduled, day)
    except:
        scheduled = ""

    try:
        rawEstimated = str(el.select('.//td[3]/div[2]').text())
        estimated = getFullDate(rawEstimated, day)
    except:
        estimated = ""

    try:
        rawStatus = str(el.select('.//td[4]').text())
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
    if estimated != "":
        result["estimated"] = estimated
    return result


# ARRIVALs

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayUrlAppendix = timeFourHourAgo.strftime(datePatternForUrl)
    urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + yesterdayUrlAppendix
    resp = g.go(urlPKC)

    for el in g.doc.select("//*[@id='incoming']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
        arrival = getDataFromDocumentPKC(el, timeFourHourAgo.day)
        arrivals.append(arrival)


# today
todayUrlAppendix = nowTime.strftime(datePatternForUrl)
urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + todayUrlAppendix
resp = g.go(urlPKC)

for el in g.doc.select("//*[@id='incoming']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
    arrival = getDataFromDocumentPKC(el, nowTime.day)
    arrivals.append(arrival)

# tomorrow
tomorrowTime = nowTime + timedelta(days=1)
tomorrowUrlAppendix = tomorrowTime.strftime(datePatternForUrl)
urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + tomorrowUrlAppendix
resp = g.go(urlPKC)

for el in g.doc.select("//*[@id='incoming']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
    arrival = getDataFromDocumentPKC(el, tomorrowTime.day)
    arrivals.append(arrival)

# DEPARTEDs

# four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    yesterdayUrlAppendix = timeFourHourAgo.strftime(datePatternForUrl)
    urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + yesterdayUrlAppendix
    resp = g.go(urlPKC)

    for el in g.doc.select("//*[@id='outgoing']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
        departure = getDataFromDocumentPKC(el, timeFourHourAgo.day)
        departures.append(departure)

# today
todayUrlAppendix = nowTime.strftime(datePatternForUrl)
urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + todayUrlAppendix
resp = g.go(urlPKC)

for el in g.doc.select("//*[@id='outgoing']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
    departure = getDataFromDocumentPKC(el, nowTime.day)
    departures.append(departure)

# tomorrow
tomorrowTime = nowTime + timedelta(days=1)
tomorrowUrlAppendix = tomorrowTime.strftime(datePatternForUrl)
urlPKC = "http://www.airport-pkc.ru/eng/flight/requestParams/date/" + tomorrowUrlAppendix

resp = g.go(urlPKC)

for el in g.doc.select("//*[@id='outgoing']//table/tbody/tr[contains(@class, 'not_hidcont')]"):
    departure = getDataFromDocumentPKC(el, tomorrowTime.day)
    departures.append(departure)

resultPKC = {}
resultPKC["airport_id"] = "PKC"
resultPKC["departures"] = departures
resultPKC["arrivals"] = arrivals

jsonResult = json.dumps(resultPKC)
#print jsonResultPKC
