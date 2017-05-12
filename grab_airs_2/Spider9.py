# coding: utf-8

from grab import Grab
import json
from datetime import datetime, timedelta
import logging
import time
import warnings
warnings.filterwarnings('ignore')

from grab.spider import Spider, Task

class ExampleSpider(Spider):
    g = Grab(connect_timeout=90, timeout=90)

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
            self.LATE: self.DELAYED
        }.get(status, self.UNKNOWN)

    def getFullDate(self, hourMinute, scheduleDateTime):
        datePattern = "%Y-%m-%d %H:%M:%S"
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

    def getTimeStampFromDateTime(datetime):
        return int(time.mktime(datetime.timetuple()) + datetime.microsecond / 1E6)

    def getDataFromDocumentMEL(self, el, isDeparted=False):
        scheduled = ""
        flightno = ""
        status = ""
        actual = ""
        estimated = ""
        rawStatus = ""
        terminal = ""
        gate = ""
        dayMonthDateTime = ""

        try:
            dayMonthOfFlight = el.select('.//td[1]').text()
            dayMonthDateTime = datetime.strptime(dayMonthOfFlight, "%d/%m")
        except:
            dayMonthDateTime = ""

        try:
            flightno = el.select('.//td[2]').text()
        except:
            flightno = ""

        try:
            rawStatus = el.select('.//td[8]/img/@alt').text()
            rawStatus = str.lower(rawStatus)
            if rawStatus != "":
                status = self.fixStatus(rawStatus)
        except:
            rawStatus = ""
            status = ""

        if status == "":
            status = self.SCHEDULED

        try:
            rawScheduled = str(el.select('.//td[4]').text())
            h = int(rawScheduled[:2])
            m = int(rawScheduled[3:])

            scheduledDateTime = self.nowTime
            scheduledDateTime = scheduledDateTime.replace(day=dayMonthDateTime.day, month=dayMonthDateTime.month, hour=h,
                                                minute=m, second=0)

            scheduled = scheduledDateTime.strftime(self.datePattern)
        except:
            scheduled = ""

        try:
            rawAddTime = str(el.select('.//td[5]').text())
            addTime = self.getFullDate(rawAddTime, scheduledDateTime)
            if status == self.LANDED or status == self.DEPARTED:
                actual = addTime
            elif status != self.CANCELLED:
                estimated = addTime
        except:
            estimated = ""
            actual = ""

        try:
            terminal = el.select('.//td[6]').text()
        except:
            terminal = ""

        if isDeparted:
            try:
                gate = el.select('.//td[7]').text()
            except:
                gate = ""

        result = {
            "flightno": flightno,
            "scheduled": scheduled,
            "status": status,
            "raw_status": rawStatus
        }
        if terminal != "":
            result["terminal"] = terminal
        if estimated != "":
            result["estimated"] = estimated
        if actual != "":
            result["actual"] = actual
        if gate != "":
            result["gate"] = gate
        return result

    def task_generator(self):
        IA = {
            "is_departure" : False,
            "url" : "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=IA&airline="
        }

        DA = {
            "is_departure": False,
            "url": "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=DA"
        }

        ID = {
            "is_departure": True,
            "url": "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=ID"
        }

        DD = {
            "is_departure": True,
            "url": "http://melbourneairport.com.au/flight-passenger-info/flight-information/current-flights.html?search=DD&airline="
        }

        urls = [IA, DA, ID, DD]

        i = 0
        for item in urls:
            i += 1
            g = Grab(connect_timeout=29, timeout=30, url=item["url"])
            yield Task('handle', grab=g, is_departure = item["is_departure"], num_task=i)

    def saveFlighhsFromPage(self, grab, is_departure):
        if not is_departure:
            i = 0
            for el in grab.doc.select('//*[@id="resultTable"]/tbody/tr'):
                i += 1
                if i == 1:
                    continue
                arrival = self.getDataFromDocumentMEL(el)
                if arrival['flightno'].find("(") >= 0:
                    codeshareToFlight = arrival['flightno'][arrival['flightno'].find("(") + 1: arrival['flightno'].find(")")].strip()
                    codeshare = arrival['flightno'][: arrival['flightno'].find("(")].strip()
                    lastIdxOfArrivals = len(self.arrivals) - 1
                    if lastIdxOfArrivals >= 0 and self.arrivals[lastIdxOfArrivals]["flightno"] == codeshareToFlight:
                        if not self.arrivals[lastIdxOfArrivals].has_key("codeshares"):
                            self.arrivals[lastIdxOfArrivals]["codeshares"] = []
                        self.arrivals[lastIdxOfArrivals]["codeshares"].append(codeshare)
                        continue
                self.arrivals.append(arrival)
        else:
            i = 0
            for el in grab.doc.select('//*[@id="resultTable"]/tbody/tr'):
                i += 1
                if i == 1:
                    continue
                departure = self.getDataFromDocumentMEL(el, True)
                if departure['flightno'].find("(") >= 0:
                    codeshareToFlight = departure['flightno'][departure['flightno'].find("(") + 1: departure['flightno'].find(")")].strip()
                    codeshare = departure['flightno'][: departure['flightno'].find("(")].strip()
                    lastIdxOfDepartures = len(self.departures) - 1
                    if lastIdxOfDepartures >= 0 and self.departures[lastIdxOfDepartures]["flightno"] == codeshareToFlight:
                        if not self.departures[lastIdxOfDepartures].has_key("codeshares"):
                            self.departures[lastIdxOfDepartures]["codeshares"] = []
                        self.departures[lastIdxOfDepartures]["codeshares"].append(codeshare)
                        continue
                self.departures.append(departure)


    def task_handle(self, grab, task):
        rootUrl = "http://melbourneairport.com.au"
        nextPageUrl = ""
        # get a current page
        self.saveFlighhsFromPage(grab, task.is_departure)

        for el in grab.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
            try:
                altText = el.select('./a/img/@alt').text()
                if altText == "Next Page":
                    nextPageUrl = rootUrl + el.select('./a/@href').text()
            except:
                pass
        # get the next pages
        isFoundNextPage = False
        if nextPageUrl != "":
            theEnd = False
            while not theEnd:
                try:
                    resp = self.g.go(nextPageUrl)
                    self.saveFlighhsFromPage(self.g, task.is_departure)
                    isFoundNextPage = False

                    for el in self.g.doc.select('//*[@id="AdvancedSearchResults"]/table[2]/tbody/tr[2]/td'):
                        try:
                            altText = el.select('./a/img/@alt').text()
                            if altText == "Next Page":
                                nextPageUrl = rootUrl + el.select('./a/@href').text()
                                isFoundNextPage = True
                        except:
                            pass
                    if not isFoundNextPage:
                        theEnd = True
                        break
                except:
                    theEnd = True
                    break