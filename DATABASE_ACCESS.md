# Доступ к базе данных

## PostgreSQL (Docker)

### Через Docker Compose

```bash
# Подключиться к базе данных через psql
docker-compose exec db psql -U postgres -d social_media

# Или с указанием всех параметров
docker-compose exec db psql -U postgres -d social_media -h localhost
```

### Параметры подключения

- **Host**: `localhost` (извне контейнера) или `db` (изнутри Docker сети)
- **Port**: `5434` (извне) или `5432` (изнутри)
- **Database**: `social_media` (по умолчанию)
- **User**: `postgres` (по умолчанию)
- **Password**: `postgres` (по умолчанию)

### Полезные SQL команды

```sql
-- Посмотреть все таблицы
\dt

-- Посмотреть структуру таблицы posts
\d posts

-- Посмотреть все посты
SELECT id, user, text, image, image_thumbnail, created_at FROM posts;

-- Посмотреть посты с thumbnails
SELECT id, user, text, image, image_thumbnail FROM posts WHERE image_thumbnail IS NOT NULL;

-- Посчитать посты
SELECT COUNT(*) FROM posts;

-- Удалить все посты
DELETE FROM posts;

-- Посмотреть последний пост
SELECT * FROM posts ORDER BY created_at DESC LIMIT 1;
```

### Подключение из внешних инструментов

#### pgAdmin, DBeaver, или другой клиент:

- **Host**: `localhost`
- **Port**: `5434`
- **Database**: `social_media`
- **Username**: `postgres`
- **Password**: `postgres`

### Через командную строку (локально)

Если у вас установлен `psql` локально:

```bash
psql -h localhost -p 5434 -U postgres -d social_media
```

## SQLite (если используется локально)

Если запускаете без Docker и используете SQLite:

```bash
# Подключиться к SQLite базе
sqlite3 social_media.db

# Или с указанием пути
sqlite3 data/social_media.db
```

### Полезные SQLite команды

```sql
-- Посмотреть все таблицы
.tables

-- Посмотреть структуру таблицы
.schema posts

-- Посмотреть все посты
SELECT * FROM posts;

-- Выход
.quit
```

## Проверка подключения

### Проверить, что база работает:

```bash
# Проверить статус контейнера
docker-compose ps db

# Проверить логи
docker-compose logs db

# Проверить подключение
docker-compose exec db pg_isready -U postgres
```

## Резервное копирование

### Создать backup:

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U postgres social_media > backup_$(date +%Y%m%d_%H%M%S).sql

# Восстановить из backup
docker-compose exec -T db psql -U postgres social_media < backup.sql
```

## Обновление схемы БД

После изменений в `database.py`, схема обновляется автоматически при первом запуске приложения.

Если нужно принудительно обновить:

```bash
# Перезапустить API контейнер
docker-compose restart api
```



