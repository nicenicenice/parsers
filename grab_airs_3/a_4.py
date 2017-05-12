from grab import Grab
import json
from datetime import datetime, timedelta

#12:50

datePattern = "%Y-%m-%d %H:%M:%S"
nowTime = datetime.now()
departures = []
arrivals = []

UNKNOWN = "unknown"

CHECKIN_CLOSE = "check-in-close"
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

        CHECKIN_CLOSE:BOARDING,
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
        flightno = el.select('.//@rf_eng').text() + "-" + el.select('.//@flt').text()
        flightno = flightno.encode("utf-8")
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

g = Grab(connect_timeout=90, timeout=00)

url = "http://www.koltsovo.ru/en/passazhiram"
resp = g.go(url)

"""g.setup(headers={
    'Content-Type': 'application/x-www-form-urlencoded; charset=windows-1251',
    "Cookie":"_ym_uid=1493567582118947836; __utmt=1; _ym_isad=1; _dc_gtm_UA-8807610-17=1; _ga=GA1.2.43996284.1493567581; _gid=GA1.2.1829132119.1493812595; _ym_visorc_28119129=w; __utma=158817440.43996284.1493567581.1493674827.1493812580.3; __utmb=158817440.5.10.1493812580; __utmc=158817440; __utmz=158817440.1493567581.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); rbsbbx=2; s=e80475f6cdd75e578eabd5fa75841027"
})"""

#g.setup(cookies={'s': 'e80475f6cdd75e578eabd5fa75841027'})

urlSVXArrive = "http://www.koltsovo.ru/1linetablo.ajax.5.19.php?arrive"
todayArrivalsParams = {
    "arrive":"",
    "rip": "93.185.27.173",
    "uag": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "lang":"en",
}

resp = g.go(urlSVXArrive, post=todayArrivalsParams)

for el in g.doc.select("//online_arrive/flight"):
    arrival = getDataFromDocumentKUF(el, True)
    if arrival != -1:
        arrivals.append(arrival)

# DEPART

urlSVXDepart = "http://www.koltsovo.ru/1linetablo.ajax.5.19.php?depart"
#g = Grab(connect_timeout=90, timeout=90)
#g.setup(cookies={'s': 'e80475f6cdd75e578eabd5fa75841027'})

"""g.setup(headers={
    'Content-Type': 'application/x-www-form-urlencoded; charset=windows-1251',
    "Cookie":"_ym_uid=1493567582118947836; __utmt=1; _ym_isad=1; _dc_gtm_UA-8807610-17=1; _ga=GA1.2.43996284.1493567581; _gid=GA1.2.1829132119.1493812595; _ym_visorc_28119129=w; __utma=158817440.43996284.1493567581.1493674827.1493812580.3; __utmb=158817440.5.10.1493812580; __utmc=158817440; __utmz=158817440.1493567581.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); rbsbbx=2; s=e80475f6cdd75e578eabd5fa75841027"
})"""

todayDepartedParams = {
    "depart":"",
    "rip": "93.185.27.173",
    "uag": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
    "lang":"en",
}

resp = g.go(urlSVXDepart, post=todayDepartedParams)

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


resultSVX = {}
resultSVX["airport_id"] = "SVX"
resultSVX["departures"] = departures
resultSVX["arrivals"] = arrivals
jsonResult = json.dumps(resultSVX)
#print jsonResult