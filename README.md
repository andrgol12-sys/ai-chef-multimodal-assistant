# 🧑‍🍳 AI Chef — Multimodal Recipe Assistant

AI Chef — это мультимодальный AI-ассистент, который помогает придумать рецепты из продуктов, которые уже есть дома.

Проект умеет работать с текстом и изображениями: пользователь может ввести список ингредиентов вручную или загрузить фото продуктов. Приложение распознаёт продукты через OpenAI Vision, генерирует рецепты через LLM и создаёт изображение готового блюда.

---

## 🚀 Возможности

* 📝 ввод ингредиентов текстом;
* 📷 загрузка фото продуктов;
* 👁 распознавание ингредиентов через OpenAI Vision;
* ⚠️ разделение продуктов на уверенно распознанные и сомнительные;
* 🧠 генерация 3 рецептов через OpenAI или GigaChat;
* 🖼 генерация изображения первого блюда через OpenAI Image API;
* 🌐 веб-интерфейс на Flask;
* 💻 CLI-режим для запуска из терминала;
* 📁 сохранение результатов в TXT и JSON;
* 🧪 обработка ошибок внешних API без падения приложения.

---

## 🧩 Архитектура

```text
Текст / Фото продуктов
        ↓
OpenAI Vision
        ↓
Список ингредиентов
        ↓
LLM: OpenAI / GigaChat
        ↓
3 рецепта
        ↓
OpenAI Image API
        ↓
Изображение готового блюда
        ↓
Flask UI + TXT/JSON outputs
```

---

## 🛠️ Стек технологий

* Python
* Flask
* OpenAI API
* OpenAI Vision
* OpenAI Image API
* GigaChat API
* python-dotenv
* HTML / CSS
* Git / GitHub

---

## 📸 Пример работы

### Ввод

Пользователь может:

1. Ввести ингредиенты вручную:

```text
картофель, лук, яйца
```

2. Или загрузить фото продуктов.

---

### Вывод

Приложение показывает:

* распознанные ингредиенты;
* сомнительные ингредиенты;
* итоговый список продуктов;
* 3 рецепта;
* сложность, калорийность и время приготовления;
* пошаговую инструкцию;
* изображение первого блюда;
* ссылки на сохранённые TXT/JSON файлы.

---

## 🌐 Запуск веб-интерфейса

### 1. Клонировать репозиторий

```bash
git clone https://github.com/andrgol12-sys/ai-chef-multimodal-assistant.git
cd ai-chef-multimodal-assistant
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
```

### 3. Активировать окружение

Windows PowerShell:

```bash
.venv\Scripts\activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Создать `.env`

Скопируйте файл `.env.example` в `.env` и добавьте свои ключи API.

```env
LLM_PROVIDER=openai

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_VISION_MODEL=gpt-4o-mini

OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1024x1024

GIGACHAT_CREDENTIALS=your_gigachat_authorization_key
GIGACHAT_MODEL=GigaChat
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_VERIFY_SSL=false

FLASK_SECRET_KEY=your_secret_key
```

### 6. Запустить Flask

```bash
python app.py
```

Откройте в браузере:

```text
http://127.0.0.1:5000
```

---

## 💻 CLI-режим

Интерактивный запуск:

```bash
python main.py
```

Запуск по текстовым ингредиентам:

```bash
python main.py --ingredients картофель лук яйца
```

Запуск по фото:

```bash
python main.py --image fridge.jpg
```

Фото + дополнительные ингредиенты:

```bash
python main.py --image fridge.jpg --ingredients соль перец масло
```

---

## 📁 Структура проекта

```text
AI Chef/
├── app.py                  # Flask-приложение
├── main.py                 # CLI-запуск
├── config.py               # конфигурация и переменные окружения
├── models.py               # модели данных
├── output.py               # сохранение TXT/JSON
├── prompts.py              # промпты для LLM
│
├── llm/
│   ├── openai_client.py    # генерация рецептов через OpenAI
│   ├── openai_vision.py    # распознавание продуктов по фото
│   ├── openai_image.py     # генерация изображения блюда
│   ├── gigachat_client.py  # генерация рецептов через GigaChat
│   ├── factory.py
│   └── utils.py
│
├── templates/
│   └── index.html
│
├── static/
│   └── style.css
│
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧪 Что было протестировано

* генерация рецептов по текстовым ингредиентам;
* распознавание продуктов по фото;
* обработка сомнительных ингредиентов;
* генерация изображения готового блюда;
* сохранение результатов в TXT и JSON;
* запуск через CLI;
* запуск через Flask-интерфейс.

---

## ⚠️ Ограничения MVP

Распознавание продуктов по фото зависит от качества изображения. Если продукты находятся в сетке, прозрачном пакете или упаковке, Vision-модель может ошибиться. Поэтому в проект добавлен механизм сомнительных ингредиентов: пользователь сам решает, включать их в итоговый список или нет.

---

## 📌 Статус проекта

MVP готов.

Проект создан как учебная работа по теме мультимодальности и вайбкодинга: от CLI-прототипа до веб-интерфейса с Vision, LLM и генерацией изображения.

---

## 👤 Author

Created by [andrgol12-sys](https://github.com/andrgol12-sys)
AIGolubev