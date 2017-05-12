from Spider9 import *

#logging.basicConfig(level=logging.DEBUG)
bot = ExampleSpider(
    thread_number=4,
    network_try_limit = 3
)
bot.run()

resultMEL = {}
resultMEL["airport_id"] = "MEL"
resultMEL["departures"] = bot.departures
resultMEL["arrivals"] = bot.arrivals

jsonResult = json.dumps(resultMEL)
print jsonResult