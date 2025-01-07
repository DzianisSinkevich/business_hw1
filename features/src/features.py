import pika
import numpy as np
import json
import time
from datetime import datetime
from sklearn.datasets import load_diabetes

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Обработчик файла
file_handler = logging.FileHandler('./logs/full_log.txt')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Обработчик потоковой передачи
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

logger.info("Микросервис features запущен")

while True:
    try:
        X, y = load_diabetes(return_X_y=True)
        random_row = np.random.randint(0, X.shape[0]-1)

        connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='y_true')
        channel.queue_declare(queue='features')

        message_id = datetime.timestamp(datetime.now())
        message_y_true = {
            'id': message_id,
            'body': y[random_row]
        }

        message_features = {
            'id': message_id,
            'body': list(X[random_row])
        }

        channel.basic_publish(exchange='',
                            routing_key='y_true',
                            body=json.dumps(message_y_true))
        logger.info('Сообщение с вектором признаков отправлено в очередь')

        channel.basic_publish(exchange='',
                            routing_key='features',
                            body=json.dumps(message_features))
        logger.info('Сообщение с вектором признаков отправлено в очередь')

        connection.close()

        time.sleep(10)
    except Exception as e:
        time.sleep(10)
        logger.error(f"Ошибка подключения к очереди {e}")