import tkinter as tk
from tkinter import messagebox
import keyboard          # pip install keyboard
import hashlib
import os
import datetime
from pathlib import Path

# ================= НАСТРОЙКИ =================
MASTER_PASSWORD = "смени_меня_123"     # ОБЯЗАТЕЛЬНО поменяй!
HOTKEY = "ctrl+alt+l"
LOG_FILE = Path("winlocker_log.txt")
# =============================================

def hash_password(pw: str, salt: bytes) -> str:
    return hashlib.sha256(salt + pw.encode()).hexdigest()

# Первый запуск: создаём файл с хешем пароля
CRED_FILE = Path("winlocker_cred.txt")
if not CRED_FILE.exists():
    import getpass
    print("Первый запуск. Задай пароль для разблокировки.")
    pw1 = getpass.getpass("Пароль: ")
    pw2 = getpass.getpass("Повтори: ")
    if pw1 != pw2 or not pw1:
        print("Пароли не совпадают или пусты. Выход.")
        raise SystemExit(1)
    salt = os.urandom(16)
    with open(CRED_FILE, "w") as f:
        f.write(salt.hex() + "\n" + hash_password(pw1, salt))
    print("Пароль сохранён.")

with open(CRED_FILE) as f:
    salt_hex, stored_hash = f.read().splitlines()
SALT = bytes.fromhex(salt_hex)

def log_event(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now().isoformat()}  {text}\n")

def check_password(pw: str) -> bool:
    if pw == MASTER_PASSWORD:
        log_event("ВХОД: мастер-пароль")
        return True
    if hash_password(pw, SALT) == stored_hash:
        log_event("ВХОД: обычный пароль")
        return True
    log_event("ОТКАЗ: неверный пароль")
    return False

def show_lock_screen():
    lock = tk.Tk()
    lock.attributes("-fullscreen", True)
    lock.attributes("-topmost", True)
    lock.configure(bg="black")
    lock.protocol("WM_DELETE_WINDOW", lambda: None)  # нельзя закрыть крестиком

    # перехват Alt+F4 и т.п. — окно не закроется штатно
    lock.bind("<Alt-F4>", lambda e: "break")

    tk.Label(lock, text="ЭКРАН ЗАБЛОКИРОВАН", fg="white", bg="black",
             font=("Arial", 32, "bold")).pack(pady=(120, 30))

    pw_var = tk.StringVar()
    entry = tk.Entry(lock, textvariable=pw_var, show="*", font=("Arial", 20),
                     justify="center")
    entry.pack(pady=10)
    entry.focus_force()

    attempts = {"n": 0}

    def try_unlock(event=None):
        if check_password(pw_var.get()):
            log_event("ЭКРАН РАЗБЛОКИРОВАН")
            lock.destroy()
        else:
            attempts["n"] += 1
            pw_var.set("")
            msg = f"Неверный пароль. Попыток: {attempts['n']}"
            status.config(text=msg)
            if attempts["n"] >= 5:
                status.config(text="Слишком много попыток. Подожди 10 секунд.")
                lock.after(10000, lambda: (attempts.update(n=0),
                                           status.config(text="Введи пароль")))

    entry.bind("<Return>", try_unlock)

    tk.Button(lock, text="Разблокировать", command=try_unlock,
              font=("Arial", 16)).pack(pady=10)

    status = tk.Label(lock, text="Введи пароль", fg="gray", bg="black",
                      font=("Arial", 14))
    status.pack(pady=20)

    lock.mainloop()

def on_hotkey():
    # не открывать второй экран, если уже открыт
    if not getattr(on_hotkey, "active", False):
        on_hotkey.active = True
        try:
            show_lock_screen()
        finally:
            on_hotkey.active = False

if __name__ == "__main__":
    print(f"Готово. Нажми {HOTKEY.upper()} для блокировки. Ctrl+C — выход.")
    log_event("ПРОГРАММА ЗАПУЩЕНА")
    keyboard.add_hotkey(HOTKEY, on_hotkey)
    keyboard.wait()  # держим программу живой