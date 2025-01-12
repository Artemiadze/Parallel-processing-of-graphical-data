import threading
import queue
import cv2
import os


def invert_colors(image):
    """Инвертирование цветов изображения."""
    return cv2.bitwise_not(image)


def producer_task(file_queue, image_queue):
    """Загружает изображения и кладет их в очередь."""
    while True:
        file_path = file_queue.get()
        if file_path is None:
            break  # Сигнал завершения
        image = cv2.imread(file_path)
        if image is not None:
            image_queue.put((file_path, image))
        file_queue.task_done()


def consumer_task(image_queue, result_queue):
    """Обрабатывает изображения (инвертирует цвета)."""
    while True:
        item = image_queue.get()
        if item is None:
            break  # Сигнал завершения
        file_path, image = item
        processed_image = invert_colors(image)
        result_queue.put((file_path, processed_image))
        image_queue.task_done()


def writer_task(result_queue, output_dir):
    """Сохраняет обработанные изображения."""
    while True:
        item = result_queue.get()
        if item is None:
            break  # Сигнал завершения
        file_path, image = item
        output_path = os.path.join(output_dir, os.path.basename(file_path))
        cv2.imwrite(output_path, image)
        result_queue.task_done()


def main(input_dir, output_dir, num_consumers=4):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    file_queue = queue.Queue()
    image_queue = queue.Queue()
    result_queue = queue.Queue()

    # Создаем и запускаем Producer
    producer = threading.Thread(target=producer_task, args=(file_queue, image_queue))
    producer.start()

    # Запускаем Consumer-потоки
    consumers = []
    for _ in range(num_consumers):
        consumer = threading.Thread(target=consumer_task, args=(image_queue, result_queue))
        consumer.start()
        consumers.append(consumer)

    # Запускаем Writer-поток
    writer = threading.Thread(target=writer_task, args=(result_queue, output_dir))
    writer.start()

    # Заполняем очередь файлами изображений
    for file_name in os.listdir(input_dir):
        file_path = os.path.join(input_dir, file_name)
        file_queue.put(file_path)

    # Останавливаем Producer
    file_queue.put(None)
    producer.join()

    # Останавливаем Consumers
    for _ in consumers:
        image_queue.put(None)
    for consumer in consumers:
        consumer.join()

    # Останавливаем Writer
    result_queue.put(None)
    writer.join()

    print("Обработка завершена!")


# Пример использования
if __name__ == "__main__":
    main("original", "new")