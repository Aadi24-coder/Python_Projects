import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pymongo import MongoClient
import numpy as np

# ============================================
# DATABASE CONNECTION
# ============================================
client = MongoClient("mongodb://localhost:27017/")
db = client["student_db"]
students_collection = db["students"]

# ============================================
# COLOR THEME
# ============================================
BG        = "#1e1e2e"   # dark background
CARD      = "#2a2a3e"   # card/frame background
ACCENT    = "#7c3aed"   # purple accent
GREEN     = "#22c55e"
RED       = "#ef4444"
YELLOW    = "#f59e0b"
TEXT      = "#e2e8f0"
SUBTEXT   = "#94a3b8"
WHITE     = "#ffffff"

# ============================================
# HELPER — Grade from average
# ============================================
def get_grade(average):
    if average >= 90: return "A+"
    elif average >= 75: return "A"
    elif average >= 60: return "B"
    elif average >= 45: return "C"
    else: return "F"

def grade_color(grade):
    return {
        "A+": GREEN, "A": GREEN,
        "B": YELLOW, "C": YELLOW, "F": RED
    }.get(grade, TEXT)

# ============================================
# FUNCTION — Add Student
# ============================================
def add_student():
    name    = name_entry.get().strip()
    roll    = roll_entry.get().strip()
    maths   = maths_entry.get().strip()
    science = science_entry.get().strip()
    english = english_entry.get().strip()

    if not all([name, roll, maths, science, english]):
        messagebox.showerror("Missing Fields", "Please fill in all fields before adding!")
        return

    # Check for duplicate roll number
    if students_collection.find_one({"roll": roll}):
        messagebox.showerror("Duplicate Roll", f"Roll number {roll} already exists!")
        return

    try:
        maths   = int(maths)
        science = int(science)
        english = int(english)
    except ValueError:
        messagebox.showerror("Invalid Input", "Marks must be whole numbers (e.g. 85)!")
        return

    # Validate marks range
    for subject, mark in [("Maths", maths), ("Science", science), ("English", english)]:
        if not (0 <= mark <= 100):
            messagebox.showerror("Invalid Marks", f"{subject} marks must be between 0 and 100!")
            return

    # Calculate average using NumPy
    marks   = np.array([maths, science, english])
    average = round(float(np.mean(marks)), 2)
    grade   = get_grade(average)

    student = {
        "name":    name,
        "roll":    roll,
        "maths":   maths,
        "science": science,
        "english": english,
        "average": average,
        "grade":   grade
    }

    students_collection.insert_one(student)
    messagebox.showinfo("Success", f"✅ {name} added! | Average: {average} | Grade: {grade}")

    # Clear all fields
    for entry in [name_entry, roll_entry, maths_entry, science_entry, english_entry]:
        entry.delete(0, tk.END)

    # Refresh the student table
    load_students()

# ============================================
# FUNCTION — Load / View All Students
# ============================================
def load_students():
    # Clear existing rows
    for row in tree.get_children():
        tree.delete(row)

    records = list(students_collection.find())

    if not records:
        total_label.config(text="Total Students: 0")
        return

    # Use Pandas to build a clean DataFrame
    df = pd.DataFrame(records)[["name", "roll", "maths", "science", "english", "average", "grade"]]
    df.columns = ["Name", "Roll", "Maths", "Science", "English", "Average", "Grade"]

    for _, row in df.iterrows():
        color = grade_color(row["Grade"])
        tree.insert("", tk.END, values=list(row), tags=(row["Grade"],))

    # Color-code rows by grade
    tree.tag_configure("A+", foreground=GREEN)
    tree.tag_configure("A",  foreground=GREEN)
    tree.tag_configure("B",  foreground=YELLOW)
    tree.tag_configure("C",  foreground=YELLOW)
    tree.tag_configure("F",  foreground=RED)

    total_label.config(text=f"Total Students: {len(records)}")

# ============================================
# FUNCTION — Search Student by Roll Number
# ============================================
def search_student():
    roll = search_entry.get().strip()

    if not roll:
        messagebox.showerror("Input Required", "Please enter a Roll Number to search!")
        return

    student = students_collection.find_one({"roll": roll})

    if not student:
        messagebox.showerror("Not Found", f"No student found with Roll Number: {roll}")
        result_label.config(text="No result found.", fg=RED)
        return

    result_text = (
        f"  Name    : {student['name']}\n"
        f"  Roll    : {student['roll']}\n"
        f"  Maths   : {student['maths']}\n"
        f"  Science : {student['science']}\n"
        f"  English : {student['english']}\n"
        f"  Average : {student['average']}\n"
        f"  Grade   : {student['grade']}"
    )
    result_label.config(text=result_text, fg=grade_color(student['grade']))

# ============================================
# FUNCTION — Delete Student by Roll Number
# ============================================
def delete_student():
    roll = search_entry.get().strip()

    if not roll:
        messagebox.showerror("Input Required", "Please enter a Roll Number to delete!")
        return

    student = students_collection.find_one({"roll": roll})

    if not student:
        messagebox.showerror("Not Found", f"No student found with Roll Number: {roll}")
        return

    confirm = messagebox.askyesno(
        "Confirm Delete",
        f"Are you sure you want to delete {student['name']} (Roll: {roll})?"
    )
    if not confirm:
        return

    students_collection.delete_one({"roll": roll})
    messagebox.showinfo("Deleted", f"✅ {student['name']} deleted successfully!")
    result_label.config(text="Student deleted.", fg=SUBTEXT)
    search_entry.delete(0, tk.END)
    load_students()

# ============================================
# FUNCTION — Show Analytics Chart (Matplotlib)
# ============================================
def show_analytics():
    records = list(students_collection.find())

    if len(records) < 1:
        messagebox.showwarning("No Data", "Add at least 1 student to see analytics!")
        return

    df = pd.DataFrame(records)

    # --- Figure setup ---
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.patch.set_facecolor("#1e1e2e")
    fig.suptitle("📊 Student Analytics Dashboard", fontsize=16, color=WHITE, fontweight="bold", y=1.02)

    # ---- Chart 1: Bar chart — Average marks per student ----
    ax1 = axes[0]
    ax1.set_facecolor(CARD)

    colors = [grade_color(g) for g in df["grade"]]
    bars   = ax1.bar(df["name"], df["average"], color=colors, edgecolor="#1e1e2e", linewidth=0.8)

    # Add value labels on bars
    for bar, avg in zip(bars, df["average"]):
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{avg:.1f}",
            ha="center", va="bottom",
            color=WHITE, fontsize=9, fontweight="bold"
        )

    ax1.set_title("Average Marks per Student", color=WHITE, fontsize=12, pad=10)
    ax1.set_xlabel("Student Name", color=SUBTEXT, fontsize=10)
    ax1.set_ylabel("Average Marks", color=SUBTEXT, fontsize=10)
    ax1.set_ylim(0, 110)
    ax1.tick_params(colors=TEXT, rotation=20)
    ax1.spines[:].set_color("#3a3a5e")
    for spine in ax1.spines.values():
        spine.set_color("#3a3a5e")
    ax1.yaxis.label.set_color(SUBTEXT)
    ax1.xaxis.label.set_color(SUBTEXT)

    # ---- Chart 2: Subject-wise class average ----
    ax2 = axes[1]
    ax2.set_facecolor(CARD)

    subjects      = ["Maths", "Science", "English"]
    subject_avgs  = [df["maths"].mean(), df["science"].mean(), df["english"].mean()]
    subject_colors = [ACCENT, "#06b6d4", "#f97316"]

    bars2 = ax2.bar(subjects, subject_avgs, color=subject_colors, edgecolor="#1e1e2e", linewidth=0.8)

    for bar, avg in zip(bars2, subject_avgs):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{avg:.1f}",
            ha="center", va="bottom",
            color=WHITE, fontsize=10, fontweight="bold"
        )

    ax2.set_title("Subject-wise Class Average", color=WHITE, fontsize=12, pad=10)
    ax2.set_xlabel("Subject", color=SUBTEXT, fontsize=10)
    ax2.set_ylabel("Average Marks", color=SUBTEXT, fontsize=10)
    ax2.set_ylim(0, 110)
    ax2.tick_params(colors=TEXT)
    for spine in ax2.spines.values():
        spine.set_color("#3a3a5e")

    plt.tight_layout()
    plt.show()

# ============================================
# MAIN WINDOW
# ============================================
window = tk.Tk()
window.title("Student Result Management System")
window.geometry("1000x700")
window.configure(bg=BG)
window.resizable(True, True)

# ---- Heading ----
heading = tk.Label(
    window,
    text="🎓  Student Result Management System",
    font=("Courier", 20, "bold"),
    bg=BG, fg=WHITE
)
heading.pack(pady=(20, 5))

subtitle = tk.Label(
    window,
    text="Powered by Python • MongoDB • NumPy • Pandas • Matplotlib • Tkinter",
    font=("Courier", 9),
    bg=BG, fg=SUBTEXT
)
subtitle.pack(pady=(0, 15))

# ============================================
# TAB CONTROL — organises sections cleanly
# ============================================
style = ttk.Style()
style.theme_use("clam")
style.configure("TNotebook",          background=BG,   borderwidth=0)
style.configure("TNotebook.Tab",      background=CARD, foreground=TEXT,
                padding=[18, 8],      font=("Courier", 11, "bold"))
style.map("TNotebook.Tab",
          background=[("selected", ACCENT)],
          foreground=[("selected", WHITE)])
style.configure("TFrame", background=BG)

notebook = ttk.Notebook(window)
notebook.pack(fill="both", expand=True, padx=20, pady=5)

# ============================================
# TAB 1 — ADD STUDENT
# ============================================
tab_add = ttk.Frame(notebook)
notebook.add(tab_add, text="  ➕  Add Student  ")

form_card = tk.Frame(tab_add, bg=CARD, padx=40, pady=30, relief="flat")
form_card.pack(pady=30)

def make_field(frame, label_text, row):
    tk.Label(
        frame, text=label_text,
        font=("Courier", 12), bg=CARD, fg=TEXT, anchor="w"
    ).grid(row=row, column=0, padx=10, pady=10, sticky="w")

    entry = tk.Entry(
        frame, font=("Courier", 12), width=28,
        bg="#1e1e2e", fg=WHITE,
        insertbackground=WHITE,
        relief="flat", bd=5
    )
    entry.grid(row=row, column=1, padx=10, pady=10)
    return entry

name_entry    = make_field(form_card, "Student Name  :", 0)
roll_entry    = make_field(form_card, "Roll Number   :", 1)
maths_entry   = make_field(form_card, "Maths Marks   :", 2)
science_entry = make_field(form_card, "Science Marks :", 3)
english_entry = make_field(form_card, "English Marks :", 4)

add_btn = tk.Button(
    form_card,
    text="  ➕  Add Student  ",
    font=("Courier", 12, "bold"),
    bg=ACCENT, fg=WHITE,
    relief="flat", cursor="hand2",
    padx=20, pady=10,
    command=add_student
)
add_btn.grid(row=5, column=0, columnspan=2, pady=20)

# Grade legend
legend = tk.Label(
    tab_add,
    text="Grade Scale:  A+ ≥ 90   |   A ≥ 75   |   B ≥ 60   |   C ≥ 45   |   F < 45",
    font=("Courier", 10), bg=BG, fg=SUBTEXT
)
legend.pack(pady=5)

# ============================================
# TAB 2 — VIEW ALL STUDENTS
# ============================================
tab_view = ttk.Frame(notebook)
notebook.add(tab_view, text="  📋  View Students  ")

# Table header bar
header_bar = tk.Frame(tab_view, bg=BG)
header_bar.pack(fill="x", padx=10, pady=(10, 5))

total_label = tk.Label(
    header_bar, text="Total Students: 0",
    font=("Courier", 11, "bold"), bg=BG, fg=ACCENT
)
total_label.pack(side="left")

refresh_btn = tk.Button(
    header_bar, text="🔄 Refresh",
    font=("Courier", 10), bg=CARD, fg=TEXT,
    relief="flat", cursor="hand2", padx=10, pady=4,
    command=load_students
)
refresh_btn.pack(side="right")

# Treeview (table)
cols = ("Name", "Roll", "Maths", "Science", "English", "Average", "Grade")

tree_frame = tk.Frame(tab_view, bg=BG)
tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
scrollbar.pack(side="right", fill="y")

style.configure("Treeview",
    background=CARD, foreground=TEXT,
    fieldbackground=CARD, rowheight=30,
    font=("Courier", 10)
)
style.configure("Treeview.Heading",
    background=ACCENT, foreground=WHITE,
    font=("Courier", 11, "bold"), relief="flat"
)
style.map("Treeview", background=[("selected", "#3a3a6e")])

tree = ttk.Treeview(
    tree_frame, columns=cols, show="headings",
    yscrollcommand=scrollbar.set, selectmode="browse"
)
scrollbar.config(command=tree.yview)

col_widths = {"Name": 160, "Roll": 80, "Maths": 80, "Science": 90, "English": 90, "Average": 90, "Grade": 70}
for col in cols:
    tree.heading(col, text=col)
    tree.column(col, width=col_widths[col], anchor="center")

tree.pack(fill="both", expand=True)

# Analytics button below table
analytics_btn = tk.Button(
    tab_view, text="  📊  Show Analytics Chart  ",
    font=("Courier", 11, "bold"),
    bg="#06b6d4", fg=WHITE,
    relief="flat", cursor="hand2",
    padx=20, pady=8,
    command=show_analytics
)
analytics_btn.pack(pady=12)

# ============================================
# TAB 3 — SEARCH & DELETE
# ============================================
tab_search = ttk.Frame(notebook)
notebook.add(tab_search, text="  🔍  Search / Delete  ")

search_card = tk.Frame(tab_search, bg=CARD, padx=40, pady=30)
search_card.pack(pady=30)

tk.Label(
    search_card, text="Enter Roll Number:",
    font=("Courier", 13), bg=CARD, fg=TEXT
).grid(row=0, column=0, padx=10, pady=10)

search_entry = tk.Entry(
    search_card, font=("Courier", 13), width=20,
    bg=BG, fg=WHITE, insertbackground=WHITE,
    relief="flat", bd=5
)
search_entry.grid(row=0, column=1, padx=10, pady=10)

btn_frame = tk.Frame(search_card, bg=CARD)
btn_frame.grid(row=1, column=0, columnspan=2, pady=15)

tk.Button(
    btn_frame, text="🔍  Search",
    font=("Courier", 11, "bold"),
    bg=ACCENT, fg=WHITE, relief="flat",
    cursor="hand2", padx=16, pady=8,
    command=search_student
).pack(side="left", padx=10)

tk.Button(
    btn_frame, text="🗑️  Delete",
    font=("Courier", 11, "bold"),
    bg=RED, fg=WHITE, relief="flat",
    cursor="hand2", padx=16, pady=8,
    command=delete_student
).pack(side="left", padx=10)

result_label = tk.Label(
    search_card, text="",
    font=("Courier", 12), bg=CARD, fg=TEXT,
    justify="left"
)
result_label.grid(row=2, column=0, columnspan=2, pady=15)

# ============================================
# LOAD DATA ON STARTUP & LAUNCH
# ============================================
load_students()
window.mainloop()