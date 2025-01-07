import pika
import pickle
import numpy as np
import json

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

logger.info("Микросервис model запущен")

with open('myfile.pkl', 'rb') as pkl_file:
    regressor = pickle.load(pkl_file)

while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='features')
        channel.queue_declare(queue='y_pred')

        def callback(ch, method, properties, body):
            logger.info(f'Получены признаки: {body}')
            features_set = json.loads(body)
            message_id = features_set['id']
            features = features_set['body']

            pred = regressor.predict(np.array(features).reshape(1, -1))

            message_y_pred = {
            'id': message_id,
            'body': pred[0]
            }

            channel.basic_publish(exchange='',
                            routing_key='y_pred',
                            body=json.dumps(message_y_pred))
            logger.info(f'Предсказание {pred[0]} направлено в очередь')

        channel.basic_consume(
            queue='features',
            on_message_callback=callback,
            auto_ack=True
        )

        channel.start_consuming()
    except Exception as e:
        logger.error(f"Ошибка подключения к очереди: {e}")