-- Перенос данных из импортированных CSV-таблиц (imp_*) в таблицы базы.
-- Порядок: сначала справочники, потом таблицы, которые на них ссылаются.
-- Перед запуском: выполнен schema.sql и импортированы CSV:
--   imp_users       (role, fio, login, pass)
--   imp_pvz         (addr)
--   imp_tovar       (art, name, unit, price, suppl, manuf, cat, discount, quant, descr, photo)
--   imp_zakaz       (num, zak_date, dost_date, pvz, fio, code, status)
--   imp_zakaz_tovar (zak_id, art, quant)

INSERT INTO role (role) SELECT DISTINCT TRIM(role) FROM imp_users;

INSERT INTO users (role_id, fio, login, pass)
SELECT role.id, TRIM(i.fio), TRIM(i.login), i.pass
FROM imp_users i
JOIN role ON role.role = TRIM(i.role);

INSERT INTO pvz (addr) SELECT TRIM(addr) FROM imp_pvz ORDER BY rowid;

INSERT INTO suppl (suppl) SELECT DISTINCT TRIM(suppl) FROM imp_tovar;
INSERT INTO manuf (manuf) SELECT DISTINCT TRIM(manuf) FROM imp_tovar;
INSERT INTO cat (cat)     SELECT DISTINCT TRIM(cat)   FROM imp_tovar;

INSERT INTO tovar (art, name, unit, price, suppl, manuf, cat, discount, quant, descr, photo)
SELECT TRIM(i.art), TRIM(i.name), TRIM(i.unit), i.price, suppl.id, manuf.id, cat.id,
       i.discount, i.quant, TRIM(i.descr), NULLIF(TRIM(i.photo), '')
FROM imp_tovar i
JOIN suppl ON suppl.suppl = TRIM(i.suppl)
JOIN manuf ON manuf.manuf = TRIM(i.manuf)
JOIN cat   ON cat.cat     = TRIM(i.cat);

INSERT INTO status (status) SELECT DISTINCT TRIM(status) FROM imp_zakaz;

INSERT INTO zakaz (id, zak_date, dost_date, pvz_id, user_id, code, status_id)
SELECT i.num, i.zak_date, i.dost_date, i.pvz, users.id, i.code, status.id
FROM imp_zakaz i
JOIN users  ON users.fio = TRIM(i.fio)
JOIN status ON status.status = TRIM(i.status);

INSERT INTO zakaz_tovar (zak_id, tovar_id, quant)
SELECT i.zak_id, tovar.id, i.quant
FROM imp_zakaz_tovar i
JOIN tovar ON tovar.art = TRIM(i.art);

-- Проверка: числа должны совпасть с количеством строк в Excel
SELECT 'users', COUNT(*) FROM users UNION ALL
SELECT 'pvz', COUNT(*) FROM pvz UNION ALL
SELECT 'tovar', COUNT(*) FROM tovar UNION ALL
SELECT 'zakaz', COUNT(*) FROM zakaz UNION ALL
SELECT 'zakaz_tovar', COUNT(*) FROM zakaz_tovar;

-- Когда всё совпало, временные таблицы больше не нужны
DROP TABLE imp_users;
DROP TABLE imp_pvz;
DROP TABLE imp_tovar;
DROP TABLE imp_zakaz;
DROP TABLE imp_zakaz_tovar;
