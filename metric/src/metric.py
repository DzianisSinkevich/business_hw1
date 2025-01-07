import pika
import json
import time

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

table_header= 'id,y_true,y_pred,absolute_error'

try:
    answer_string ="log file started"
    with open('./logs/labels_log.txt', 'a') as log:
        log.write(answer_string +'\n')
    with open('./logs/metric_log.csv', 'w') as log:
        log.write(table_header +'\n')
except Exception as e:
    logger.error(f"Ошибка создания лог файла: {e}")

true_dicts = []
pred_dicts = []

def pair_found(true_dict, pred_dict):
    if true_dict['id'] != pred_dict['id']:
        return
    if true_dicts.__contains__(true_dict):
        true_dicts.remove(true_dict)
    if pred_dicts.__contains__(pred_dict):
        pred_dicts.remove(pred_dict)
    print(f"pair found {true_dict['id']}")

    id = true_dict['id']
    y_true = true_dict['body']
    y_pred = pred_dict['body']
    absolute_error = abs(y_true - y_pred)
    with open('./logs/metric_log.csv', 'a') as log:
        log.write(f'{id},{y_true},{y_pred},{absolute_error}\n')

logger.info("Микросервис metric запущен")
while True:
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='y_true')
        channel.queue_declare(queue='y_pred')

        def callback_true_dict(ch, method, properties, body):
            true_dict = json.loads(body)
            id = true_dict['id']
            body = true_dict['body']
            print(f'true id:{ id },   true body:{body }')

            for pred_dict in pred_dicts:
                if pred_dict['id'] == id:
                    pair_found(true_dict, pred_dict)
                    return
            true_dicts.append(true_dict)

        def callback_pred_dict(ch, method, properties, body):
            pred_dict = json.loads(body)
            id = pred_dict['id']
            body = pred_dict['body']
            print(f'pred id:{ id },   pred body:{body }')

            for true_dict in true_dicts:
                if true_dict['id'] == id:
                    pair_found(true_dict, pred_dict)
                    return
            pred_dicts.append(pred_dict)

        channel.basic_consume(
            queue='y_true',
            on_message_callback=callback_true_dict,
            auto_ack=True
        )
        channel.basic_consume(
            queue='y_pred',
            on_message_callback=callback_pred_dict,
            auto_ack=True
        )

        channel.start_consuming()
    except Exception as e:
        time.sleep(10)
        logger.error(f"Ошибка подключения к очереди {e}")