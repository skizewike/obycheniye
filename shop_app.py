import sqlite3
import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

DB_PATH = "shop.db"
RES_DIR = "import"

# Стиль: заменить на значения из руководства по стилю (Приложение 3)
FONT = ("Times New Roman", 12)
FONT_TITLE = ("Times New Roman", 18, "bold")
COLOR_BG = "#FFFFFF"
COLOR_ACCENT = "#00FA9A"


def query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(sql, params).fetchall()


class ShopApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("1000x650")
        self.configure(bg=COLOR_BG)
        self.iconbitmap(f"{RES_DIR}/Icon.ico")
        # tkinter не хранит картинку сам: без ссылки она исчезнет с экрана
        self.logo = ImageTk.PhotoImage(Image.open(f"{RES_DIR}/Icon.png").resize((80, 80)))
        self.user_fio = None
        self.user_role = None
        self.show_login()

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

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

        self.user_fio, self.user_role = rows[0]
        self.unbind("<Return>")
        self.show_products()

    def login_as_guest(self):
        self.user_fio = "Гость"
        self.user_role = "Гость"
        self.unbind("<Return>")
        self.show_products()

    def show_header(self, title):
        header = tk.Frame(self, bg=COLOR_ACCENT)
        header.pack(fill="x")
        tk.Label(header, image=self.logo, bg=COLOR_ACCENT).pack(side="left", padx=5, pady=5)
        tk.Label(header, text=title, font=FONT_TITLE, bg=COLOR_ACCENT).pack(side="left", padx=10)
        tk.Button(header, text="Выход", font=FONT, command=self.show_login).pack(side="right", padx=10)
        tk.Label(header, text=f"{self.user_fio} ({self.user_role})", font=FONT,
                 bg=COLOR_ACCENT).pack(side="right", padx=10)

    def show_products(self):
        self.clear_window()
        self.title("Список товаров")
        self.show_header("Список товаров")
        # Список товаров — следующий шаг
        tk.Label(self, text="Здесь будет список товаров", font=FONT, bg=COLOR_BG).pack(pady=40)


if __name__ == "__main__":
    app = ShopApp()
    app.mainloop()
