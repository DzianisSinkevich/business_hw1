import pandas as pd
import matplotlib.pyplot as plt
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import os

import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Обработчик файла
file_handler = logging.FileHandler('./logs/plot_log.txt')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Обработчик потоковой передачи
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

PNG_FILE_PATH = './logs/error_distribution.png'
CSV_FILE_PATH = "./logs/metric_log.csv"


class CSVEventHandler(FileSystemEventHandler):
    def __init__(self, csv_file):
        self.csv_file = csv_file

    def on_modified(self, event):
        if event.src_path == self.csv_file:
            logger.info(f"Получена новая пара данных. Изменение гистрограммы.")
            self.drawing()

    def drawing(self):
        df = pd.read_csv(self.csv_file)

        plt.figure(figsize=(12, 7))
        plt.hist(df['absolute_error'], bins=24, color='red', edgecolor="black",alpha=0.6)
        plt.title('Гистограмма абсолютных ошибок')
        plt.xlabel('Размер ошибки')
        plt.ylabel('Частота ошибки')
        plt.grid(axis='y', alpha=0.75)

        plt.savefig(PNG_FILE_PATH)
        plt.close()
        logger.info(f"Обновленая гистограмма сохранена в {PNG_FILE_PATH}")

def csv_reader(csv_file):
    event_handler = CSVEventHandler(csv_file)
    observer = Observer()
    observer.schedule(event_handler, path=os.path.dirname(CSV_FILE_PATH), recursive=False)
    observer.start()
    logger.info(f"Ожидание изменений в {CSV_FILE_PATH}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

logger.info("Микросервис plot запущен")
while True:
    logger.info("Plotter перезапущен")
    try:
        time.sleep(10)
        csv_file_path = CSV_FILE_PATH
        csv_reader(csv_file_path)
    except Exception as e:
        logger.error("Ошибка отрисовки {e}")