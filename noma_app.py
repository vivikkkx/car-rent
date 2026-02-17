import sqlite3 as db  
import tkinter as tk  
from tkinter import ttk, messagebox  

DB_PATH = "E:/2025_2026/12_klase/Matule/auto_noma.db" 
conn = db.connect(DB_PATH) 
cursor = conn.cursor() 

AUTO_TIPI = ["Econom", "Comfort", "Business"]  # Saraksts ar iepriekš definētiem auto tipiem

def fetch_ids(sql):  # Funkcija ID iegūšanai no datubāzes pēc SQL vaicājuma.
    cursor.execute(sql)
    return [str(r[0]) for r in cursor.fetchall()]

# Iegūst lietotāja definēto tabulu sarakstu no datubāzes
cursor.execute("""
SELECT name FROM sqlite_master
WHERE type='table' AND name NOT LIKE 'sqlite_%'
ORDER BY name
""")
tables = [r[0] for r in cursor.fetchall()]

root = tk.Tk()
root.title("Auto Noma")
root.geometry("1000x720")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
style.configure("TButton", padding=6)
style.configure("TLabel", font=("Segoe UI", 10))


top = ttk.Frame(root, padding=10)
top.pack(fill="x")

ttk.Label(top, text="Tabula:").pack(side="left")
table_var = tk.StringVar(value=tables[0])
table_combo = ttk.Combobox(
    top, values=tables, textvariable=table_var,
    state="readonly", width=25
)
table_combo.pack(side="left", padx=8)


search_box = ttk.LabelFrame(top, text="Klienta meklēšana", padding=6)
search_box.pack(side="left", padx=20)
search_entry = ttk.Entry(search_box, width=20)
search_entry.pack(side="left", padx=5)


mid = ttk.Frame(root, padding=(10, 0))
mid.pack(fill="both", expand=True)

tree = ttk.Treeview(mid, show="headings")
tree.pack(side="left", fill="both", expand=True)

scroll = ttk.Scrollbar(mid, orient="vertical", command=tree.yview)
scroll.pack(side="right", fill="y")
tree.configure(yscrollcommand=scroll.set)


bottom = ttk.Frame(root, padding=10)
bottom.pack(fill="x")

form = ttk.LabelFrame(bottom, text="Datu ievade", padding=10)
form.pack(fill="x")

entries = {}
columns = []

def load_table(*_):  # Funkcija tabulas datu ielādei un attēlošanai. Iegūst kolonnas, attēlo datus, veido dinamisku ievades formu
    global columns, entries
    table = table_var.get()

    cursor.execute(f'PRAGMA table_info("{table}")')
    columns = [c[1] for c in cursor.fetchall()]

    tree["columns"] = columns
    for c in columns:
        tree.heading(c, text=c)
        tree.column(c, width=140)

    tree.delete(*tree.get_children())
    cursor.execute(f'SELECT * FROM "{table}"')
    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

    for w in form.winfo_children():
        w.destroy()
    entries.clear()

    for i, c in enumerate(columns):
        ttk.Label(form, text=c).grid(row=i//3, column=(i%3)*2, sticky="w", padx=5, pady=4)

        if c == "auto_tips":
            cb = ttk.Combobox(form, values=AUTO_TIPI, state="readonly")
            cb.current(0)
            cb.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = cb

        elif table == "Nomas" and c == "klients_id":
            cb = ttk.Combobox(form, values=fetch_ids("SELECT klients_id FROM Klienti"), state="readonly")
            cb.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = cb

        elif table == "Nomas" and c == "auto_id":
            cb = ttk.Combobox(form, values=fetch_ids("SELECT auto_id FROM Automašīnas"), state="readonly")
            cb.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = cb

            def on_auto_select(event):  # Iekšējā funkcija notikumu apstrādei auto atlasei. Automātiski aizpilda saistītos laukus
                auto = cb.get()
                if not auto:
                    return
                cursor.execute("""
                    SELECT tips_id, auto_tips
                    FROM Automašīnas
                    WHERE auto_id = ?
                """, (auto,))
                res = cursor.fetchone()
                if res:
                    tips_val, auto_tips_val = res
                    if "tips_id" in entries:
                        entries["tips_id"].set(str(tips_val))
                    if "auto_tips" in entries:
                        entries["auto_tips"].set(auto_tips_val)

            cb.bind("<<ComboboxSelected>>", on_auto_select)
            entries[c] = cb

        elif table == "Nomas" and c == "tips_id":
            cb = ttk.Combobox(form, values=fetch_ids('SELECT tips_id FROM "Auto tipi"'), state="readonly")
            cb.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = cb

        elif table == "Nomas" and c == "statuss":
            cb = ttk.Combobox(
                form,
                values=["aktīva", "beigusies"],
                state="readonly",
                width=27
            )
            cb.current(0)
            cb.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = cb

        else:
            e = ttk.Entry(form)
            e.grid(row=i//3, column=(i%3)*2+1, padx=5)
            entries[c] = e

def search_client():  # Funkcija klientu meklēšanai tabulā "Nomas". 
    name = search_entry.get().strip()
    if not name:
        return

    if table_var.get() != "Nomas":
        messagebox.showinfo("Info", "Meklēšana darbojas tikai tabulai 'Nomas'")
        return

    cols = [
        "noma_id",
        "vards",
        "uzvards",
        "sakuma_data",
        "beigu_data",
        "statuss",
        "klients_id",
        "auto_id",
        "tips_id"
    ]

    tree["columns"] = cols
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, width=130)

    tree.delete(*tree.get_children())

    cursor.execute("""
        SELECT
            N.noma_id,
            K.vards,
            K.uzvards,
            N.sakuma_data,
            N.beigu_data,
            N.statuss,
            N.klients_id,
            N.auto_id,
            N.tips_id
        FROM Nomas N
        JOIN Klienti K ON N.klients_id = K.klients_id
        WHERE K.vards LIKE ? OR K.uzvards LIKE ?
    """, (f"%{name}%", f"%{name}%"))

    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

def add_row():  # Funkcija jaunas rindas pievienošanai izvēlētajai tabulai. 
    table = table_var.get()
    values = []

    for c in columns:
        if table == "Nomas" and c == "beigu_data":
            v = entries[c].get().strip()
            values.append("—" if v == "" else v)

        elif table == "Nomas" and c == "statuss":
            beigu = entries["beigu_data"].get().strip()
            values.append(entries[c].get())  

        else:
            v = entries[c].get().strip()
            values.append(None if v == "" else v)

    try:
        cursor.execute(
            f'INSERT INTO "{table}" VALUES ({",".join("?"*len(values))})',
            values
        )
        conn.commit()
        load_table()
    except Exception as e:
        messagebox.showerror("Kļūda", str(e))

btns = ttk.Frame(bottom)
btns.pack(pady=8)

ttk.Button(btns, text="Atjaunot", command=load_table).pack(side="left")
ttk.Button(btns, text="Pievienot", command=add_row).pack(side="left", padx=8)
ttk.Button(search_box, text="Meklēt", command=search_client).pack(side="left", padx=5)

table_combo.bind("<<ComboboxSelected>>", load_table)
load_table()

root.mainloop()
conn.close()


