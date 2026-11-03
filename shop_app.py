import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

DB_PATH = "shop.db"
RES_DIR = "import"
PLACEHOLDER = "picture.png"

# Стиль: заменить на значения из руководства по стилю (Приложение 3)
FONT = ("Times New Roman", 12)
FONT_BOLD = ("Times New Roman", 12, "bold")
FONT_OLD_PRICE = ("Times New Roman", 12, "overstrike")
FONT_TITLE = ("Times New Roman", 18, "bold")
COLOR_BG = "#FFFFFF"
COLOR_ACCENT = "#00FA9A"
COLOR_BIG_DISCOUNT = "#2E8B57"
COLOR_NO_STOCK = "#ADD8E6"

ROLE_GUEST = "Гость"
ROLE_CLIENT = "Авторизированный клиент"
ROLE_MANAGER = "Менеджер"
ROLE_ADMIN = "Администратор"

ALL_SUPPLIERS = "Все поставщики"
SORT_NONE = "Без сортировки"
SORT_ASC = "Остаток: по возрастанию"
SORT_DESC = "Остаток: по убыванию"

PRODUCTS_SQL = """
    SELECT tovar.id, tovar.art, tovar.name, cat.cat, tovar.descr, manuf.manuf,
           suppl.suppl, tovar.price, tovar.unit, tovar.quant, tovar.discount, tovar.photo
    FROM tovar
    JOIN cat ON cat.id = tovar.cat
    JOIN manuf ON manuf.id = tovar.manuf
    JOIN suppl ON suppl.id = tovar.suppl
    ORDER BY tovar.id
"""

ORDERS_SQL = """
    SELECT zakaz.id, zakaz.zak_date, zakaz.dost_date, zakaz.code,
           status.status, pvz.addr, users.fio
    FROM zakaz
    JOIN status ON status.id = zakaz.status_id
    JOIN pvz ON pvz.id = zakaz.pvz_id
    JOIN users ON users.id = zakaz.user_id
    ORDER BY zakaz.id
"""


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query(sql, params=()):
    with connect() as conn:
        return conn.execute(sql, params).fetchall()


def execute(sql, params=()):
    with connect() as conn:
        return conn.execute(sql, params).lastrowid


def load_photo(file_name, size):
    path = os.path.join(RES_DIR, file_name or PLACEHOLDER)
    if not os.path.exists(path):
        path = os.path.join(RES_DIR, PLACEHOLDER)
    image = Image.open(path)
    image.thumbnail(size)
    return ImageTk.PhotoImage(image)


def make_scroll_area(parent):
    """Прокручиваемая область: Frame внутри Canvas, потому что сам Frame не прокручивается."""
    canvas = tk.Canvas(parent, bg=COLOR_BG, highlightthickness=0)
    scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=COLOR_BG)
    inner.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"))
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    return inner


def bind_click(widget, handler):
    widget.bind("<Button-1>", handler)
    for child in widget.winfo_children():
        bind_click(child, handler)


class ShopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1100x700")
        self.configure(bg=COLOR_BG)
        self.iconbitmap(os.path.join(RES_DIR, "Icon.ico"))
        # tkinter не хранит картинку сам: без ссылки она исчезнет с экрана
        self.logo = ImageTk.PhotoImage(Image.open(os.path.join(RES_DIR, "Icon.png")).resize((60, 60)))
        self.user_fio = None
        self.user_role = None
        self.form_window = None
        self.show_login()

    def report_callback_exception(self, exc, value, traceback):
        messagebox.showerror("Непредвиденная ошибка",
                             f"Произошла ошибка: {value}\nПовторите действие или перезапустите программу.")

    def clear_window(self):
        self.unbind_all("<MouseWheel>")
        for widget in self.winfo_children():
            widget.destroy()

    def is_staff(self):
        return self.user_role in (ROLE_MANAGER, ROLE_ADMIN)

    # ---------- Вход ----------

    def show_login(self):
        self.clear_window()
        self.title("Вход в систему")
        self.user_fio = None
        self.user_role = None

        form = tk.Frame(self, bg=COLOR_BG)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, image=self.logo, bg=COLOR_BG).pack(pady=5)
        tk.Label(form, text="Вход в систему", font=FONT_TITLE, bg=COLOR_BG).pack(pady=10)

        tk.Label(form, text="Логин", font=FONT, bg=COLOR_BG).pack(anchor="w")
        self.login_entry = tk.Entry(form, font=FONT, width=30)
        self.login_entry.pack(pady=(0, 10))

        tk.Label(form, text="Пароль", font=FONT, bg=COLOR_BG).pack(anchor="w")
        self.password_entry = tk.Entry(form, font=FONT, width=30, show="*")
        self.password_entry.pack(pady=(0, 15))

        tk.Button(form, text="Войти", font=FONT, bg=COLOR_ACCENT, width=25,
                  command=self.login).pack(pady=5)
        tk.Button(form, text="Войти как гость", font=FONT, width=25,
                  command=self.login_as_guest).pack(pady=5)

        self.login_entry.focus()
        self.bind("<Return>", lambda event: self.login())

    def login(self):
        login = self.login_entry.get().strip()
        password = self.password_entry.get()
        if not login or not password:
            messagebox.showwarning("Не все поля заполнены", "Введите логин и пароль.")
            return

        rows = query(
            "SELECT users.fio, role.role FROM users "
            "JOIN role ON role.id = users.role_id "
            "WHERE users.login = ? AND users.pass = ?",
            (login, password),
        )
        if not rows:
            messagebox.showerror(
                "Ошибка входа",
                "Неверный логин или пароль.\nПроверьте раскладку клавиатуры и Caps Lock и попробуйте снова.",
            )
            return

        self.user_fio = rows[0]["fio"]
        self.user_role = rows[0]["role"]
        self.unbind("<Return>")
        self.show_products()

    def login_as_guest(self):
        self.user_fio = "Гость"
        self.user_role = ROLE_GUEST
        self.unbind("<Return>")
        self.show_products()

    def show_header(self, title, back_command=None):
        header = tk.Frame(self, bg=COLOR_ACCENT)
        header.pack(fill="x")
        tk.Label(header, image=self.logo, bg=COLOR_ACCENT).pack(side="left", padx=5, pady=5)
        tk.Label(header, text=title, font=FONT_TITLE, bg=COLOR_ACCENT).pack(side="left", padx=10)
        tk.Button(header, text="Выход", font=FONT, command=self.show_login).pack(side="right", padx=10)
        if back_command:
            tk.Button(header, text="Назад", font=FONT, command=back_command).pack(side="right", padx=5)
        tk.Label(header, text=f"{self.user_fio} ({self.user_role})", font=FONT,
                 bg=COLOR_ACCENT).pack(side="right", padx=10)

    # ---------- Список товаров ----------

    def show_products(self):
        self.clear_window()
        self.title("Список товаров")
        self.show_header("Список товаров")
        if self.is_staff():
            self.show_products_toolbar()

        area = tk.Frame(self, bg=COLOR_BG)
        area.pack(fill="both", expand=True)
        self.product_list = make_scroll_area(area)
        self.refresh_products()

    def show_products_toolbar(self):
        toolbar = tk.Frame(self, bg=COLOR_BG)
        toolbar.pack(fill="x", padx=10, pady=5)

        tk.Label(toolbar, text="Поиск:", font=FONT, bg=COLOR_BG).pack(side="left")
        self.search_var = tk.StringVar()
        # trace_add вызывает обновление при каждом изменении текста: поиск без кнопки «Найти»
        self.search_var.trace_add("write", lambda *args: self.refresh_products())
        tk.Entry(toolbar, textvariable=self.search_var, font=FONT, width=25).pack(side="left", padx=(5, 15))

        tk.Label(toolbar, text="Поставщик:", font=FONT, bg=COLOR_BG).pack(side="left")
        suppliers = [ALL_SUPPLIERS] + [row["suppl"] for row in query("SELECT suppl FROM suppl ORDER BY suppl")]
        self.supplier_box = ttk.Combobox(toolbar, values=suppliers, state="readonly", font=FONT, width=18)
        self.supplier_box.current(0)
        self.supplier_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_products())
        self.supplier_box.pack(side="left", padx=(5, 15))

        tk.Label(toolbar, text="Сортировка:", font=FONT, bg=COLOR_BG).pack(side="left")
        self.sort_box = ttk.Combobox(toolbar, values=[SORT_NONE, SORT_ASC, SORT_DESC],
                                     state="readonly", font=FONT, width=22)
        self.sort_box.current(0)
        self.sort_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_products())
        self.sort_box.pack(side="left", padx=5)

        tk.Button(toolbar, text="Заказы", font=FONT, command=self.show_orders).pack(side="right", padx=5)
        if self.user_role == ROLE_ADMIN:
            tk.Button(toolbar, text="Добавить товар", font=FONT, bg=COLOR_ACCENT,
                      command=lambda: self.open_product_form(None)).pack(side="right", padx=5)

    def filter_products(self, products):
        supplier = self.supplier_box.get()
        if supplier != ALL_SUPPLIERS:
            products = [product for product in products if product["suppl"] == supplier]

        words = self.search_var.get().lower().split()
        if words:
            text_fields = ("art", "name", "cat", "descr", "manuf", "suppl", "unit")
            found = []
            for product in products:
                text = " ".join(str(product[field] or "") for field in text_fields).lower()
                if all(word in text for word in words):
                    found.append(product)
            products = found

        if self.sort_box.get() == SORT_ASC:
            products = sorted(products, key=lambda product: product["quant"])
        elif self.sort_box.get() == SORT_DESC:
            products = sorted(products, key=lambda product: product["quant"], reverse=True)
        return products

    def refresh_products(self):
        products = query(PRODUCTS_SQL)
        if self.is_staff():
            products = self.filter_products(products)

        for widget in self.product_list.winfo_children():
            widget.destroy()
        self.product_images = []

        if not products:
            tk.Label(self.product_list, text="Товары не найдены. Измените условия поиска или фильтра.",
                     font=FONT, bg=COLOR_BG).pack(pady=30)
        for product in products:
            self.add_product_card(product)

    def add_product_card(self, product):
        if product["quant"] == 0:
            bg = COLOR_NO_STOCK
        elif product["discount"] > 15:
            bg = COLOR_BIG_DISCOUNT
        else:
            bg = COLOR_BG

        card = tk.Frame(self.product_list, bg=bg, bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=5)

        photo = load_photo(product["photo"], (150, 100))
        self.product_images.append(photo)
        tk.Label(card, image=photo, bg=bg).pack(side="left", padx=10, pady=10)

        tk.Label(card, text=f"Скидка\n{product['discount']}%", font=FONT_TITLE, bg=bg,
                 width=8).pack(side="right", padx=10)

        info = tk.Frame(card, bg=bg)
        info.pack(side="left", fill="both", expand=True, pady=10)
        tk.Label(info, text=f"{product['cat']} | {product['name']}", font=FONT_BOLD, bg=bg).pack(anchor="w")
        tk.Label(info, text=f"Описание товара: {product['descr'] or ''}", font=FONT, bg=bg,
                 wraplength=600, justify="left").pack(anchor="w")
        tk.Label(info, text=f"Производитель: {product['manuf']}", font=FONT, bg=bg).pack(anchor="w")
        tk.Label(info, text=f"Поставщик: {product['suppl']}", font=FONT, bg=bg).pack(anchor="w")

        price_row = tk.Frame(info, bg=bg)
        price_row.pack(anchor="w")
        tk.Label(price_row, text="Цена:", font=FONT, bg=bg).pack(side="left")
        if product["discount"] > 0:
            final_price = product["price"] * (100 - product["discount"]) / 100
            tk.Label(price_row, text=f"{product['price']:.2f} ₽", font=FONT_OLD_PRICE, fg="red",
                     bg=bg).pack(side="left", padx=5)
            tk.Label(price_row, text=f"{final_price:.2f} ₽", font=FONT, fg="black", bg=bg).pack(side="left")
        else:
            tk.Label(price_row, text=f"{product['price']:.2f} ₽", font=FONT, bg=bg).pack(side="left", padx=5)

        tk.Label(info, text=f"Единица измерения: {product['unit']}", font=FONT, bg=bg).pack(anchor="w")
        tk.Label(info, text=f"Количество на складе: {product['quant']}", font=FONT, bg=bg).pack(anchor="w")

        if self.user_role == ROLE_ADMIN:
            bind_click(card, lambda event, product_id=product["id"]: self.open_product_form(product_id))

    def form_is_open(self):
        # Второе окно редактирования открыть нельзя, чтобы случайно не изменить две записи сразу
        if self.form_window is not None and self.form_window.winfo_exists():
            messagebox.showwarning("Окно уже открыто",
                                   "Сначала сохраните изменения или закройте открытое окно редактирования.")
            self.form_window.lift()
            return True
        return False

    def open_product_form(self, product_id):
        if not self.form_is_open():
            self.form_window = ProductForm(self, product_id)

    # ---------- Заказы ----------

    def show_orders(self):
        self.clear_window()
        self.title("Список заказов")
        self.show_header("Список заказов", back_command=self.show_products)
        if self.user_role == ROLE_ADMIN:
            toolbar = tk.Frame(self, bg=COLOR_BG)
            toolbar.pack(fill="x", padx=10, pady=5)
            tk.Button(toolbar, text="Добавить заказ", font=FONT, bg=COLOR_ACCENT,
                      command=lambda: self.open_order_form(None)).pack(side="right")

        area = tk.Frame(self, bg=COLOR_BG)
        area.pack(fill="both", expand=True)
        self.order_list = make_scroll_area(area)
        self.refresh_orders()

    def refresh_orders(self):
        for widget in self.order_list.winfo_children():
            widget.destroy()
        for order in query(ORDERS_SQL):
            self.add_order_card(order)

    def add_order_card(self, order):
        card = tk.Frame(self.order_list, bg=COLOR_BG, bd=1, relief="solid")
        card.pack(fill="x", padx=10, pady=5)

        delivery = tk.Frame(card, bg=COLOR_BG, bd=1, relief="solid")
        delivery.pack(side="right", fill="y", padx=10, pady=10)
        tk.Label(delivery, text="Дата доставки", font=FONT, bg=COLOR_BG).pack(padx=15, pady=(10, 0))
        tk.Label(delivery, text=order["dost_date"], font=FONT_BOLD, bg=COLOR_BG).pack(padx=15, pady=(0, 10))

        info = tk.Frame(card, bg=COLOR_BG)
        info.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        tk.Label(info, text=f"Артикул заказа: {order_items_text(order['id'])}", font=FONT_BOLD,
                 bg=COLOR_BG).pack(anchor="w")
        tk.Label(info, text=f"Статус заказа: {order['status']}", font=FONT, bg=COLOR_BG).pack(anchor="w")
        tk.Label(info, text=f"Адрес пункта выдачи: {order['addr']}", font=FONT, bg=COLOR_BG).pack(anchor="w")
        tk.Label(info, text=f"Дата заказа: {order['zak_date']}", font=FONT, bg=COLOR_BG).pack(anchor="w")

        if self.user_role == ROLE_ADMIN:
            bind_click(card, lambda event, order_id=order["id"]: self.open_order_form(order_id))

    def open_order_form(self, order_id):
        if not self.form_is_open():
            self.form_window = OrderForm(self, order_id)


def order_items_text(order_id):
    rows = query(
        "SELECT tovar.art, zakaz_tovar.quant FROM zakaz_tovar "
        "JOIN tovar ON tovar.id = zakaz_tovar.tovar_id WHERE zakaz_tovar.zak_id = ?",
        (order_id,),
    )
    return ", ".join(f"{row['art']}, {row['quant']}" for row in rows)


class BaseForm(tk.Toplevel):
    """Общее для форм товара и заказа: окно, поля в два столбца, кнопки."""

    def __init__(self, app, title):
        super().__init__(app)
        self.app = app
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.iconbitmap(os.path.join(RES_DIR, "Icon.ico"))
        self.resizable(False, False)
        self.fields = tk.Frame(self, bg=COLOR_BG)
        self.fields.pack(padx=15, pady=15)
        self.row = 0

    def add_field(self, label, widget):
        tk.Label(self.fields, text=label, font=FONT, bg=COLOR_BG).grid(row=self.row, column=0, sticky="nw", pady=3)
        widget.grid(row=self.row, column=1, sticky="w", pady=3, padx=(10, 0))
        self.row += 1
        return widget

    def entry(self, label, value=""):
        widget = tk.Entry(self.fields, font=FONT, width=40)
        widget.insert(0, "" if value is None else str(value))
        return self.add_field(label, widget)

    def combobox(self, label, values, value=""):
        widget = ttk.Combobox(self.fields, values=values, state="readonly", font=FONT, width=38)
        widget.set(value or "")
        return self.add_field(label, widget)

    def add_buttons(self, on_save, on_delete):
        buttons = tk.Frame(self, bg=COLOR_BG)
        buttons.pack(fill="x", padx=15, pady=(0, 15))
        tk.Button(buttons, text="Сохранить", font=FONT, bg=COLOR_ACCENT, command=on_save).pack(side="left")
        tk.Button(buttons, text="Отмена", font=FONT, command=self.destroy).pack(side="left", padx=10)
        if on_delete:
            tk.Button(buttons, text="Удалить", font=FONT, fg="red", command=on_delete).pack(side="right")

    def error(self, title, text):
        messagebox.showerror(title, text, parent=self)


class ProductForm(BaseForm):
    def __init__(self, app, product_id):
        super().__init__(app, "Редактирование товара" if product_id else "Добавление товара")
        self.product_id = product_id
        self.new_photo_path = None
        self.product = query("SELECT * FROM tovar WHERE id = ?", (product_id,))[0] if product_id else None

        self.categories = {row["cat"]: row["id"] for row in query("SELECT id, cat FROM cat")}
        self.manufacturers = {row["manuf"]: row["id"] for row in query("SELECT id, manuf FROM manuf")}
        self.suppliers = {row["suppl"]: row["id"] for row in query("SELECT id, suppl FROM suppl")}

        # ID при добавлении не показываем, при редактировании — только для чтения
        if product_id:
            id_entry = self.entry("ID", product_id)
            id_entry.configure(state="readonly")
        self.art_entry = self.entry("Артикул", self.value("art", ""))
        self.name_entry = self.entry("Наименование", self.value("name", ""))
        self.category_box = self.combobox("Категория", list(self.categories),
                                          self.name_by_id(self.categories, "cat"))
        self.descr_text = tk.Text(self.fields, font=FONT, width=40, height=4, wrap="word")
        self.descr_text.insert("1.0", self.value("descr", "") or "")
        self.add_field("Описание", self.descr_text)
        self.manuf_box = self.combobox("Производитель", list(self.manufacturers),
                                       self.name_by_id(self.manufacturers, "manuf"))
        self.suppl_box = self.combobox("Поставщик", list(self.suppliers),
                                       self.name_by_id(self.suppliers, "suppl"))
        self.price_entry = self.entry("Цена", self.value("price", ""))
        self.unit_entry = self.entry("Единица измерения", self.value("unit", "шт."))
        self.quant_entry = self.entry("Количество на складе", self.value("quant", 0))
        self.discount_entry = self.entry("Скидка, %", self.value("discount", 0))

        photo_frame = tk.Frame(self.fields, bg=COLOR_BG)
        self.photo_label = tk.Label(photo_frame, bg=COLOR_BG)
        self.photo_label.pack(anchor="w")
        tk.Button(photo_frame, text="Выбрать фото", font=FONT, command=self.choose_photo).pack(anchor="w", pady=3)
        self.add_field("Фото", photo_frame)
        self.show_photo(self.value("photo", None))

        self.add_buttons(self.save, self.delete if product_id else None)

    def value(self, field, default):
        """Значение поля редактируемого товара или значение по умолчанию для нового."""
        return default if self.product is None else self.product[field]

    def name_by_id(self, names, field):
        for name, item_id in names.items():
            if item_id == self.value(field, None):
                return name
        return ""

    def show_photo(self, file_name):
        if self.new_photo_path:
            image = Image.open(self.new_photo_path)
            image.thumbnail((300, 200))
            self.photo_image = ImageTk.PhotoImage(image)
        else:
            self.photo_image = load_photo(file_name, (300, 200))
        self.photo_label.configure(image=self.photo_image)

    def choose_photo(self):
        path = filedialog.askopenfilename(parent=self, title="Выберите фото товара",
                                          filetypes=[("Изображения", "*.jpg *.jpeg *.png")])
        if path:
            self.new_photo_path = path
            self.show_photo(None)

    def read_form(self):
        art = self.art_entry.get().strip()
        name = self.name_entry.get().strip()
        if not art or not name:
            raise ValueError("Заполните поля «Артикул» и «Наименование».")
        for box, field in ((self.category_box, "категорию"), (self.manuf_box, "производителя"),
                           (self.suppl_box, "поставщика")):
            if not box.get():
                raise ValueError(f"Выберите {field} из выпадающего списка.")
        try:
            price = round(float(self.price_entry.get().replace(",", ".")), 2)
        except ValueError:
            raise ValueError("Цена должна быть числом, например 1999.99.") from None
        if price < 0:
            raise ValueError("Цена не может быть отрицательной.")
        try:
            quant = int(self.quant_entry.get())
            discount = int(self.discount_entry.get())
        except ValueError:
            raise ValueError("Количество и скидка должны быть целыми числами, например 5.") from None
        if quant < 0:
            raise ValueError("Количество на складе не может быть отрицательным.")
        if not 0 <= discount <= 100:
            raise ValueError("Скидка должна быть от 0 до 100 %.")
        return {
            "art": art, "name": name, "unit": self.unit_entry.get().strip() or "шт.",
            "price": price, "suppl": self.suppliers[self.suppl_box.get()],
            "manuf": self.manufacturers[self.manuf_box.get()], "cat": self.categories[self.category_box.get()],
            "discount": discount, "quant": quant, "descr": self.descr_text.get("1.0", "end").strip(),
            "photo": self.value("photo", None),
        }

    def save_new_photo(self, art):
        image = Image.open(self.new_photo_path)
        image.thumbnail((300, 200))
        file_name = f"{art}_{datetime.now():%Y%m%d%H%M%S}.jpg"
        image.convert("RGB").save(os.path.join(RES_DIR, file_name), "JPEG")
        return file_name

    def delete_photo_file(self, file_name):
        path = os.path.join(RES_DIR, file_name or "")
        if file_name and file_name != PLACEHOLDER and os.path.exists(path):
            os.remove(path)

    def save(self):
        try:
            data = self.read_form()
        except ValueError as error:
            self.error("Ошибка ввода", str(error))
            return

        old_photo = data["photo"]
        try:
            if self.new_photo_path:
                data["photo"] = self.save_new_photo(data["art"])
            columns = ("art", "name", "unit", "price", "suppl", "manuf", "cat", "discount", "quant", "descr", "photo")
            values = [data[column] for column in columns]
            if self.product_id:
                assignments = ", ".join(f"{column} = ?" for column in columns)
                execute(f"UPDATE tovar SET {assignments} WHERE id = ?", values + [self.product_id])
            else:
                execute(f"INSERT INTO tovar ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})", values)
        except sqlite3.IntegrityError:
            self.error("Ошибка сохранения", "Товар с таким артикулом уже существует. Укажите другой артикул.")
            return
        except (sqlite3.Error, OSError) as error:
            self.error("Ошибка сохранения", f"Не удалось сохранить товар: {error}")
            return

        if self.new_photo_path:
            self.delete_photo_file(old_photo)
        messagebox.showinfo("Сохранено", "Данные товара сохранены.", parent=self)
        self.destroy()
        self.app.refresh_products()

    def delete(self):
        orders = query("SELECT COUNT(*) AS n FROM zakaz_tovar WHERE tovar_id = ?", (self.product_id,))[0]["n"]
        if orders:
            self.error("Удаление невозможно",
                       f"Этот товар есть в заказах (заказов: {orders}). Товар, который присутствует в заказе, удалить нельзя.")
            return
        if not messagebox.askyesno("Подтверждение удаления",
                                   f"Удалить товар «{self.product['name']}» ({self.product['art']})?\n"
                                   "Это действие нельзя отменить.", icon="warning", parent=self):
            return
        execute("DELETE FROM tovar WHERE id = ?", (self.product_id,))
        self.delete_photo_file(self.product["photo"])
        messagebox.showinfo("Удалено", "Товар удалён.", parent=self)
        self.destroy()
        self.app.refresh_products()


class OrderForm(BaseForm):
    def __init__(self, app, order_id):
        super().__init__(app, "Редактирование заказа" if order_id else "Добавление заказа")
        self.order_id = order_id
        order = query("SELECT * FROM zakaz WHERE id = ?", (order_id,))[0] if order_id else None

        self.statuses = {row["status"]: row["id"] for row in query("SELECT id, status FROM status")}
        self.addresses = {row["addr"]: row["id"] for row in query("SELECT id, addr FROM pvz ORDER BY id")}
        self.clients = {row["fio"]: row["id"] for row in query("SELECT id, fio FROM users ORDER BY fio")}

        def name_of(names, item_id):
            return next((name for name, value in names.items() if value == item_id), "")

        if order_id:
            id_entry = self.entry("Номер заказа", order_id)
            id_entry.configure(state="readonly")
        self.items_entry = self.entry("Артикул (артикул, кол-во, ...)",
                                      order_items_text(order_id) if order_id else "")
        self.status_box = self.combobox("Статус заказа", list(self.statuses),
                                        name_of(self.statuses, order["status_id"]) if order else "")
        self.address_box = self.combobox("Адрес пункта выдачи", list(self.addresses),
                                         name_of(self.addresses, order["pvz_id"]) if order else "")
        self.client_box = self.combobox("Клиент", list(self.clients),
                                        name_of(self.clients, order["user_id"]) if order else "")
        self.zak_date_entry = self.entry("Дата заказа (ГГГГ-ММ-ДД)", order["zak_date"] if order else "")
        self.dost_date_entry = self.entry("Дата выдачи (ГГГГ-ММ-ДД)", order["dost_date"] if order else "")

        self.add_buttons(self.save, self.delete if order_id else None)

    def read_items(self):
        parts = [part.strip() for part in self.items_entry.get().split(",") if part.strip()]
        if not parts or len(parts) % 2 != 0:
            raise ValueError("Укажите товары парами «артикул, количество», например: А112Т4, 2, F635R4, 1")
        items = {}
        for art, quant_text in zip(parts[::2], parts[1::2]):
            rows = query("SELECT id FROM tovar WHERE art = ?", (art,))
            if not rows:
                raise ValueError(f"Товар с артикулом «{art}» не найден. Проверьте артикул.")
            if not quant_text.isdigit() or int(quant_text) == 0:
                raise ValueError(f"Количество для «{art}» должно быть целым числом больше 0.")
            if rows[0]["id"] in items:
                raise ValueError(f"Артикул «{art}» указан дважды. Объедините количество в одну пару.")
            items[rows[0]["id"]] = int(quant_text)
        return items

    def read_date(self, entry, field):
        try:
            return datetime.strptime(entry.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"{field}: введите существующую дату в формате ГГГГ-ММ-ДД, например 2025-04-20.") from None

    def save(self):
        try:
            items = self.read_items()
            for box, field in ((self.status_box, "статус"), (self.address_box, "адрес пункта выдачи"),
                               (self.client_box, "клиента")):
                if not box.get():
                    raise ValueError(f"Выберите {field} из выпадающего списка.")
            zak_date = self.read_date(self.zak_date_entry, "Дата заказа")
            dost_date = self.read_date(self.dost_date_entry, "Дата выдачи")
            if dost_date < zak_date:
                raise ValueError("Дата выдачи не может быть раньше даты заказа.")
        except ValueError as error:
            self.error("Ошибка ввода", str(error))
            return

        values = (zak_date.isoformat(), dost_date.isoformat(), self.addresses[self.address_box.get()],
                  self.clients[self.client_box.get()], self.statuses[self.status_box.get()])
        try:
            # Заказ и его состав сохраняются в одной транзакции: либо всё, либо ничего
            with connect() as conn:
                if self.order_id:
                    order_id = self.order_id
                    conn.execute("UPDATE zakaz SET zak_date = ?, dost_date = ?, pvz_id = ?, user_id = ?, "
                                 "status_id = ? WHERE id = ?", values + (order_id,))
                    conn.execute("DELETE FROM zakaz_tovar WHERE zak_id = ?", (order_id,))
                else:
                    code = conn.execute("SELECT COALESCE(MAX(code), 900) + 1 FROM zakaz").fetchone()[0]
                    order_id = conn.execute("INSERT INTO zakaz (zak_date, dost_date, pvz_id, user_id, status_id, code) "
                                            "VALUES (?, ?, ?, ?, ?, ?)", values + (code,)).lastrowid
                conn.executemany("INSERT INTO zakaz_tovar (zak_id, tovar_id, quant) VALUES (?, ?, ?)",
                                 [(order_id, tovar_id, quant) for tovar_id, quant in items.items()])
        except sqlite3.Error as error:
            self.error("Ошибка сохранения", f"Не удалось сохранить заказ: {error}")
            return

        messagebox.showinfo("Сохранено", "Заказ сохранён.", parent=self)
        self.destroy()
        self.app.refresh_orders()

    def delete(self):
        if not messagebox.askyesno("Подтверждение удаления",
                                   f"Удалить заказ № {self.order_id}?\nЭто действие нельзя отменить.",
                                   icon="warning", parent=self):
            return
        # Состав заказа удалится сам: в zakaz_tovar стоит ON DELETE CASCADE
        execute("DELETE FROM zakaz WHERE id = ?", (self.order_id,))
        messagebox.showinfo("Удалено", "Заказ удалён.", parent=self)
        self.destroy()
        self.app.refresh_orders()


if __name__ == "__main__":
    app = ShopApp()
    app.mainloop()
