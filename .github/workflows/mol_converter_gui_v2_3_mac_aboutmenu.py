
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Menu
import platform
import sys

# macOS About menu support
def show_about():
    about_window = tk.Toplevel()
    about_window.title("About Mol Converter")
    about_window.geometry("400x300")
    about_window.resizable(False, False)

    tk.Label(about_window, text="Mol Converter v2.3", font=("Helvetica", 16, "bold")).pack(pady=(20, 10))
    tk.Label(about_window, text="Freeware – Free to use and share\nCreated by Edwin Angeli (2025)\nNo warranty or liability assumed.", justify="center").pack(pady=(0, 10))

    link = tk.Label(about_window, text="Connect on LinkedIn", fg="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/edwinangeli/"))

    tk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=(20, 10))

if sys.platform == "darwin":
    root = tk.Tk()
    menubar = Menu(root)
    root.createcommand('tk::mac::ShowAboutDialog', show_about)
    root.config(menu=menubar)
else:
    root = tk.Tk()

import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from rdkit import Chem
from rdkit.Chem import Draw
from tkinterdnd2 import DND_FILES, TkinterDnD
import webbrowser
import platform

CONFIG_FILE = os.path.expanduser("~/.molconverter_config.json")
queued_files = []

# -----------------------------
# Config / File Helpers
# -----------------------------
def load_last_folder():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f).get("last_folder", "")
        except:
            return ""
    return ""

def save_last_folder(folder):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"last_folder": folder}, f)

def update_folder_label():
    current_folder = load_last_folder()
    if current_folder and os.path.exists(current_folder):
        folder_label.config(text=f"Current export folder:\n{current_folder}")
    else:
        folder_label.config(text="No export folder selected yet.")

def choose_export_folder():
    new_folder = filedialog.askdirectory(title="Select Export Folder")
    if new_folder:
        save_last_folder(new_folder)
        update_folder_label()

def get_image_size():
    selection = size_var.get()
    if selection == "Small (256x256)":
        return 256
    elif selection == "Large (1200x1200)":
        return 1200
    else:
        return 600

# -----------------------------
# Queue & File Handling
# -----------------------------
def queue_files(files):
    global queued_files
    new_files = root.tk.splitlist(files)
    added = False
    for f in new_files:
        if f.lower().endswith(".mol") and f not in queued_files:
            queued_files.append(f)
            file_listbox.insert(tk.END, os.path.basename(f))
            added = True
    update_queue_label()
    check_scrollbar()
    if not added:
        progress_label.config(text="No new .mol files added.")

def update_queue_label():
    count = len(queued_files)
    if count == 0:
        queue_label.config(text="No files queued.")
    else:
        queue_label.config(text=f"{count} file(s) queued for conversion.")

def clear_queue():
    global queued_files
    queued_files = []
    file_listbox.delete(0, tk.END)
    update_queue_label()
    check_scrollbar()

def remove_selected_file(event=None):
    """Remove the right-clicked file from queue"""
    global queued_files
    try:
        index = file_listbox.nearest(event.y)
        filename = file_listbox.get(index)
        file_listbox.delete(index)
        for f in queued_files:
            if os.path.basename(f) == filename:
                queued_files.remove(f)
                break
        update_queue_label()
        check_scrollbar()
    except:
        pass

# -----------------------------
# Scrollbar Auto-Hide Logic
# -----------------------------
def check_scrollbar(*args):
    """Show scrollbar only if list exceeds visible rows"""
    if file_listbox.size() > 8:
        if not scrollbar_list.winfo_ismapped():
            scrollbar_list.pack(side=tk.RIGHT, fill=tk.Y)
    else:
        if scrollbar_list.winfo_ismapped():
            scrollbar_list.pack_forget()
    file_listbox.yview(*args)

# -----------------------------
# Conversion Logic
# -----------------------------
def convert_files():
    global queued_files
    if not queued_files:
        messagebox.showwarning("No Files", "Please add some MOL files first.")
        return

    output_dir = load_last_folder()
    if not output_dir or not os.path.exists(output_dir):
        messagebox.showinfo(
            "Select Export Folder",
            "Please select a folder where the files will be saved."
        )
        output_dir = filedialog.askdirectory(title="Select Export Folder")
        if not output_dir:
            return
        save_last_folder(output_dir)
        update_folder_label()

    export_png = var_png.get()
    export_png_trans = var_png_trans.get()
    export_svg = var_svg.get()
    export_pdf = var_pdf.get()

    if not (export_png or export_png_trans or export_svg or export_pdf):
        messagebox.showwarning("No Format Selected", "Please select at least one export format.")
        return

    size = get_image_size()
    converted = 0
    total = len(queued_files)
    progress_label.config(text=f"Processing 0/{total}...")
    root.update_idletasks()

    for idx, mol_file in enumerate(queued_files, start=1):
        mol = Chem.MolFromMolFile(mol_file)
        if mol is None:
            continue

        base = os.path.splitext(os.path.basename(mol_file))[0]

        # --- PNG ---
        if export_png:
            png_file = os.path.join(output_dir, f"{base}.png")
            Draw.MolToFile(mol, png_file, size=(size, size))

        # --- Transparent PNG ---
        if export_png_trans:
            from rdkit.Chem.Draw import rdMolDraw2D
            cairo_drawer = rdMolDraw2D.MolDraw2DCairo(size, size)
            rdMolDraw2D.PrepareAndDrawMolecule(cairo_drawer, mol)
            cairo_drawer.FinishDrawing()
            png_trans_file = os.path.join(output_dir, f"{base}_transparent.png")
            with open(png_trans_file, "wb") as f:
                f.write(cairo_drawer.GetDrawingText())

        # --- SVG ---
        if export_svg:
            drawer = Draw.MolDraw2DSVG(size, size)
            Draw.rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
            drawer.FinishDrawing()
            svg_file = os.path.join(output_dir, f"{base}.svg")
            with open(svg_file, "w") as f:
                f.write(drawer.GetDrawingText())

        # --- PDF (via SVG → PDF using CairoSVG) ---
        if export_pdf:
            from rdkit.Chem.Draw import rdMolDraw2D
            import cairosvg
            svg_drawer = rdMolDraw2D.MolDraw2DSVG(size, size)
            rdMolDraw2D.PrepareAndDrawMolecule(svg_drawer, mol)
            svg_drawer.FinishDrawing()
            svg_text = svg_drawer.GetDrawingText()
            pdf_file = os.path.join(output_dir, f"{base}.pdf")
            cairosvg.svg2pdf(bytestring=svg_text.encode('utf-8'), write_to=pdf_file)

        converted += 1
        progress_label.config(text=f"Processing {idx}/{total}...")
        root.update_idletasks()

    messagebox.showinfo("Conversion Complete", f"{converted} file(s) converted!")
    progress_label.config(text=f"Done! {converted} file(s) converted.")
    os.system(f'open "{output_dir}"' if platform.system() == "Darwin" else f'start "" "{output_dir}"')

    clear_queue()

# -----------------------------
# About Window
# -----------------------------
def show_about():
    about_window = tk.Toplevel(root)
    about_window.title("About Mol Converter")
    about_window.geometry("340x170")
    about_window.resizable(False, False)

    tk.Label(
        about_window,
        text="Mol Converter v2.3",
        font=("Arial", 12, "bold")
    ).pack(pady=5)

    tk.Label(
        about_window,
        text="Freeware – Free to use and share\n"
             "Created by Edwin Angeli (2025)\n"
             "No warranty or liability assumed",
        font=("Arial", 9),
        justify="center"
    ).pack(pady=5)

    link = tk.Label(
        about_window,
        text="Connect on LinkedIn",
        font=("Arial", 9, "underline"),
        fg="blue",
        cursor="hand2"
    )
    link.pack(pady=5)
    link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/edwinangeli/"))

# -----------------------------
# GUI Root (Clean Layout)
# -----------------------------
root = TkinterDnD.Tk()
root.title("Mol Converter v2.3 – Freeware by Edwin Angeli")
root.geometry("600x750")  # Clean fixed size

bg_color = root.cget("bg")

# -----------------------------
# GUI Elements (Mac-Style Clean)
# -----------------------------
label = tk.Label(root, text="Drag & drop your .mol files here\nor click the button to select files", pady=8, bg=bg_color)
label.pack()

btn_select = tk.Button(root, text="Select MOL Files", 
                       command=lambda: queue_files(filedialog.askopenfilenames(
                           title="Select MOL files", filetypes=[("MOL files", "*.mol")])))
btn_select.pack(pady=3)

queue_label = tk.Label(root, text="No files queued.", bg=bg_color)
queue_label.pack(pady=(3, 0))

# Frame for the file queue (no border)
frame_list = tk.Frame(root, bg=bg_color)
frame_list.pack(pady=5, fill="x", padx=10)

# Inner frame with white background for visual highlight
inner_frame = tk.Frame(frame_list, bg="white")
inner_frame.pack(fill="both", expand=True)

# Scrollbar (auto-hide)
scrollbar_list = tk.Scrollbar(inner_frame, orient=tk.VERTICAL)

file_listbox = tk.Listbox(
    inner_frame,
    height=8,
    yscrollcommand=check_scrollbar,
    bg="white",
    highlightthickness=0,
    borderwidth=0
)
scrollbar_list.config(command=file_listbox.yview)

file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# Scrollbar starts hidden
check_scrollbar()

# Bind right-click to remove
file_listbox.bind("<Button-2>", remove_selected_file)  # Mac
file_listbox.bind("<Button-3>", remove_selected_file)  # Windows/Linux

# Bigger right-click hint
hint_label = tk.Label(
    root,
    text="💡 Right-click a file to remove it from the queue",
    font=("Arial", 10),
    fg="gray25",
    bg=bg_color
)
hint_label.pack(pady=(2, 5))

btn_folder = tk.Button(root, text="Change Export Folder", command=choose_export_folder)
btn_folder.pack(pady=3)

btn_convert = tk.Button(root, text="Convert Files", bg="lightgreen", command=convert_files)
btn_convert.pack(pady=3)

btn_clear = tk.Button(root, text="Clear Queue", command=clear_queue)
btn_clear.pack(pady=3)

format_frame = tk.LabelFrame(root, text="Select export formats", padx=10, pady=10, bg=bg_color)
format_frame.pack(pady=5)

var_png = tk.BooleanVar(value=True)
var_png_trans = tk.BooleanVar(value=False)
var_svg = tk.BooleanVar(value=True)
var_pdf = tk.BooleanVar(value=False)

tk.Checkbutton(format_frame, text="PNG", variable=var_png, bg=bg_color).grid(row=0, column=0, sticky="w")
tk.Checkbutton(format_frame, text="Transparent PNG", variable=var_png_trans, bg=bg_color).grid(row=1, column=0, sticky="w")
tk.Checkbutton(format_frame, text="SVG", variable=var_svg, bg=bg_color).grid(row=0, column=1, sticky="w")
tk.Checkbutton(format_frame, text="PDF", variable=var_pdf, bg=bg_color).grid(row=1, column=1, sticky="w")

size_frame = tk.LabelFrame(root, text="Select image size", padx=10, pady=10, bg=bg_color)
size_frame.pack(pady=5)

size_var = tk.StringVar(value="Medium (600x600)")
size_options = ["Small (256x256)", "Medium (600x600)", "Large (1200x1200)"]
tk.OptionMenu(size_frame, size_var, *size_options).pack()

folder_label = tk.Label(root, text="", wraplength=560, justify="center", bg=bg_color)
folder_label.pack(pady=5)

update_folder_label()

progress_label = tk.Label(root, text="", fg="blue", bg=bg_color)
progress_label.pack(pady=5)

btn_about = tk.Button(root, text="About", command=show_about)
btn_about.pack(pady=2)

btn_exit = tk.Button(root, text="Exit", command=root.quit)
btn_exit.pack(pady=3)

# Slightly bigger footer
footer_label = tk.Label(
    root,
    text="Freeware – Created by Edwin Angeli (2025)",
    font=("Arial", 9),
    fg="gray40",
    bg=bg_color
)
footer_label.pack(side=tk.BOTTOM, pady=5)

# Drag & drop
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', lambda e: queue_files(e.data))

root.mainloop()
