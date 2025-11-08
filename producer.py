import time, json, random
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode()
)

sensor_ids = ['roadA','roadB','roadC']

while True:
  data = {
    'sensor': random.choice(sensor_ids),
    'speed': random.randint(10, 60),
    'timestamp': int(time.time())
  }
  print("Sending", data)
  producer.send('traffic', data)
  time.sleep(2)  # every 2 seconds
