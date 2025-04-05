# Установка библиотек (выполните в терминале):
# pip install transformers torch pillow python-docx PyMuPDF

import os
import re
from PIL import Image
from transformers import pipeline, BlipProcessor, BlipForConditionalGeneration
import docx  # Для .docx файлов
import fitz  # PyMuPDF, для .pdf файлов
import sys   # Для sys.exit

# Функция для извлечения текста из DOCX
def extract_text_from_docx(file_path):
    """Извлекает текст из файла .docx."""
    try:
        doc = docx.Document(file_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Ошибка при чтении DOCX {file_path}: {e}")
        return ""

# Функция для извлечения текста из PDF
def extract_text_from_pdf(file_path):
    """Извлекает текст из файла .pdf."""
    try:
        doc = fitz.open(file_path)
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        doc.close()
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Ошибка при чтении PDF {file_path}: {e}")
        return ""

# Функция для получения описания-саммари из текста
def get_summary_description_from_text(text, summarizer):
    """Генерирует краткое саммари из текста для имени файла."""
    if not text:
        return "text_file" 
    
    # Увеличиваем фрагмент текста для лучшего контекста
    text_to_summarize = text[:1024] 
    
    try:
        # Генерируем саммари (параметры пока те же, можно подбирать)
        summary = summarizer(text_to_summarize, max_length=30, min_length=5, do_sample=False)
        description = summary[0]['summary_text']
    except Exception as e:
        print(f"Ошибка при генерации саммари: {e}")
        description = "text_summary_error"

    return description

# Функция для обработки изображений
def process_image_file(file_path, processor, model):
    """Генерирует подпись к изображению."""
    try:
        image = Image.open(file_path).convert("RGB")
        inputs = processor(image, return_tensors="pt")
        out = model.generate(**inputs)
        description = processor.decode(out[0], skip_special_tokens=True)
        return description
    except Exception as e:
        print(f"Ошибка при обработке изображения {file_path}: {e}")
        return "image_file" # Дефолтное имя при ошибке

# Функция для очистки имени файла
def clean_filename(description):
    """Удаляет недопустимые символы и ограничивает длину."""
    description = re.sub(r'[\/:*?"<>|]', '_', description)  # Заменяем недопустимые символы
    description = description[:50]  # Ограничиваем до 50 символов
    return description.strip()

# Функция для переименования файла
def rename_file(file_path, description):
    """Переименовывает файл, добавляя суффикс при необходимости."""
    if not description:
        print(f"Пропуск переименования файла {file_path}: не удалось сгенерировать описание.")
        return # Не переименовываем, если описание пустое
        
    directory = os.path.dirname(file_path)
    extension = os.path.splitext(file_path)[1]
    new_name_base = clean_filename(description)
    new_name = new_name_base + extension
    new_path = os.path.join(directory, new_name)

    # Обеспечиваем уникальность имени
    counter = 1
    while os.path.exists(new_path):
        # Проверяем, не пытаемся ли мы переименовать файл в его же имя
        if os.path.abspath(file_path) == os.path.abspath(new_path):
             print(f"Пропуск переименования файла {file_path}: новое имя совпадает со старым.")
             return
             
        new_name = new_name_base + f"_{counter}" + extension
        new_path = os.path.join(directory, new_name)
        counter += 1

    try:
        os.rename(file_path, new_path)
        print(f"Переименован: {file_path} -> {new_path}")
    except OSError as e:
        print(f"Ошибка переименования {file_path} в {new_path}: {e}")

# Основная функция для обработки директории
def process_directory(directory, summarizer, img_processor, img_model):
    """Обрабатывает файлы (.txt, .docx, .pdf, .jpg, .png) в директории."""
    supported_text_ext = ('.txt', '.docx', '.pdf')
    supported_img_ext = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')

    for root, _, files in os.walk(directory):
        print(f"Сканирование директории: {root}")
        for file in files:
            file_path = os.path.join(root, file)
            file_lower = file.lower()
            description = None # Сбрасываем описание для каждого файла
            
            try:
                print(f"Обработка файла: {file_path}")
                # Обработка текстовых форматов
                if file_lower.endswith(supported_text_ext):
                    text = ""
                    if file_lower.endswith('.txt'):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                    elif file_lower.endswith('.docx'):
                        text = extract_text_from_docx(file_path)
                    elif file_lower.endswith('.pdf'):
                        text = extract_text_from_pdf(file_path)
                    
                    print(f"  Извлечено символов: {len(text)} из {file_path}") # Debug print

                    if text: # Если текст успешно извлечен
                        description = get_summary_description_from_text(text, summarizer)
                    else:
                        print(f"Не удалось извлечь текст из {file_path}")
                        description = "empty_or_error" # Запасное имя

                # Обработка изображений
                elif file_lower.endswith(supported_img_ext):
                    description = process_image_file(file_path, img_processor, img_model)
                
                else:
                    print(f"Пропуск файла (неподдерживаемый формат): {file_path}")
                    continue # Переходим к следующему файлу

                # Переименование файла, если описание получено
                if description:
                    rename_file(file_path, description)
                else:
                     print(f"Пропуск переименования {file_path}: не удалось сгенерировать описание.")

            except Exception as e:
                print(f"Критическая ошибка при обработке {file_path}: {e}")

# Запуск программы
if __name__ == "__main__":
    print("Загрузка моделей...")
    # Заменяем модель на google/pegasus-xsum
    summarization_pipeline = pipeline("summarization", model="google/pegasus-xsum") 
    blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
    print("Модели загружены.")

    # Получаем путь к директории из переменной окружения DATA_DIR,
    # или используем текущую директорию, если запускаем не в Docker
    default_dir = "." # Текущая директория по умолчанию
    directory = os.environ.get("DATA_DIR", default_dir)

    # Проверка, существует ли директория
    if not os.path.isdir(directory):
        print(f"Ошибка: Директория '{directory}' не найдена.")
        sys.exit(1)
    else:
        print(f"Начинаю обработку директории: {directory}")
        process_directory(directory, summarization_pipeline, blip_processor, blip_model) # Передаем модели
        print("Обработка завершена.") 