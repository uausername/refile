# Установка библиотек (выполните в терминале):
# pip install transformers torch pillow

import os
import re
from PIL import Image
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration

# Функция для обработки текстовых файлов
def process_text_file(file_path, ner_model):
    """Извлекает ключевые сущности из текста для имени файла."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()[:1000]  # Обрезаем до 1000 символов
    entities = ner_model(text)
    unique_entities = set(entity['word'] for entity in entities)
    description = "_".join(unique_entities) if unique_entities else "text_file"
    return description

# Функция для обработки изображений
def process_image_file(file_path, processor, model):
    """Генерирует подпись к изображению."""
    image = Image.open(file_path).convert("RGB")
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    description = processor.decode(out[0], skip_special_tokens=True)
    return description

# Функция для очистки имени файла
def clean_filename(description):
    """Удаляет недопустимые символы и ограничивает длину."""
    description = re.sub(r'[\/:*?"<>|]', '_', description)  # Заменяем недопустимые символы
    description = description[:50]  # Ограничиваем до 50 символов
    return description.strip()

# Функция для переименования файла
def rename_file(file_path, description):
    """Переименовывает файл, добавляя суффикс при необходимости."""
    directory = os.path.dirname(file_path)
    extension = os.path.splitext(file_path)[1]
    new_name = clean_filename(description) + extension
    new_path = os.path.join(directory, new_name)
    
    # Обеспечиваем уникальность имени
    counter = 1
    while os.path.exists(new_path):
        new_name = clean_filename(description) + f"_{counter}" + extension
        new_path = os.path.join(directory, new_name)
        counter += 1
    
    os.rename(file_path, new_path)
    print(f"Переименован: {file_path} -> {new_path}")

# Основная функция для обработки директории
def process_directory(directory, ner_model, img_processor, img_model):
    """Обрабатывает все .txt и .jpg/.png файлы в директории."""
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                if file.lower().endswith('.txt'):
                    description = process_text_file(file_path, ner_model)
                    rename_file(file_path, description)
                elif file.lower().endswith(('.jpg', '.png')):
                    description = process_image_file(file_path, img_processor, img_model)
                    rename_file(file_path, description)
            except Exception as e:
                print(f"Ошибка при обработке {file_path}: {e}")

# Запуск программы
if __name__ == "__main__":
    print("Загрузка моделей...")
    ner_pipeline = pipeline("ner", model="dslim/bert-base-NER", aggregation_strategy="simple")
    blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    print("Модели загружены.")

    # Получаем путь к директории из переменной окружения DATA_DIR,
    # по умолчанию используем /data (путь внутри контейнера)
    directory = os.environ.get("DATA_DIR", "/data")

    # Проверка, существует ли директория
    if not os.path.isdir(directory):
        print(f"Ошибка: Директория '{directory}' не найдена.")
        # Можно добавить sys.exit(1) здесь, если нужно прервать выполнение
        import sys
        sys.exit(1)
    else:
        print(f"Начинаю обработку директории: {directory}")
        process_directory(directory, ner_pipeline, blip_processor, blip_model) # Передаем модели
        print("Обработка завершена.") 