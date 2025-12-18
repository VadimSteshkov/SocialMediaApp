# Exercise 5: Image Resize Microservice

## Текущее состояние проекта

### Что уже есть:
1. **REST API** (FastAPI) - `api.py`
   - Поддержка создания постов с URL изображений
   - Хранение только URL изображений в БД (не файлы)
   - PostgreSQL/SQLite поддержка

2. **База данных** - `database.py`
   - Таблица `posts` с полем `image` (TEXT) - хранит только URL
   - Нет поддержки хранения файлов

3. **Frontend** - `static/app.js`, `static/index.html`
   - Отображает изображения по URL
   - Нет загрузки файлов

4. **Docker** - `Dockerfile`, `docker-compose.yml`
   - Один контейнер для API
   - PostgreSQL контейнер

5. **GitHub Actions**
   - Тесты (`test.yml`)
   - Docker build (`docker-build.yml`)

### Проблема:
- Изображения загружаются полностью, что вызывает долгую загрузку
- Нет оптимизации изображений
- Нет системы для предобработки

---

## Что нужно реализовать

### 1. Хранение изображений
- **Полноразмерные изображения**: сохранять в файловой системе или S3-подобном хранилище
- **Уменьшенные версии (thumbnails)**: сохранять отдельно
- **Обновить схему БД**: добавить поле `image_thumbnail` в таблицу `posts`

### 2. Загрузка файлов
- Добавить endpoint для загрузки файлов (`POST /api/posts/upload`)
- Сохранять файлы локально (в `uploads/` или `static/uploads/`)
- Возвращать URL для полноразмерного изображения

### 3. Message Queue (Очередь сообщений)
- Использовать **RabbitMQ** или **Redis** для очереди задач
- При загрузке изображения отправлять сообщение в очередь
- Сообщение содержит: `post_id`, `image_path`

### 4. Image Resize Microservice
- Отдельный Python сервис (контейнер)
- Слушает очередь сообщений
- Получает задачу на ресайз
- Обрабатывает изображение (Pillow/PIL)
- Сохраняет thumbnail
- Обновляет БД с путем к thumbnail

### 5. Обновление REST API
- Endpoint для загрузки файлов
- Endpoint для получения изображений (полноразмерных и thumbnails)
- Обновить `PostResponse` модель: добавить `image_thumbnail`
- По умолчанию возвращать thumbnail, опционально - полное изображение

### 6. Обновление WebApp
- Добавить загрузку файлов в форму
- Отображать thumbnails в списке постов
- При клике показывать полноразмерное изображение

### 7. Docker Compose обновление
- Добавить контейнер для RabbitMQ/Redis
- Добавить контейнер для Image Resize Service
- Настроить networking между сервисами
- Общие volumes для хранения изображений

### 8. GitHub Actions
- Тесты для нового функционала
- Build и push контейнеров для:
  - API сервиса
  - Image Resize сервиса

---

## Архитектура решения

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────┐
│   FastAPI API   │  ← Основной API сервис
│   (api.py)      │
└─────┬───────┬───┘
      │       │
      │       │ Message Queue
      │       ▼
      │  ┌──────────────┐
      │  │  RabbitMQ    │  ← Очередь задач
      │  └──────┬───────┘
      │         │
      │         ▼
      │  ┌──────────────────┐
      │  │ Image Resize      │  ← Микросервис ресайза
      │  │ Microservice      │
      │  └───────────────────┘
      │
      ▼
┌─────────────┐
│ PostgreSQL  │  ← База данных
└─────────────┘

┌─────────────┐
│  File Store │  ← Хранилище изображений
│  (uploads/) │     (shared volume)
└─────────────┘
```

---

## План реализации

### Этап 1: Обновление базы данных
- [ ] Добавить поле `image_thumbnail` в таблицу `posts`
- [ ] Обновить методы `insert_post`, `get_post_by_id` и т.д.

### Этап 2: Загрузка файлов в API
- [ ] Добавить endpoint `POST /api/posts/upload` для загрузки файлов
- [ ] Сохранять файлы в `uploads/full/`
- [ ] Отправлять сообщение в очередь после сохранения

### Этап 3: Message Queue
- [ ] Добавить RabbitMQ в `docker-compose.yml`
- [ ] Установить библиотеку `pika` для работы с RabbitMQ
- [ ] Реализовать отправку сообщений в очередь

### Этап 4: Image Resize Microservice
- [ ] Создать `image_resize_service.py`
- [ ] Создать `Dockerfile.resize` для микросервиса
- [ ] Реализовать слушатель очереди
- [ ] Реализовать ресайз изображений (Pillow)
- [ ] Обновление БД с thumbnail путем

### Этап 5: Обновление API
- [ ] Обновить `PostResponse` модель
- [ ] Endpoint для получения изображений
- [ ] Обновить все endpoints для возврата thumbnail

### Этап 6: Обновление Frontend
- [ ] Добавить `<input type="file">` в форму
- [ ] Отображать thumbnails в списке
- [ ] Модальное окно для полноразмерного изображения

### Этап 7: Docker Compose
- [ ] Добавить RabbitMQ сервис
- [ ] Добавить Image Resize сервис
- [ ] Настроить volumes для изображений
- [ ] Настроить networking

### Этап 8: GitHub Actions
- [ ] Обновить тесты
- [ ] Добавить build для Image Resize контейнера
- [ ] Тестирование интеграции

---

## Технологии

- **Message Queue**: RabbitMQ (легче для начала) или Redis
- **Image Processing**: Pillow (PIL) - `pip install Pillow`
- **RabbitMQ Client**: `pika` - `pip install pika`
- **File Upload**: FastAPI `UploadFile`

---

## Структура файлов (новые)

```
SocialMediaApp/
├── api.py                          # Обновить для загрузки файлов
├── database.py                      # Обновить схему БД
├── image_resize_service.py          # НОВЫЙ: Микросервис ресайза
├── Dockerfile                       # Обновить для API
├── Dockerfile.resize               # НОВЫЙ: Dockerfile для микросервиса
├── docker-compose.yml              # Обновить: добавить RabbitMQ и resize service
├── requirements.txt                # Обновить: добавить pika, Pillow
├── requirements-resize.txt         # НОВЫЙ: зависимости для микросервиса
├── uploads/                        # НОВЫЙ: хранилище изображений
│   ├── full/                       # Полноразмерные
│   └── thumbnails/                 # Уменьшенные
├── static/
│   └── app.js                      # Обновить для загрузки файлов
└── .github/workflows/
    ├── test.yml                    # Обновить тесты
    └── docker-build.yml            # Обновить для build обоих контейнеров
```

---

## Следующие шаги

1. ✅ Создана ветка `feature/image-resize-microservice`
2. ⏭️ Начать с обновления схемы БД
3. ⏭️ Реализовать загрузку файлов
4. ⏭️ Добавить RabbitMQ
5. ⏭️ Создать микросервис ресайза
6. ⏭️ Обновить frontend
7. ⏭️ Настроить Docker Compose
8. ⏭️ Обновить GitHub Actions

---

## Примечания

- Используем RabbitMQ как более стандартное решение для message queues
- Thumbnail размер: 300x300px (можно настраивать)
- Форматы: JPEG, PNG
- Хранение: локальная файловая система (можно позже мигрировать на S3)



