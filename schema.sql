-- Схема базы данных магазина обуви (SQLite)
-- Соответствует ER-диаграмме: 10 таблиц, 9 связей.
PRAGMA foreign_keys = ON;

-- ===== Справочники =====

CREATE TABLE role (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL UNIQUE              -- Администратор / Менеджер / Авторизированный клиент
);

CREATE TABLE status (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL UNIQUE            -- Новый / Завершен
);

CREATE TABLE pvz (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    addr TEXT NOT NULL                     -- адрес пункта выдачи
);

CREATE TABLE suppl (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    suppl TEXT NOT NULL UNIQUE             -- поставщик
);

CREATE TABLE manuf (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    manuf TEXT NOT NULL UNIQUE             -- производитель
);

CREATE TABLE cat (
    id  INTEGER PRIMARY KEY AUTOINCREMENT,
    cat TEXT NOT NULL UNIQUE               -- категория товара
);

-- ===== Основные таблицы =====

CREATE TABLE users (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    role_id INTEGER NOT NULL REFERENCES role(id),
    fio     TEXT NOT NULL,
    login   TEXT NOT NULL UNIQUE,
    pass    TEXT NOT NULL
);

CREATE TABLE tovar (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    art      TEXT NOT NULL UNIQUE,          -- артикул
    name     TEXT NOT NULL,                 -- наименование
    unit     TEXT NOT NULL DEFAULT 'шт.',   -- единица измерения
    price    REAL NOT NULL CHECK (price >= 0),
    suppl    INTEGER NOT NULL REFERENCES suppl(id),
    manuf    INTEGER NOT NULL REFERENCES manuf(id),
    cat      INTEGER NOT NULL REFERENCES cat(id),
    discount INTEGER NOT NULL DEFAULT 0 CHECK (discount BETWEEN 0 AND 100),  -- скидка, %
    quant    INTEGER NOT NULL DEFAULT 0 CHECK (quant >= 0),                  -- кол-во на складе
    descr    TEXT,                          -- описание
    photo    TEXT                           -- имя файла фото (может быть пустым)
);

CREATE TABLE zakaz (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    zak_date  TEXT NOT NULL,                -- дата заказа, ГГГГ-ММ-ДД
    dost_date TEXT NOT NULL,                -- дата доставки, ГГГГ-ММ-ДД
    pvz_id    INTEGER NOT NULL REFERENCES pvz(id),
    user_id   INTEGER NOT NULL REFERENCES users(id),
    code      INTEGER NOT NULL,             -- код для получения
    status_id INTEGER NOT NULL REFERENCES status(id)
);

-- Состав заказа (связь «многие ко многим» между zakaz и tovar)
CREATE TABLE zakaz_tovar (
    zak_id   INTEGER NOT NULL REFERENCES zakaz(id) ON DELETE CASCADE,
    tovar_id INTEGER NOT NULL REFERENCES tovar(id),
    quant    INTEGER NOT NULL CHECK (quant > 0),
    PRIMARY KEY (zak_id, tovar_id)
);
