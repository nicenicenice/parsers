# -*- coding: utf-8 -*-

#15:30

from grab import Grab
import time
import json
from datetime import datetime, timedelta
from lxml.html import fromstring
import re

g = Grab(connect_timeout=90, timeout=90)
datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

GATE = "gate"
DEPARTURE = "departure"
AIRBORNE = "airborne"
BOARDING_CLOSED = "boarding closed"
ON_TIME = "on time"
CHECK_IN = "check-in"
ARRIVED = "arrived"
LATE = "late"
LAST_CALL = "last call"
GATE_CLOSED = "gate closed"
FINAL_CALL = "final call"
GATE_OPEN = "gate open"

LUGGAGE = "luggage"
SCHEDULED = "scheduled"
DELAYED = "delayed"
CANCELLED = "cancelled"
CHECKIN = "checkin"
BOARDING = "boarding"
OUTGATE = "outgate"
DEPARTED = "departed"
EXPECTED = "expected"
LANDED = "landed"

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime
    day = scheduleDateTime.day

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=day, hour=h, minute=m, second=0)

    if h < 5 and scheduleDateTime.hour > 20:
        notFormatedTime += timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

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

        LUGGAGE:LANDED,
        GATE:OUTGATE,
        DEPARTURE:DELAYED,
        AIRBORNE:DEPARTED,
        CHECK_IN:CHECKIN,
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

def getDataFromDocumentKRR(el, justToAddRestInfo=False, isDeparture=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    check_in_desks = ""
    gate = ""

    if justToAddRestInfo:
        #print el.text_content()
        try:
            some_status = el.xpath('./div/div[2]/ul/li[1]/div/p')[0].text_content()
            if some_status == "Departure is expected":
                estimated = el.xpath('./div/div[2]/ul/li[2]/div/div/p')[0].text_content()
        except:
            pass
        try:
            checkInDesksString = el.xpath('./div/div[2]/ul/li[1]/div/div/p[2]')[0].text_content()
            check_in_desks = checkInDesksString[checkInDesksString.find(" ") + 1:]
            #check_in_desks = getFormatedCheckinDesks(check_in_desks)
        except:
            check_in_desks = ""

        try:
            gateString = el.xpath('./div/div[2]/ul/li[2]/div/div/p[2]')[0].text_content()
            gate = gateString[gateString.find(" ") + 1:]
        except:
            gate = ""
        result = {
            "check_in_desks":check_in_desks,
            "gate" : gate
        }
        if estimated != "":
            result['estimated'] = estimated
        return result

    try:
        timestamp = el.xpath('./@data-time')

        scheduledDateTime = datetime.fromtimestamp(int(timestamp[0]) + 3 * 60 * 60)
        scheduled = scheduledDateTime.strftime('%Y-%m-%d %H:%M:%S')

        #rawStatus = el.xpath('./div/div[2]/span')[0].text_content()
    except:
        scheduled = ""

    try:
        rawStatus = el.xpath('./div/div[7]')[0].text_content()
        rawStatus = str.strip(rawStatus)
        rawStatus = str.lower(rawStatus)
        if rawStatus.find(" ") >= 0:
            matched = re.search("([a-zA-Z-]+).*? ([\.\s\d\:]+)", rawStatus)
            if matched:
                shortRawStatus = matched.groups()[0]
                shortRawStatus = str.lower(shortRawStatus)

                if isDeparture and (rawStatus.find("delayed") >= 0 or rawStatus.find("expected") >= 0):
                    if matched.groups()[1].find(" ") >= 0:
                        newDate = matched.groups()[1] + " " + str(scheduledDateTime.year)
                        newDateTime = datetime.strptime(newDate, "%d.%m %H:%M %Y")
                        estimated = newDateTime.strftime(datePattern)
                    else:
                        estimated = getFullDate(matched.groups()[1], scheduledDateTime)
                if shortRawStatus == LANDED or shortRawStatus == AIRBORNE:
                    actual = getFullDate(matched.groups()[1], scheduledDateTime)
            status = fixStatus(shortRawStatus)
        else:
            status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""
        actual = ""
    if status == "":
        status = SCHEDULED

    try:
        flightno = el.xpath('./div/div[3]/span')[0].text_content()
        flightno = flightno.encode("utf-8")
    except:
        flightno = ""

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
    return result

def mergeFlights(arr1, arr2):
    result = []
    result = arr1
    for flight in arr2:
        if flight not in result:
            result.append(flight)
    return result

def getTimeStampFromDateTime(datetime):
    return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

def printHtml(timestampFrom, isDep=False):
    url = "http://basel.aero/en/ajax/ajax.php"

    postParams = {
        "action": "score",
        "sessid": "",
        "start_date_arrive": timestampFrom,
        "start_date_depart": timestampFrom,
        "url": "/en/krasnodar/passengers/online-schedule/"
    }

    if isDep:
        typeOfFlight = "depart"
    else:
        typeOfFlight = "arrival"

    try:
        resp = g.go(url, post=postParams)
        respJson = json.loads(resp.body)
        print respJson[typeOfFlight]
    except:
        pass

def getDomTreeFromResponse(timestampFrom, isDeparture=False):
    url = "http://basel.aero/en/ajax/ajax.php"

    postParams = {
        "action":"score",
        "sessid":"",
        "start_date_arrive":timestampFrom,
        "start_date_depart":timestampFrom,
        "url":"/en/krasnodar/passengers/online-schedule/"
    }

    if isDeparture:
        typeOfFlight = "depart"
    else:
        typeOfFlight = "arrival"

    theEnd = False
    while not theEnd:
        try:
            resp = g.go(url, post=postParams)
            respJson = json.loads(resp.body)
            dom = fromstring(respJson[typeOfFlight])
            theEnd = True
            break
        except:
           continue
    return dom

#respJson['depart']
#print respJson['arrival']

fourHourAgoDateTime = nowTime - timedelta(hours=4)

timestampFrom = getTimeStampFromDateTime(fourHourAgoDateTime)
nextTimestamp1 = timestampFrom + 6 * 60 * 60
nextTimestamp2 = nextTimestamp1 + 6 * 60 * 60
nextTimestamp3 = nextTimestamp2 + 6 * 60 * 60
nextTimestamp4 = nextTimestamp3 + 6 * 60 * 60


arrivals1 = []
arrivals2 = []
arrivals3 = []
arrivals4 = []
arrivals5 = []

dom = getDomTreeFromResponse(timestampFrom, False)
#printHtml(timestampFrom, False)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        arrival = getDataFromDocumentKRR(el, False, False)
        arrivals1.append(arrival)
    else:
        data = getDataFromDocumentKRR(el, True, False)
        if data.has_key("estimated") and data["estimated"] != "":
            scheduled = arrivals1[len(arrivals1) - 1]["scheduled"]
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            estimated = getFullDate(data["estimated"], scheduleDateTime)
            arrivals1[len(arrivals1) - 1]["estimated"] = estimated


dom = getDomTreeFromResponse(nextTimestamp1, False)
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        arrival = getDataFromDocumentKRR(el, False, False)
        arrivals2.append(arrival)
    else:
        data = getDataFromDocumentKRR(el, True, False)
        if data.has_key("estimated") and data["estimated"] != "":
            scheduled = arrivals2[len(arrivals2) - 1]["scheduled"]
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            estimated = getFullDate(data["estimated"], scheduleDateTime)
            arrivals2[len(arrivals2) - 1]["estimated"] = estimated

dom = getDomTreeFromResponse(nextTimestamp2, False)
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        arrival = getDataFromDocumentKRR(el, False, False)
        arrivals3.append(arrival)
    else:
        data = getDataFromDocumentKRR(el, True, False)
        if data.has_key("estimated") and data["estimated"] != "":
            scheduled = arrivals3[len(arrivals3) - 1]["scheduled"]
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            estimated = getFullDate(data["estimated"], scheduleDateTime)
            arrivals3[len(arrivals3) - 1]["estimated"] = estimated

dom = getDomTreeFromResponse(nextTimestamp3, False)
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        arrival = getDataFromDocumentKRR(el, False, False)
        arrivals4.append(arrival)
    else:
        data = getDataFromDocumentKRR(el, True, False)
        if data.has_key("estimated") and data["estimated"] != "":
            scheduled = arrivals4[len(arrivals4) - 1]["scheduled"]
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            estimated = getFullDate(data["estimated"], scheduleDateTime)
            arrivals4[len(arrivals4) - 1]["estimated"] = estimated

dom = getDomTreeFromResponse(nextTimestamp4, False)
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        arrival = getDataFromDocumentKRR(el, False, False)
        arrivals5.append(arrival)
    else:
        data = getDataFromDocumentKRR(el, True, False)
        if data.has_key("estimated") and data["estimated"] != "":
            scheduled = arrivals5[len(arrivals5) - 1]["scheduled"]
            scheduleDateTime = datetime.strptime(scheduled, datePattern)
            estimated = getFullDate(data["estimated"], scheduleDateTime)
            arrivals5[len(arrivals5) - 1]["estimated"] = estimated

arrivals12 = mergeFlights(arrivals1, arrivals2)
arrivals34 = mergeFlights(arrivals3, arrivals4)
arrivals = mergeFlights(arrivals12, arrivals34)
arrivals = mergeFlights(arrivals, arrivals5)



departures1 = []
departures2 = []
departures3 = []
departures4 = []
departures5 = []

dom = getDomTreeFromResponse(timestampFrom, True)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    i += 1
    if i % 2 != 0:
        departure = getDataFromDocumentKRR(el, False, True)
        departures1.append(departure)
    else:
        data = getDataFromDocumentKRR(el, True)
        if data["gate"] != "":
            departures1[len(departures1) - 1]["gate"] = data["gate"]
        if data["check_in_desks"] != "":
            departures1[len(departures1) - 1]["check_in_desks"] = data["check_in_desks"]

dom = getDomTreeFromResponse(nextTimestamp1, True)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    try:
        a = el.xpath("./div/strong").text_content()
    except:
        i += 1
        if i % 2 != 0:
            departure = getDataFromDocumentKRR(el, False, True)
            departures2.append(departure)
        else:
            data = getDataFromDocumentKRR(el, True)
            if data["gate"] != "":
                departures2[len(departures2) - 1]["gate"] = data["gate"]
            if data["check_in_desks"] != "":
                departures2[len(departures2) - 1]["check_in_desks"] = data["check_in_desks"]

dom = getDomTreeFromResponse(nextTimestamp2, True)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    try:
        a = el.xpath("./div/strong").text_content()
    except:
        i += 1
        if i % 2 != 0:
            departure = getDataFromDocumentKRR(el, False, True)
            departures3.append(departure)
        else:
            data = getDataFromDocumentKRR(el, True)
            if data["gate"] != "":
                departures3[len(departures3) - 1]["gate"] = data["gate"]
            if data["check_in_desks"] != "":
                departures3[len(departures3) - 1]["check_in_desks"] = data["check_in_desks"]

dom = getDomTreeFromResponse(nextTimestamp3, True)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    try:
        a = el.xpath("./div/strong").text_content()
    except:
        i += 1
        if i % 2 != 0:
            departure = getDataFromDocumentKRR(el, False, True)
            departures4.append(departure)
        else:
            data = getDataFromDocumentKRR(el, True)
            if data["gate"] != "":
                departures4[len(departures4) - 1]["gate"] = data["gate"]
            if data["check_in_desks"] != "":
                departures4[len(departures4) - 1]["check_in_desks"] = data["check_in_desks"]

dom = getDomTreeFromResponse(nextTimestamp4, True)
i = 0
for el in dom.xpath("./div[contains(@class, 'hide') or contains(@class ,'dev-not-hide')]"):
    try:
        a = el.xpath("./div/strong").text_content()
    except:
        i += 1
        if i % 2 != 0:
            departure = getDataFromDocumentKRR(el, False, True)
            departures5.append(departure)
        else:
            data = getDataFromDocumentKRR(el, True)
            if data["gate"] != "":
                departures5[len(departures5) - 1]["gate"] = data["gate"]
            if data["check_in_desks"] != "":
                departures5[len(departures5) - 1]["check_in_desks"] = data["check_in_desks"]

departures12 = mergeFlights(departures1, departures2)
departures34 = mergeFlights(departures3, departures4)
departures = mergeFlights(departures12, departures34)
departures = mergeFlights(departures, departures5)

resultKRR = {}
resultKRR["airport_id"] = "KRR"
resultKRR["departures"] = departures
resultKRR["arrivals"] = arrivals

jsonResult = json.dumps(resultKRR)
#print jsonResult
