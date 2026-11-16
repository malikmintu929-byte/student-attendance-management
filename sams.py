import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# DATABASE
conn = sqlite3.connect("attendance.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS attendance(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    roll TEXT,
    name TEXT,
    status TEXT,
    date TEXT
)
""")
conn.commit()

# MAIN WINDOW
root = tk.Tk()
root.title("Student Attendance Management System")
root.geometry("1100x850")
root.configure(bg="#f0f4f8")

tk.Label(
    root, text="STUDENT ATTENDANCE MANAGEMENT SYSTEM",
    font=("Arial", 20, "bold"),
    bg="#17365d", fg="white", pady=15
).pack(fill="x")

# INPUT FORM
form = tk.LabelFrame(
    root, text="Add / Update Attendance",
    font=("Arial", 12, "bold"), bg="#f0f4f8",
    padx=15, pady=12
)
form.pack(fill="x", padx=20, pady=10)

tk.Label(form, text="Roll Number:", bg="#f0f4f8").grid(row=0, column=0, padx=8, pady=8)
roll_entry = tk.Entry(form, width=20)
roll_entry.grid(row=0, column=1)

tk.Label(form, text="Student Name:", bg="#f0f4f8").grid(row=0, column=2, padx=8)
name_entry = tk.Entry(form, width=22)
name_entry.grid(row=0, column=3)

tk.Label(form, text="Status:", bg="#f0f4f8").grid(row=1, column=0, padx=8, pady=8)
status_box = ttk.Combobox(
    form, values=["Present", "Absent"],
    state="readonly", width=17
)
status_box.set("Present")
status_box.grid(row=1, column=1)

tk.Label(form, text="Date (YYYY-MM-DD):", bg="#f0f4f8").grid(row=1, column=2, padx=8)
date_entry = tk.Entry(form, width=22)
date_entry.grid(row=1, column=3)
date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

# ATTENDANCE TABLE
table_frame = tk.LabelFrame(
    root, text="Attendance History",
    font=("Arial", 12, "bold"), bg="#f0f4f8"
)
table_frame.pack(fill="x", padx=20, pady=10)

columns = ("ID", "Roll", "Name", "Status", "Date")
table = ttk.Treeview(
    table_frame, columns=columns,
    show="headings", height=7
)

for col in columns:
    table.heading(col, text=col)
    table.column(col, width=180, anchor="center")

table.column("ID", width=60)

scroll = ttk.Scrollbar(
    table_frame, orient="vertical", command=table.yview
)
table.configure(yscrollcommand=scroll.set)
table.pack(side="left", fill="x", expand=True)
scroll.pack(side="right", fill="y")

# GRAPH DASHBOARD
dashboard = tk.LabelFrame(
    root, text="ATTENDANCE ANALYSIS DASHBOARD",
    font=("Arial", 13, "bold"), bg="white"
)
dashboard.pack(fill="both", expand=True, padx=20, pady=10)

fig = Figure(figsize=(10, 3.5), dpi=100)
fig.patch.set_facecolor("white")
ax1 = fig.add_subplot(121)
ax2 = fig.add_subplot(122)

canvas = FigureCanvasTkAgg(fig, master=dashboard)
canvas.get_tk_widget().pack(fill="both", expand=True)

# CLEAR INPUTS
def clear_fields():
    roll_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    status_box.set("Present")
    date_entry.delete(0, tk.END)
    date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
    table.selection_remove(table.selection())

# REFRESH TABLE AND GRAPHS
def refresh():

    for item in table.get_children():
        table.delete(item)

    cur.execute("SELECT * FROM attendance ORDER BY id DESC")
    rows = cur.fetchall()

    month = datetime.now().strftime("%Y-%m")
    present = 0
    absent = 0

    for row in rows:
        table.insert("", "end", values=row)

        if row[4].startswith(month):
            if row[3] == "Present":
                present += 1
            else:
                absent += 1

    # PIE CHART
    ax1.clear()
    ax2.clear()

    if present + absent > 0:
        ax1.pie(
            [present, absent],
            labels=["Present", "Absent"],
            autopct="%1.1f%%",
            colors=["#198754", "#dc3545"],
            startangle=90
        )
    else:
        ax1.text(0.5, 0.5, "No Attendance Data",
                 ha="center", va="center")

    ax1.set_title("Present vs Absent")

    # BAR GRAPH
    bars = ax2.bar(
        ["Present", "Absent"],
        [present, absent],
        color=["#198754", "#dc3545"],
        width=0.5
    )

    ax2.set_title("Monthly Attendance")
    ax2.set_ylabel("Number of Records")
    ax2.set_ylim(0, max(present, absent, 1) * 1.25)
    ax2.grid(axis="y", alpha=0.3)

    for bar, value in zip(bars, [present, absent]):
        ax2.text(
            bar.get_x() + bar.get_width()/2,
            bar.get_height(),
            str(value), ha="center", va="bottom"
        )

    fig.tight_layout()
    canvas.draw_idle()

# ADD ATTENDANCE
def add_attendance():
    roll = roll_entry.get().strip()
    name = name_entry.get().strip()
    status = status_box.get()
    date = date_entry.get().strip()

    if not roll or not name:
        messagebox.showerror("Error", "Enter roll and student name")
        return

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Error", "Enter date as YYYY-MM-DD")
        return

    cur.execute("""
        INSERT INTO attendance (roll, name, status, date)
        VALUES (?, ?, ?, ?)
    """, (roll, name, status, date))

    conn.commit()
    refresh()
    clear_fields()
    messagebox.showinfo("Success", "Attendance added!")

# SELECT RECORD FOR EDITING
def select_record(event):
    selected = table.selection()
    if not selected:
        return

    data = table.item(selected[0], "values")

    clear_fields()
    roll_entry.insert(0, data[1])
    name_entry.insert(0, data[2])
    status_box.set(data[3])
    date_entry.delete(0, tk.END)
    date_entry.insert(0, data[4])

table.bind("<<TreeviewSelect>>", select_record)

# UPDATE ATTENDANCE
def update_attendance():
    selected = table.selection()

    if not selected:
        messagebox.showwarning("Warning", "Select a record first")
        return

    data = table.item(selected[0], "values")
    roll = roll_entry.get().strip()
    name = name_entry.get().strip()
    status = status_box.get()
    date = date_entry.get().strip()

    if not roll or not name:
        messagebox.showerror("Error", "Fill all fields")
        return

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        messagebox.showerror("Error", "Invalid date")
        return

    cur.execute("""
        UPDATE attendance
        SET roll=?, name=?, status=?, date=?
        WHERE id=?
    """, (roll, name, status, date, data[0]))

    conn.commit()
    refresh()
    clear_fields()
    messagebox.showinfo("Success", "Attendance updated!")

# DELETE ATTENDANCE
def delete_attendance():
    selected = table.selection()

    if not selected:
        messagebox.showwarning("Warning", "Select a record first")
        return

    if messagebox.askyesno("Confirm", "Delete selected attendance?"):
        data = table.item(selected[0], "values")
        cur.execute("DELETE FROM attendance WHERE id=?", (data[0],))
        conn.commit()
        refresh()
        clear_fields()
        messagebox.showinfo("Success", "Record deleted!")

# BUTTONS
buttons = tk.Frame(root, bg="#f0f4f8")
buttons.pack(pady=8)

tk.Button(
    buttons, text="Add Attendance",
    command=add_attendance, bg="#198754",
    fg="white", padx=15
).pack(side="left", padx=5)

tk.Button(
    buttons, text="Update",
    command=update_attendance, bg="#17365d",
    fg="white", padx=15
).pack(side="left", padx=5)

tk.Button(
    buttons, text="Delete",
    command=delete_attendance, bg="#cc0000",
    fg="white", padx=15
).pack(side="left", padx=5)

tk.Button(
    buttons, text="Clear",
    command=clear_fields, padx=15
).pack(side="left", padx=5)

def close_app():
    conn.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close_app)

refresh()
root.mainloop()