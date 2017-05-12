from Spider7 import *

#logging.basicConfig(level=logging.DEBUG)
bot = ExampleSpider(
    thread_number=4,
    network_try_limit = 3
)
bot.run()

resultBKK = {}
resultBKK["airport_id"] = "BKK"
resultBKK["departures"] = bot.departures
resultBKK["arrivals"] = bot.arrivals

jsonResult = json.dumps(resultBKK)
print jsonResult