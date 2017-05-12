from grab import Grab
import json
from datetime import datetime, timedelta

#11%00

g = Grab(connect_timeout=90, timeout=90)

datePattern = "%Y-%m-%d %H:%M:%S"
dateUrlPattern = "%Y-%m-%d"
nowTime = datetime.now()
departures = []
arrivals = []

FINAL_CALL = "final call"
LAST_BAG = "last bag"
FIRST_BAG = "first bag"
CAROUSEL_CLOSE = "carousel close"
CAROUSEL_OPEN = "carousel open"
DELAY = "delay"

OPEN = "open"
GATE_OPEN = "gate open"
GATE_CLOSED = "gate closed"

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

        FINAL_CALL:BOARDING,
        GATE_CLOSED:OUTGATE,
        GATE_OPEN:BOARDING,
        OPEN:BOARDING,
        CAROUSEL_OPEN:LANDED,
        LAST_BAG:LANDED,
        FIRST_BAG:LANDED,
        CAROUSEL_CLOSE:LANDED,
        DELAY:DELAYED,
    }.get(status, "")


def getDataFromDocumentKUL(el):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    gate = ""
    check_in_desks = ""
    destination = ""

    try:
        destination = str(el.select('.//td[1]').text())
    except:
        destination = ""

    try:
        flightno = str(el.select('.//td[4]').text())
    except:
        flightno = ""

    try:
        rawStatus = str.lower(el.select('.//td[5]').text())
        status = fixStatus(rawStatus)
    except:
        rawStatus = ""
    if status == "":
        status = SCHEDULED

    try:
        scheduled = el.select('.//td[6]').text()
    except:
        scheduled = ""

    try:
        estimated = str(el.select('.//td[7]').text())
    except:
        estimated = ""

    try:
        gate = str(el.select('.//td[8]').text())
    except:
        gate = ""

    try:
        check_in_desks = str(el.select('.//td[9]').text())
    except:
        check_in_desks = ""

    result = {
        "flightno": flightno,
        "scheduled": scheduled,
        "status": status,
        "raw_status": rawStatus,
        "destination": destination
    }
    if estimated != "":
        result["estimated"] = estimated

    if gate != "":
        result["gate"] = gate

    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    return result


#ARRIVALS

#four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    urlDate = timeFourHourAgo.strftime(dateUrlPattern)
    urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
    resp = g.go(urlKUL)

    for el in g.doc.select('//*[@id="arrival-flight"]/table/tbody/tr'):
        arrival = getDataFromDocumentKUL(el)
        arrivals.append(arrival)


#now
urlDate = nowTime.strftime(dateUrlPattern)
urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
resp = g.go(urlKUL)

for el in g.doc.select('//*[@id="arrival-flight"]/table/tbody/tr'):
    arrival = getDataFromDocumentKUL(el)
    arrivals.append(arrival)

#tomorrow

tomorrowTime = nowTime + timedelta(days=1)
urlDate = tomorrowTime.strftime(dateUrlPattern)
urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
resp = g.go(urlKUL)

for el in g.doc.select('//*[@id="arrival-flight"]/table/tbody/tr'):
    arrival = getDataFromDocumentKUL(el)
    arrivals.append(arrival)



# DEPARTURES
# four hours ago
timeFourHourAgo = nowTime - timedelta(hours=4)
if timeFourHourAgo.day != nowTime.day:

    urlDate = timeFourHourAgo.strftime(dateUrlPattern)
    urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
    resp = g.go(urlKUL)

    for el in g.doc.select('//*[@id="departure-flight"]/table/tbody/tr'):
        departure = getDataFromDocumentKUL(el)
        departures.append(departure)

# now
urlDate = nowTime.strftime(dateUrlPattern)
urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
resp = g.go(urlKUL)

for el in g.doc.select('//*[@id="departure-flight"]/table/tbody/tr'):
    departure = getDataFromDocumentKUL(el)
    departures.append(departure)

# tomorrow

tomorrowTime = nowTime + timedelta(days=1)
urlDate = tomorrowTime.strftime(dateUrlPattern)
urlKUL = "http://www.klia.com.my/index.php?m=airport&c=flight_schedule_details&date=" + urlDate + "&flighttype=departure&aid=1"
resp = g.go(urlKUL)

for el in g.doc.select('//*[@id="departure-flight"]/table/tbody/tr'):
    departure = getDataFromDocumentKUL(el)
    departures.append(departure)


def filterFlightByCodesahres(flights):
    resultFlights = []
    for flight in flights:
        wasCodeshareAdded = False
        if len(resultFlights) <= 0:
            resultFlights.append(flight)
        else:
            for resFligth in resultFlights:
                if resFligth['scheduled'] == flight['scheduled'] and resFligth['destination'] == flight['destination']:
                    if not resFligth.has_key("codeshares"):
                        resFligth['codeshares'] = []

                    if flight.has_key("check_in_desks") and resFligth.has_key("check_in_desks") \
                        or flight.has_key("gate") and resFligth.has_key("gate"):
                        break

                    if flight.has_key("check_in_desks") and not resFligth.has_key("check_in_desks"):
                        resFligth['check_in_desks'] = flight['check_in_desks']
                    if flight.has_key("gate") and not resFligth.has_key("gate"):
                        resFligth['gate'] = flight['gate']
                    if flight['status'] != "" and resFligth['status'] == "":
                        resFligth['status'] = flight['status']
                    if flight['raw_status'] != "" and resFligth['raw_status'] == "":
                        resFligth['raw_status'] = flight['raw_status']
                    resFligth['codeshares'].append(flight['flightno'])
                    wasCodeshareAdded = True
                    break
            if not wasCodeshareAdded:
                resultFlights.append(flight)

    for flight in resultFlights:
        flight.pop('destination', None)
    return resultFlights



resultKUL = {}
resultKUL["airport_id"] = "KUL"
resultKUL["arrivals"] = filterFlightByCodesahres(arrivals)
resultKUL["departures"] = filterFlightByCodesahres(departures)

jsonResult = json.dumps(resultKUL)
#print jsonResult



