# ZuzublikBot

### Тестовое задание

---
### В `examples` находятся файлы для проверки работы бота.

## Установка

1. Клонируйте репозиторий.
   ```bash
   git clone https://github.com/Slava140/zuzubliks_parser.git
   ```
   
2. Перейдите в созданную директорию.
   ```bash
   cd zuzubliks_parser
   ```

3. Переименуйте файл `.env.example` в `.env`.
   ```bash
   mv .env.example .env
   ```

4. Замените значение `TG_BOT_TOKEN` на Ваш токен.
   ```bash
   TG_BOT_TOKEN=your_token
   ```

5. Установите зависимости.
   ```bash
   poetry install
   ```

6. Запустите бота.
   ```bash
   poetry run python src/main.py
   ```
