# ZuzublikBot

### Тестовое задание

---
### В `examples` находятся файлы для проверки работы бота.

## Установка

1. Клонируйте репозиторий.
   ```bash
   git clone https://github.com/Slava140/Jora.git
   ```

2. Переименуйте файл `.env.example` в `.env`.
   ```bash
   mv .env.example .env
   ```

3. Замените значение `TG_BOT_TOKEN` на Ваш токен.
   ```bash
   TG_BOT_TOKEN=your_token
   ```

4. Установите зависимости.
   ```bash
   poetry install
   ```

5. Запустите бота.
   ```bash
   poetry run pyhton src/main.py
   ```