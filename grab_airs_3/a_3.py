from grab import Grab
import json
from datetime import datetime, timedelta

g = Grab(connect_timeout=70, timeout=70)

datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

UNKNOWN = "unknown"
ON_SCHEDULE = "on schedule"
CHECKIN_OPEN = "check-in-open"

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

        GATE_OPEN:BOARDING,
        CHECKIN_OPEN:CHECKIN,
        GATE_CLOSED:OUTGATE,
        ON_SCHEDULE: SCHEDULED,
        ARRIVED:LANDED
    }.get(status, UNKNOWN)

def getFullDate(hourMinute, scheduleDateTime):
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    correctDate = nowTime

    h = int(hourMinute[:2])
    m = int(hourMinute[3:])

    notFormatedTime = correctDate.replace(day=scheduleDateTime.day, month=scheduleDateTime.month, hour=h, minute=m, second=0)

    if scheduleDateTime.hour > 20 and h < 5:
        notFormatedTime = notFormatedTime + timedelta(days=1)
    elif scheduleDateTime.hour < 5 and h > 20:
        notFormatedTime = notFormatedTime - timedelta(days=1)

    formatedTime = notFormatedTime.strftime(datePattern)
    return formatedTime

def getFormatedCheckinDesks(checkinStr):
    idxOfParenthisis = checkinStr.find("(")
    if idxOfParenthisis > 0:
        checkinStr = checkinStr[:idxOfParenthisis - 1]
    if checkinStr.find(",") > 0:
        arDesks = checkinStr.split(",")
        return arDesks[0] + " - " + arDesks[len(arDesks) - 1]
    else:
        return checkinStr

codeSharesToFlightNo = {}

def getDataFromDocumentKUF(el, isArrival=False):
    scheduled = ""
    flightno = ""
    status = ""
    actual = ""
    estimated = ""
    rawStatus = ""
    codeShares = []
    gate = ""
    check_in_desks = ""

    try:
        flightno = str(el.select('.//@rf_eng').text()) + "-" + str(el.select('.//@flt').text())
    except:
        flightno = ""

    try:
        rawScheduled = str(el.select('.//@dp_eng').text()) + " " + str(nowTime.year)
        rawDateTime = datetime.strptime(rawScheduled, '%d %b %H:%M %Y')

        scheduled = rawDateTime.strftime(datePattern)

    except:
        scheduled = ""

    try:
        codeSharesString = str(el.select('.//@sovm_eng').text())

        if len(codeSharesString) > 0:
            indexWith = codeSharesString.find("with")
            codeShare = str(codeSharesString[indexWith + 5:])
            key = str(flightno) + ":" + str(rawDateTime.day)
            codeSharesToFlightNo[key] = {}
            codeSharesToFlightNo[key]["flight"] = codeShare
            codeSharesToFlightNo[key]["date"] = rawDateTime.day
            codeSharesToFlightNo[key]["is_arrival"] = isArrival
            return -1
    except:
        pass

    try:
        rawStatus = str(el.select('.//@statuzz_eng').text())
        rawStatus = str.lower(rawStatus)
        if rawStatus.find("delayed") >= 0:
            status = DELAYED
        if status == "" and len(rawStatus) > 0:
            status = fixStatus(rawStatus)
    except:
        rawStatus = ""
        status = ""

    if status == "":
        status = SCHEDULED

    try:
        if status == DEPARTED or status == LANDED:
            rawActual = str(el.select('.//@dr_eng').text())
            actual = getFullDate(rawActual, rawDateTime)
        elif status == DELAYED:
            rawEstimated = str(el.select('.//@dr_eng').text()) + " " + str(rawDateTime.year)
            estimatedDateTime = datetime.strptime(rawEstimated, "%d %b %H:%M %Y")
            estimated = estimatedDateTime.strftime(datePattern)
        else:
            rawEstimated = str(el.select('.//@dr_eng').text())
            estimated = getFullDate(rawEstimated, rawDateTime)
    except:
        estimated = ""
        actual = ""

    if not isArrival:
        try:
            gateString = el.select('.//@gate_eng').text()
            if gateString != "(Gate changed)":
                if gateString.find(" ") > 0:
                    gateString = gateString[:gateString.find(" ")]
                gate = gateString
        except:
            gate = ""

        try:
            rawCheckinDesks = str(el.select('.//@checkins_eng').text())
            if rawCheckinDesks != "(Check-in counters changed)":
                check_in_desks = getFormatedCheckinDesks(rawCheckinDesks)
        except:
            check_in_desks = ""

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
    if len(codeShares) > 0:
        result["codeshares"] = codeShares
    if check_in_desks != "":
        result["check_in_desks"] = check_in_desks
    if gate != "":
        result["gate"] = gate
    return result

#urlROVArrive = "http://www.rnd-airport.ru/1linetablo.ajax.5.19.php?arrive24h"
#status_eng

# ARRIVE
urlROVArrive = "http://airport.samara.ru/1linetablo.ajax.5.19.php?arrive"
todayArrivalsParams = {
    "arrive": "",
    "lang":"en",
    "rip": "93.185.27.173",
    "uag": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"
}

resp = g.go(urlROVArrive, post=todayArrivalsParams)

for el in g.doc.select("//online_arrive/flight"):
    arrival = getDataFromDocumentKUF(el, True)
    if arrival != -1:
        arrivals.append(arrival)


# DEPART
#urlROVDepart = "http://www.rnd-airport.ru/1linetablo.ajax.5.19.php?depart24h"
urlKUFDepart = "http://airport.samara.ru/1linetablo.ajax.5.19.php?depart"

todayDepartedParams = {
    "depart": "",
    "lang":"en",
    "rip": "63.182.12.84",
    "uag": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36"

}

resp = g.go(urlKUFDepart, post=todayDepartedParams)

for el in g.doc.select("//online_depart/flight"):
    departure = getDataFromDocumentKUF(el)
    if departure != -1:
        departures.append(departure)


for codeShare in codeSharesToFlightNo:
    flightNo = codeSharesToFlightNo[codeShare]["flight"]

    for j in range(0, len(arrivals) - 1):
        if arrivals[j]["flightno"] == flightNo:
            dateTime = datetime.strptime(arrivals[j]["scheduled"], datePattern)
            if dateTime.day == codeSharesToFlightNo[codeShare]["date"] and codeSharesToFlightNo[codeShare]["is_arrival"]:
                if not arrivals[j].has_key("codeshares"):
                    arrivals[j]["codeshares"] = []
                arrivals[j]["codeshares"].append(codeShare[:codeShare.find(":")])
                break
    for j in range(0, len(departures) - 1):
        if departures[j]["flightno"] == flightNo:
            dateTime = datetime.strptime(departures[j]["scheduled"], datePattern)
            if dateTime.day == codeSharesToFlightNo[codeShare]["date"] and (not codeSharesToFlightNo[codeShare][
                "is_arrival"]):
                if not departures[j].has_key("codeshares"):
                    departures[j]["codeshares"] = []
                departures[j]["codeshares"].append(codeShare[:codeShare.find(":")])
                break


resultKUF = {}
resultKUF["airport_id"] = "KUF"
resultKUF["departures"] = departures
resultKUF["arrivals"] = arrivals
jsonResult = json.dumps(resultKUF)
#print jsonResult