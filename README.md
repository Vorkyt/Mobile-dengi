# 💰 Мой Бюджет — Kivy (Python → Android APK)

## Структура проекта
```
expense_tracker/
├── main.py           ← весь код приложения
├── buildozer.spec    ← конфигурация сборки APK
└── README.md
```

## Запуск на компьютере (тест)

```bash
pip install kivy
python main.py
```

## Сборка APK для Android

### Способ 1 — Google Colab (рекомендуется, бесплатно)

1. Откройте https://colab.research.google.com
2. Создайте новый ноутбук и вставьте:

```python
# Установка зависимостей
!pip install buildozer cython
!sudo apt-get install -y \
    python3-pip build-essential git python3 python3-dev \
    libffi-dev libssl-dev

# Загрузите файлы main.py и buildozer.spec в Colab через левую панель Files

# Сборка APK
%cd /content
!buildozer android debug
```

3. Готовый APK будет в папке `bin/`
4. Скачайте и установите на телефон

### Способ 2 — Linux/WSL локально

```bash
sudo apt install python3-pip build-essential git
pip3 install buildozer cython

cd expense_tracker/
buildozer android debug
```

### Способ 3 — GitHub Actions (автоматически)

Создайте репозиторий на GitHub, добавьте файлы и настройте Actions
с workflow для buildozer — APK будет собираться автоматически.

## Возможности приложения

- ✅ Ввод ежемесячного дохода
- ✅ Выбор валюты (₽, $, €, ₸, ₴)
- ✅ Добавление расходов по категориям
- ✅ Диаграмма расходов по категориям
- ✅ Остаток = доход − расходы
- ✅ Удаление записей
- ✅ Сохранение данных в JSON (между сессиями)
- ✅ Тёмная тема

## Категории расходов

🏠 Жильё | 🍕 Еда | 🚌 Транспорт | ❤️ Здоровье
🎮 Развлечения | 👗 Одежда | 📚 Образование | 📦 Прочее
