from grab import Grab
import json
from datetime import datetime, timedelta
import re

g = Grab(connect_timeout=90, timeout=90)
g.setup(headers={"X-Requested-With":"XMLHttpRequest"})

CHECK_IN = "check-in"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CANCELED = "canceled"
AIRBORNE = "airborne"
ESTIMSTED = "estimated"

UNKNOWN = "unknown"
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

def getFullDate(hourMinute, day):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day, hour=h, minute=m, second=0)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime


def theRestOfFlights(dte, dateTime, isDeparture=False):
    pullEnded = "<h3>No results matched your query. Please refine your search.</h3></div></div>"
    startOffset = 60
    arResult = []

    if isDeparture:
        leg = "Departures"
    else:
        leg = "Arrivals"

    urlADL = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=" + dte + "&leg=" + leg

    postUrlParams = {
        "action": "flightsearch",
        "flt_no": "",
        "carrier": "All",
        "city": "",
        "dte": dte,
        "leg": leg,
        "offset": startOffset
    }

    theEnd = False
    while (not theEnd):
        resp = g.go(urlADL, post=postUrlParams)
        if resp.body == pullEnded or resp.code != 200:
            theEnd = True
            break
        for el in g.doc.select('//div[contains(@class, "SearchResultFlightListRow")]'):
            result = getDataFromDocumentADL(el, dateTime, isDeparture)
            arResult.append(result)

        postUrlParams["offset"] += 20
    return arResult

def getCurrentAirDay():
    url = "http://www.adelaideairport.com.au/"
    resp = g.go(url)
    day = -1

    airDate = g.doc.select('//*[@id="date"]').text()
    m = re.search("[a-zA-Z]+ (\d{1,2}) [a-zA-Z]+", airDate)
    if m:
        day = m.groups()[0]
    return day

def getDataFromDocumentADL(el, dateTime, isDeparted=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    gate = ""

    try:
        flightno = el.select('.//div[1]/div/div[2]').text()
    except:
        flightno = ""

    try:
        rawScheduled = str(el.select('.//div[3]/div/div[1]').text()) + " " + str(dateTime.day) + " " + str(dateTime.month) + " " + str(dateTime.year)
        rawScheduled = str.upper(rawScheduled)
        rawDateTime = datetime.strptime(rawScheduled, '%I:%M %p %d %m %Y')
        scheduled = rawDateTime.strftime(datePattern)
    except:
        scheduled = ""

    try:
        rawStatus = el.select('.//div[4]/div/div[2]').text()
        rawStatus = str.lower(rawStatus)
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        rawEstimated = str(el.select('.//div[3]/div/div[2]').text()) + " " + str(dateTime.day) + " " + str(dateTime.month) + " " + str(dateTime.year)
        rawEstimated = str.upper(rawEstimated)
        rawDateTime = datetime.strptime(rawEstimated, '%I:%M %p %d %m %Y')
        estimated = rawDateTime.strftime(datePattern)
        if status == LANDED or status == DEPARTED:
            actual = estimated
            estimated = ""
    except:
        estimated = ""
        actual = ""

    if isDeparted:
        try:
            gate = el.select('.//div[4]/div/div[1]').text()
        except:
            gate = ""

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
    return result

whetherCurDayIsYesterdayOnAirport = False
curAirDay = getCurrentAirDay()
if int(curAirDay) > nowTime.day:
    whetherCurDayIsYesterdayOnAirport = True

# Yesterday
timeFourHourAgo = nowTime - timedelta(hours=4)

if timeFourHourAgo.day != nowTime.day or whetherCurDayIsYesterdayOnAirport:
    yesterdayUrlADLArrivals = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Yesterday&leg=Arrivals"
    yesterdayUrlADLDeparture = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Yesterday&leg=Departures"

    # ARRIVE
    resp = g.go(yesterdayUrlADLArrivals)

    try:
        yesterdaySiteDayString = str(g.doc.select('/html/body/div/div[1]').text()).strip()
        arYesterdaySiteDay = yesterdaySiteDayString.split(" ")
        day = filter(str.isdigit, arYesterdaySiteDay[3])
        monthInWord = arYesterdaySiteDay[4]
        yesterdaySideDate = str(day) + " " + monthInWord + " " + str(nowTime.year)
        yesterdaySideDateTime = datetime.strptime(yesterdaySideDate, "%d %B %Y")
    except:
        yesterdaySideDateTime = timeFourHourAgo

    for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
        arrival = getDataFromDocumentADL(el, yesterdaySideDateTime)
        arrivals.append(arrival)

    restOfFlights = theRestOfFlights("Yesterday", yesterdaySideDateTime)
    arrivals = arrivals + restOfFlights

    # DEPARTURE
    resp = g.go(yesterdayUrlADLDeparture)

    for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
        departure = getDataFromDocumentADL(el, yesterdaySideDateTime, True)
        departures.append(departure)
    restOfFlights = theRestOfFlights("Yesterday", yesterdaySideDateTime, True)
    departures = departures + restOfFlights

# Today
todayUrlADLArrivals = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Today&leg=Arrivals"
todayUrlADLDeparture = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Today&leg=Departures"

# ARRIVE
resp = g.go(todayUrlADLArrivals)

try:
    todaySiteDayString = str(g.doc.select('/html/body/div/div[1]').text()).strip()
    arTodaySiteDay = todaySiteDayString.split(" ")
    day = filter(str.isdigit, arTodaySiteDay[3])
    monthInWord = arTodaySiteDay[4]
    todaySideDate = str(day) + " " + monthInWord + " " + str(nowTime.year)
    todaySideDateTime = datetime.strptime(todaySideDate, "%d %B %Y")
except:
    todaySideDateTime = nowTime

for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
    arrival = getDataFromDocumentADL(el, todaySideDateTime)
    arrivals.append(arrival)

restOfFlights = theRestOfFlights("Today", todaySideDateTime)
arrivals = arrivals + restOfFlights

# DEPARTURE
resp = g.go(todayUrlADLDeparture)

for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
    departure = getDataFromDocumentADL(el, todaySideDateTime, True)
    departures.append(departure)
restOfFlights = theRestOfFlights("Today", todaySideDateTime, True)
departures = departures + restOfFlights



# Tomorrow
tomorrowUrlADLArrivals = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Tomorrow&leg=Arrivals"
tomorrowUrlADLDeparture = "http://www.adelaideairport.com.au/wp-admin/admin-ajax.php?action=flightsearch&flt_no=&carrier=All&city=&dte=Tomorrow&leg=Departures"
tomorrowTime = nowTime + timedelta(days=1)

# ARRIVE
resp = g.go(tomorrowUrlADLArrivals)

try:
    tomorrowSiteDayString = str(g.doc.select('/html/body/div/div[1]').text()).strip()
    arTomorrowSiteDay = tomorrowSiteDayString.split(" ")
    day = filter(str.isdigit, arTomorrowSiteDay[3])
    monthInWord = arTomorrowSiteDay[4]
    tomorrowSideDate = str(day) + " " + monthInWord + " " + str(nowTime.year)
    tomorrowSideDateTime = datetime.strptime(tomorrowSideDate, "%d %B %Y")
except:
    tomorrowSideDateTime = tomorrowTime


for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
    arrival = getDataFromDocumentADL(el, tomorrowSideDateTime)
    arrivals.append(arrival)

restOfFlights = theRestOfFlights("Tomorrow", tomorrowSideDateTime)
arrivals = arrivals + restOfFlights

# DEPARTURE
resp = g.go(tomorrowUrlADLDeparture)

for el in g.doc.select('//div[contains(@class, "SearchResultFlightListTable")]/div/div'):
    departure = getDataFromDocumentADL(el, tomorrowSideDateTime, True)
    departures.append(departure)

restOfFlights = theRestOfFlights("Tomorrow", tomorrowSideDateTime, True)
departures = departures + restOfFlights

resultADL = {}
resultADL["airport_id"] = "ADL"
resultADL["departures"] = departures
resultADL["arrivals"] = arrivals

jsonResult = json.dumps(resultADL)
#print jsonResult
