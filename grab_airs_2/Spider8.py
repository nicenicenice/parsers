# coding: utf-8

from grab import Grab
import json
from datetime import datetime, timedelta
import logging
import time
import re
#import pytz
import warnings
warnings.filterwarnings('ignore')

from grab.spider import Spider, Task

class ExampleSpider(Spider):
    g = Grab(connect_timeout=90, timeout=90)

    COUNTER = 0

    arrivals = []
    departures = []
    BOARDING_SOON = "boarding soon"
    FLIGHT_CLOSED = "flight closed"
    CHECKIN_OPEN = "check-in open"
    CHECKIN_CLOSE = "check-in close"
    CONFIRMED = "confirmed"
    EARLY = "early"
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

    siteDateTime = ""
    datePattern = "%Y-%m-%d %H:%M:%S"
    nowTime = datetime.now()
    departures = []
    arrivals = []


    def fixStatus(self, status):
        return {
            self.SCHEDULED: self.SCHEDULED,
            self.DELAYED: self.DELAYED,
            self.CANCELLED: self.CANCELLED,
            self.CHECKIN: self.CHECKIN,
            self.BOARDING: self.BOARDING,
            self.OUTGATE: self.OUTGATE,
            self.DEPARTED: self.DEPARTED,
            self.EXPECTED: self.EXPECTED,
            self.LANDED: self.LANDED,
            self.FLIGHT_CLOSED:self.BOARDING,
            self.BOARDING_SOON:self.CHECKIN,
            self.EARLY: self.SCHEDULED,
            self.CONFIRMED: self.SCHEDULED,
            self.CHECKIN_CLOSE: self.BOARDING,
            self.CHECKIN_OPEN: self.CHECKIN,
            self.CHECK_IN: self.CHECKIN,
            self.ESTIMSTED: self.EXPECTED,
            self.AIRBORNE: self.DEPARTED,
            self.CANCELED: self.CANCELLED,
            self.BOARDING_CLOSED: self.OUTGATE,
            self.ON_TIME: self.SCHEDULED,
            self.GATE_CLOSED: self.OUTGATE,
            self.FINAL_CALL: self.BOARDING,
            self.GATE_OPEN: self.BOARDING,
            self.ARRIVED: self.LANDED,
            self.LATE: self.DELAYED,
            "":self.SCHEDULED
        }.get(status, self.UNKNOWN)

    def getFullDate(self, timeString):

        datePattern = "%Y-%m-%d %H:%M:%S"
        correctDate = self.siteDateTime

        # 8:15am, Today
        day = str.lower(timeString[timeString.find(",") + 2:]).strip()
        actualString = str(timeString[:timeString.find(",")]).strip()
        actualDateTime = datetime.strptime(actualString, "%I:%M%p")

        h = actualDateTime.hour
        m = actualDateTime.minute

        notFormatedTime = correctDate.replace(hour=h, minute=m, second=0)

        if day == "tomorrow":
            notFormatedTime = notFormatedTime + timedelta(days=1)
        elif day == "yesterday":
            notFormatedTime = notFormatedTime - timedelta(days=1)

        formatedTime = notFormatedTime.strftime(datePattern)
        return formatedTime

    def getTimeStampFromDateTime(self, datetime):
        return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

    def task_generator(self):

        """
        carrier:
        date_from:11 May 2017 1:00am
        date_to:13 May 2017 1:12am
        advanced:1
        search:
        leg:A
        range:I
        _:1494517017829
        
        """
        nowTime = datetime.now()
        fourHoursAgoDateTime = nowTime - timedelta(hours=4)
        tomorrowDateTime = nowTime + timedelta(days=1)

        #timeStampFrom = str(self.getTimeStampFromDateTime(fourHoursAgoDateTime))
        #timeStampTo = str(self.getTimeStampFromDateTime(tomorrowDateTime))
        #currentTimeStamp = str(self.getTimeStampFromDateTime(nowTime))

        """
        pytz.timezone("Australia/Brisbane")
        nowTimeOfMyPlace= datetime.now()
        print str(self.getTimeStampFromDateTime(nowTimeOfMyPlace))
        nowTimeOfAeroport = datetime.now(pytz.timezone("Australia/Brisbane"))
        nowTimeOfAeroport - timedelta()
        #11 May 2017 1:00am
        #http://www.bne.com.au/sites/all/custom/flight/?carrier=&date_from=11+May+2017+1%3A00am&date_to=13+May+2017+1%3A12am&advanced=1&search=&advanced=1&leg=A
        nowTime = nowTimeOfAeroport.replace(day=nowTimeOfMyPlace.day, month=nowTimeOfMyPlace.month, year=nowTimeOfMyPlace.year, hour=nowTimeOfMyPlace.hour, minute=nowTimeOfMyPlace.minute)
        print str(self.getTimeStampFromDateTime(nowTime))
        
        """
        dateFrom = fourHoursAgoDateTime.strftime("%d %b %Y %I:%M%p")
        dateTo = tomorrowDateTime.strftime("%d %b %Y %I:%M%p")

        urlArrDomestic = "http://www.bne.com.au/sites/all/custom/flight/?range=D&leg=A&date_from=" + \
                         dateFrom + "&date_to=" \
                         + dateTo

        urlDepDomestic = "http://www.bne.com.au/sites/all/custom/flight/?range=D&leg=D&date_from=" + \
                         dateFrom + "&date_to=" \
                         + dateTo
        urlArrInter = "http://www.bne.com.au/sites/all/custom/flight/?range=I&leg=A&date_from=" + \
                      dateFrom + "&date_to=" \
                      + dateTo
        urlDepInter = "http://www.bne.com.au/sites/all/custom/flight/?range=I&leg=D&date_from=" + \
                      dateFrom + "&date_to=" \
                      + dateTo

        g = Grab(connect_timeout=90, timeout=90)

        # ARRIVAL DOMESTIC
        resp = g.go(urlArrDomestic)

        try:
            airDate = str(g.doc.select('//*[@id="flight-header"]/div[1]/div[3]/span[2]/text()').text()).strip()
            numsWithStr = airDate[:airDate.find(" ")]
            day = re.findall('\d+', numsWithStr)[0]
            dateSting = str(day) + airDate[airDate.find(" "):]
            dateTimeFromSiteSide = datetime.strptime(dateSting, "%d %b %Y")
        except:
            pass

        pre_arrivals1 = []

        dayString = g.doc.select('//*[@id="flight-header"]/div[1]/div[3]/span[2]/text()').text()
        if dayString.find(" ") >= 0:
            dayString = filter(str.isdigit, dayString[:dayString.find(" ")]) + " " + dayString[dayString.find(" ") + 1:]
            self.siteDateTime = datetime.strptime(dayString, "%d %b %Y")

        for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
            scheduled = ""
            try:
                scheduledTime = el.select('./div[6]').text()
                scheduleFirstPart = str(scheduledTime[:scheduledTime.find(","):]).strip()
                scheduleDayInWord = str.lower(scheduledTime[scheduledTime.find(",") + 1:]).strip()
                if scheduleDayInWord == "today":
                    scheduleDayMonth = dateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "yesterday":
                    yestDateTimeFromSiteSide = dateTimeFromSiteSide - timedelta(days=1)
                    scheduleDayMonth = yestDateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "tomorrow":
                    tomorDateTimeFromSiteSide = dateTimeFromSiteSide + timedelta(days=1)
                    scheduleDayMonth = tomorDateTimeFromSiteSide.strftime("%d %m %Y")
                scheduleString = scheduleDayMonth + " " + scheduleFirstPart
                scheduledDateTime = datetime.strptime(scheduleString, "%d %m %Y %I:%M%p")
                scheduled = scheduledDateTime.strftime(self.datePattern)
            except:
                pass

            flightno = el.select('.//@data-flight-number').text()
            dateFlight = el.select('.//@data-date').text()
            groupId = el.select('.//@data-row-id').text()
            urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

            lastIdx = len(pre_arrivals1) - 1
            if lastIdx >= 0:
                if groupId == pre_arrivals1[lastIdx]["groupId"]:
                    if not pre_arrivals1[lastIdx].has_key("codeshares"):
                        pre_arrivals1[lastIdx]["codeshares"] = []
                    pre_arrivals1[lastIdx]["codeshares"].append(flightno)
                    continue
            flight = {
                "flightno": flightno,
                "dateFlight": dateFlight,
                "urlOfFlight": urlOfFlight,
                "groupId": groupId,
                "is_departure": False,
                "scheduled" : scheduled
            }
            pre_arrivals1.append(flight)

        # ARRIVAL INTERNATIONAL
        resp = g.go(urlArrInter)
        pre_arrivals2 = []

        for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
            scheduled = ""
            try:
                scheduledTime = el.select('./div[6]').text()
                scheduleFirstPart = str(scheduledTime[:scheduledTime.find(","):]).strip()
                scheduleDayInWord = str.lower(scheduledTime[scheduledTime.find(",") + 1:]).strip()
                if scheduleDayInWord == "today":
                    scheduleDayMonth = dateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "yesterday":
                    yestDateTimeFromSiteSide = dateTimeFromSiteSide - timedelta(days=1)
                    scheduleDayMonth = yestDateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "tomorrow":
                    tomorDateTimeFromSiteSide = dateTimeFromSiteSide + timedelta(days=1)
                    scheduleDayMonth = tomorDateTimeFromSiteSide.strftime("%d %m %Y")
                scheduleString = scheduleDayMonth + " " + scheduleFirstPart
                scheduledDateTime = datetime.strptime(scheduleString, "%d %m %Y %I:%M%p")
                scheduled = scheduledDateTime.strftime(self.datePattern)
            except:
                pass

            flightno = el.select('.//@data-flight-number').text()
            dateFlight = el.select('.//@data-date').text()
            groupId = el.select('.//@data-row-id').text()
            urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

            lastIdx = len(pre_arrivals2) - 1
            if lastIdx >= 0:
                if groupId == pre_arrivals2[lastIdx]["groupId"]:
                    if not pre_arrivals2[lastIdx].has_key("codeshares"):
                        pre_arrivals2[lastIdx]["codeshares"] = []
                    pre_arrivals2[lastIdx]["codeshares"].append(flightno)
                    continue
            flight = {
                "flightno": flightno,
                "dateFlight": dateFlight,
                "urlOfFlight": urlOfFlight,
                "groupId": groupId,
                "is_departure": False,
                "scheduled" : scheduled
            }
            pre_arrivals2.append(flight)

        pre_arrivals = pre_arrivals1 + pre_arrivals2

        # DEPARTURE DOMESTIC
        resp = g.go(urlDepDomestic)
        pre_departures1 = []

        for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
            scheduled = ""
            try:
                scheduledTime = el.select('./div[6]').text()
                scheduleFirstPart = str(scheduledTime[:scheduledTime.find(","):]).strip()
                scheduleDayInWord = str.lower(scheduledTime[scheduledTime.find(",") + 1:]).strip()
                if scheduleDayInWord == "today":
                    scheduleDayMonth = dateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "yesterday":
                    yestDateTimeFromSiteSide = dateTimeFromSiteSide - timedelta(days=1)
                    scheduleDayMonth = yestDateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "tomorrow":
                    tomorDateTimeFromSiteSide = dateTimeFromSiteSide + timedelta(days=1)
                    scheduleDayMonth = tomorDateTimeFromSiteSide.strftime("%d %m %Y")
                scheduleString = scheduleDayMonth + " " + scheduleFirstPart
                scheduledDateTime = datetime.strptime(scheduleString, "%d %m %Y %I:%M%p")
                scheduled = scheduledDateTime.strftime(self.datePattern)
            except:
                pass

            flightno = el.select('.//@data-flight-number').text()
            dateFlight = el.select('.//@data-date').text()
            groupId = el.select('.//@data-row-id').text()
            urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

            lastIdx = len(pre_departures1) - 1
            if lastIdx >= 0:
                if groupId == pre_departures1[lastIdx]["groupId"]:
                    if not pre_departures1[lastIdx].has_key("codeshares"):
                        pre_departures1[lastIdx]["codeshares"] = []
                    pre_departures1[lastIdx]["codeshares"].append(flightno)
                    continue
            flight = {
                "flightno": flightno,
                "dateFlight": dateFlight,
                "urlOfFlight": urlOfFlight,
                "groupId": groupId,
                "is_departure": True,
                "scheduled" : scheduled
            }
            pre_departures1.append(flight)

        # DEPARTURE INTERNATIONAL
        resp = g.go(urlDepInter)
        pre_departures2 = []

        for el in g.doc.select('//*[@id="flight-table"]/div[2]/div'):
            scheduled = ""
            try:
                scheduledTime = el.select('./div[6]').text()
                scheduleFirstPart = str(scheduledTime[:scheduledTime.find(","):]).strip()
                scheduleDayInWord = str.lower(scheduledTime[scheduledTime.find(",") + 1:]).strip()
                if scheduleDayInWord == "today":
                    scheduleDayMonth = dateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "yesterday":
                    yestDateTimeFromSiteSide = dateTimeFromSiteSide - timedelta(days=1)
                    scheduleDayMonth = yestDateTimeFromSiteSide.strftime("%d %m %Y")
                elif scheduleDayInWord == "tomorrow":
                    tomorDateTimeFromSiteSide = dateTimeFromSiteSide + timedelta(days=1)
                    scheduleDayMonth = tomorDateTimeFromSiteSide.strftime("%d %m %Y")
                scheduleString = scheduleDayMonth + " " + scheduleFirstPart
                scheduledDateTime = datetime.strptime(scheduleString, "%d %m %Y %I:%M%p")
                scheduled = scheduledDateTime.strftime(self.datePattern)
            except:
                pass

            flightno = el.select('.//@data-flight-number').text()
            dateFlight = el.select('.//@data-date').text()
            groupId = el.select('.//@data-row-id').text()
            urlOfFlight = "http://www.bne.com.au/sites/all/custom/flight/single.php?display=ajax&flight_number=" + flightno + "&date=" + dateFlight

            lastIdx = len(pre_departures2) - 1
            if lastIdx >= 0:
                if groupId == pre_departures2[lastIdx]["groupId"]:
                    if not pre_departures2[lastIdx].has_key("codeshares"):
                        pre_departures2[lastIdx]["codeshares"] = []
                    pre_departures2[lastIdx]["codeshares"].append(flightno)
                    continue
            flight = {
                "flightno": flightno,
                "dateFlight": dateFlight,
                "urlOfFlight": urlOfFlight,
                "groupId": groupId,
                "is_departure" : True,
                "scheduled" : scheduled
            }
            pre_departures2.append(flight)

        pre_departures = pre_departures1 + pre_departures2

        preFlights = pre_arrivals + pre_departures
        #arrivals = arrivals + getDetailFlightInfoByPreview(pre_arrivals)
        #departures = departures + getDetailFlightInfoByPreview(pre_departures)

        i = 0
        for pre_flight in preFlights:
            i += 1
            g = Grab(connect_timeout=29, timeout=30, url=pre_flight['urlOfFlight'])
            yield Task('handle', grab=g, pre_flight=pre_flight, number=i)

    def task_handle(self, grab, task):

        preview = task.pre_flight

        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        luggage = ""
        codeshares = ""
        rawStatus = ""
        gate = ""

        try:
            rawStatus = grab.doc.select('//div/div[1]/div[3]').text()
            rawStatus = str.lower(rawStatus)

            if preview['is_departure'] and rawStatus == self.ARRIVED:
                status = self.DEPARTED
            if status == "":
                status = self.fixStatus(rawStatus)
        except:
            rawStatus = ""
            status = ""

        if status == "":
            status = self.SCHEDULED

        try:
            scheduledString = grab.doc.select('//div/div[2]/div[1]').text()
            if scheduledString.find(" ") >= 0:
                scheduledString = str(scheduledString[scheduledString.find(" ") + 1:]).strip()
                scheduledDateTime = datetime.strptime(scheduledString, "%I:%M%p, %d %b %Y")
                scheduled = scheduledDateTime.strftime(self.datePattern)
        except:
            scheduled = preview["scheduled"]

        try:
            gate = grab.doc.select('//div/div[2]/div[4]/div/following-sibling::text()[1]').text()
            if gate.find(" ") >= 0:
                gate = ""
        except:
            gate = ""

        try:
            luggage = grab.doc.select('//div/div[2]/div[5]/div/following-sibling::text()[1]').text()
            if luggage.find(" ") >= 0:
                luggage = ""
        except:
            luggage = ""

        try:
            actualString = str(grab.doc.select('//div/div[1]/div[4]').text())
            actual = self.getFullDate(actualString)
        except:
            actual = ""

        result = {
            "flightno": preview["flightno"],
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }
        if preview.has_key("codeshares") and len(preview["codeshares"]) > 0:
            result["codeshares"] = preview["codeshares"]
        if luggage != "":
            result["luggage"] = luggage
        if actual != "":
            result["actual"] = actual
        if gate != "":
            result["gate"] = gate

        if preview['is_departure']:
            self.departures.append(result)
        else:
            self.arrivals.append(result)