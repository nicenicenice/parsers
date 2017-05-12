from Spider10 import *

#logging.basicConfig(level=logging.DEBUG)
bot = ExampleSpider(
    thread_number=4,
    network_try_limit = 3
)
bot.run()

resultPER = {}
resultPER["airport_id"] = "PER"
resultPER["departures"] = bot.departures
resultPER["arrivals"] = bot.arrivals

jsonResult = json.dumps(resultPER)
print jsonResult