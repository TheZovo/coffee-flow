# Coffee Flow Mini App

MVP под Telegram Mini App для сети кофеен с функциональным аналогом Varka по публично доступным сценариям:
- сеть филиалов;
- витрина с акциями и категориями;
- самовывоз и доставка;
- бонусный баланс и списание бонусов;
- промокоды;
- история заказов и оценка после выдачи;
- отдельный бот для баристы с управлением статусами.

## Что внутри

### Клиентский контур
- Telegram-бот для клиента с inline-кнопкой открытия Mini App.
- Mini App на русском языке.
- Профиль с именем и телефоном.
- Выбор филиала, режима заказа и времени.
- Корзина, промокод, списание бонусов.
- История заказов и отзывы.

### Контур баристы
- Отдельный Telegram-бот на втором токене.
- Авторизация через `/login <секрет>`.
- Команды очереди:
  - `/queue`
  - `/order <номер>`
  - `/today`
  - `/logout`
- Inline-кнопки по заказу:
  - `В работу`
  - `Готов`
  - `В пути`
  - `Выдан`
  - `Отменить`

## Стек
- Python 3.12
- FastAPI
- aiogram 3
- PostgreSQL
- SQLAlchemy async
- HTML/CSS/Vanilla JS
- Docker / Docker Compose

## Быстрый старт
1. Скопируйте `.env.example` в `.env`.
2. Заполните переменные:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_BARISTA_BOT_TOKEN`
   - `PUBLIC_BASE_URL`
   - `SESSION_SECRET`
   - `BARISTA_SECRET`
3. Запустите:
   - `docker compose up -d --build`
4. Проверьте health:
   - [http://localhost:8000/health](http://localhost:8000/health)
5. Загруженные из админки изображения сохраняются в отдельном Docker volume `coffee_uploads` и не теряются при пересоздании контейнера.

## Основные переменные `.env`
- `DATABASE_URL=postgresql+asyncpg://coffee:coffee@db:5432/coffee`
- `APP_TIMEZONE=Europe/Minsk`
- `TELEGRAM_BOT_TOKEN=...`
- `TELEGRAM_BARISTA_BOT_TOKEN=...`
- `PUBLIC_BASE_URL=https://your-domain.example`
- `TELEGRAM_MINIAPP_URL=`  
  Если пусто, Mini App будет доступен по `PUBLIC_BASE_URL/miniapp`.
- `BARISTA_CHAT_ID=`  
  Опционально, если нужен общий чат-канал уведомлений.
- `BARISTA_SECRET=coffee-barista-secret`
- `SESSION_SECRET=change-me-coffee-session-secret`
- `DEBUG_ALLOW_FAKE_INITDATA=false`
- `AUTO_SEED=true`

## Как это работает

### Клиент
1. Пользователь пишет клиентскому боту `/start`.
2. Нажимает inline-кнопку открытия Mini App.
3. Mini App проходит Telegram-auth и создает cookie-сессию.
4. Пользователь заполняет имя и телефон.
5. Выбирает филиал, самовывоз или доставку, добавляет позиции.
6. Оформляет заказ.
7. Получает статус заказа в Mini App, а бариста получает уведомление во втором боте.

### Бариста
1. Бариста открывает отдельного бота.
2. Выполняет `/login <секрет>`.
3. Получает новые заказы с inline-кнопками.
4. Меняет статусы прямо в Telegram.
5. Клиенту отправляются обновления и после завершения начисляются бонусы.

## Команды клиентского бота
- `/start`
- `/app`
- `/help`

## Команды бариста-бота
- `/start`
- `/login <секрет>`
- `/queue`
- `/order <номер>`
- `/today`
- `/logout`

## Отладка без Telegram
Для локальной проверки Mini App без реального `init_data`:
- `DEBUG_ALLOW_FAKE_INITDATA=true`
- открыть `http://localhost:8000/miniapp?debug_tg_id=123456`

## Что уже сидируется
- 3 филиала;
- категории меню;
- баннеры;
- позиции кофе и десертов с изображениями;
- промокоды `WELCOME10` и `CAP20`.

## Важное ограничение
Под «аналогом Varka» здесь реализован функциональный аналог по публичным признакам приложения, а не побитовый клон приватной бизнес-логики или фирменного дизайна.
