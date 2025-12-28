import time, json, random
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode()
)
#List of simulated sensors
sensor_ids = ['roadA','roadB','roadC']

while True:
  data = {
    'sensor': random.choice(sensor_ids), #Choose a random sensor from the list of simulated sensors
    'speed': random.randint(10, 60), #Generate a random speed between 10 and 60km/h
    'timestamp': int(time.time())
  }
  print("Sending", data)
  producer.send('traffic', data)
  time.sleep(2) #Generate the event after every 2 seconds
