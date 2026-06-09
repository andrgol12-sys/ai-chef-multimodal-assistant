# AI Chef

CLI-приложение и веб-сайт на Python, которые по списку ингредиентов предлагают 3 блюда с рецептами через OpenAI или GigaChat. Поддерживают распознавание продуктов на фото через OpenAI Vision.

## Возможности

- интерактивный ввод ингредиентов в терминале;
- распознавание ингредиентов на фото (`--image`) через OpenAI Vision;
- объединение ингредиентов с фото и из аргументов `--ingredients`;
- генерация 3 разных блюд с названием, описанием, уровнем сложности, калорийностью, способом подачи, ингредиентами, пошаговым рецептом и временем приготовления;
- вывод результата в консоль;
- сохранение в папку `outputs` в формате `txt`, `json` или обоих сразу (включая найденные на фото ингредиенты и время обработки Vision);
- генерация изображения первого блюда через OpenAI Image API в `outputs/images/`;
- веб-интерфейс на Flask с формой ввода ингредиентов и загрузкой фото.

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Скопируйте `.env.example` в `.env` и заполните ключи API.

## Переменные окружения

| Переменная | Описание |
|---|---|
| `LLM_PROVIDER` | Провайдер по умолчанию: `openai` или `gigachat` |
| `OPENAI_API_KEY` | API-ключ OpenAI |
| `OPENAI_MODEL` | Модель OpenAI для рецептов, по умолчанию `gpt-4o-mini` |
| `OPENAI_VISION_MODEL` | Модель OpenAI для распознавания фото, по умолчанию `gpt-4o-mini` |
| `OPENAI_IMAGE_MODEL` | Модель OpenAI для генерации изображения блюда, по умолчанию `dall-e-3` |
| `OPENAI_IMAGE_SIZE` | Размер изображения, по умолчанию `1024x1024` |
| `GIGACHAT_CREDENTIALS` | Authorization key GigaChat |
| `GIGACHAT_MODEL` | Модель GigaChat, по умолчанию `GigaChat` |
| `GIGACHAT_SCOPE` | Scope доступа, по умолчанию `GIGACHAT_API_PERS` |
| `GIGACHAT_VERIFY_SSL` | Проверка SSL-сертификата (`true` / `false`) |

## Запуск

### Веб-сайт (Flask)

```bash
python app.py
```

Откройте в браузере: [http://127.0.0.1:5000](http://127.0.0.1:5000)

На странице можно:
- ввести ингредиенты текстом;
- загрузить фото продуктов;
- выбрать провайдера LLM;
- включить сомнительные продукты с фото чекбоксом;
- получить 3 рецепта, изображение первого блюда и ссылки на TXT/JSON.

### CLI

Интерактивный режим:

```bash
python main.py
```

Только текстовые ингредиенты:

```bash
python main.py --provider openai --format json --ingredients яйца молоко мука сахар
python main.py --provider gigachat --format txt --ingredients "картофель, лук, морковь"
```

Распознавание продуктов на фото (OpenAI Vision):

```bash
# файл в папке inputs/
python main.py --image products.jpg

# полный или относительный путь к файлу
python main.py --image C:\Photos\fridge.png
```

Фото + дополнительные ингредиенты (списки объединяются):

```bash
python main.py --image inputs/fridge.jpg --ingredients соль перец масло
python main.py --image fridge.jpg --ingredients яйца молоко --provider openai --format both
```

> **Примечание:** распознавание изображений всегда выполняется через OpenAI Vision (`OPENAI_API_KEY`). Генерация рецептов — через выбранный `--provider`.

## Аргументы CLI

- `--provider` — `openai` или `gigachat`;
- `--format` — `txt`, `json` или `both` (по умолчанию `both`);
- `--ingredients` — список ингредиентов без интерактивного ввода;
- `--image` — путь к изображению продуктов (jpg, jpeg, png, gif, webp).

## Структура проекта

```text
AI Chef/
├── app.py
├── main.py
├── config.py
├── templates/
│   └── index.html
├── static/
│   └── style.css
├── models.py
├── prompts.py
├── output.py
├── llm/
│   ├── openai_client.py
│   ├── openai_vision.py
│   ├── openai_image.py
│   ├── gigachat_client.py
│   └── factory.py
├── inputs/
├── outputs/
│   └── images/
├── requirements.txt
├── .env.example
└── README.md
```

## Пример результата

После запуска приложение создаст файлы вида:

- `outputs/recipes_20260531_153045.txt`
- `outputs/recipes_20260531_153045.json`
- `outputs/images/salat_iz_ovoshchey_20260531_153100.png` (первое блюдо из списка)

В JSON при использовании `--image` дополнительно сохраняется блок `vision`:

```json
{
  "vision": {
    "image_path": "G:/.../inputs/fridge.jpg",
    "detected_ingredients": ["яйца", "молоко", "сыр"],
    "text_ingredients": ["соль", "перец"],
    "processing_time_sec": 2.145
  },
  "source_ingredients": ["яйца", "молоко", "сыр", "соль", "перец"],
  "dishes": []
}
```
