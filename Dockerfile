# Используем официальный образ PyTorch с CUDA 11.8 и Python 3.10
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем основные зависимости из requirements.txt
# PyTorch уже есть в базовом образе, но могут потребоваться другие версии. 
# Уточняем установку torch/torchvision/torchaudio с нужной версией CUDA на всякий случай
# (Хотя в образе pytorch/pytorch он уже должен быть правильным)
RUN pip install --no-cache-dir -r requirements.txt 
# Если установка torch из requirements вызывает проблемы, можно закомментировать его там
# и использовать команду установки с сайта PyTorch:
# RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Копируем скрипт Python в рабочую директорию
COPY main.py .

# Указываем команду для запуска при старте контейнера
# Мы будем передавать путь к директории как аргумент или использовать переменную окружения,
# поэтому здесь не указываем CMD или ENTRYPOINT, либо настроим их позже.
# Пока оставим возможность запускать скрипт вручную: python main.py

# Опционально: Создадим директорию для данных внутри контейнера
RUN mkdir /data
VOLUME /data

# Укажем entrypoint, чтобы можно было легко запустить скрипт
ENTRYPOINT ["python", "main.py"] 