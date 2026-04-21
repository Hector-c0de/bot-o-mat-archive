"""Theme/style configuration for the BOT-O-MAT Tkinter GUI."""

import tkinter as tk
from tkinter import ttk


def apply_gui_theme(root: tk.Tk, normal_font, button_font) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg="#0f172a")

    style.configure("TFrame", background="#0f172a")
    style.configure("TLabelframe", background="#0f172a", foreground="#e5e7eb", borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background="#0f172a", foreground="#cbd5e1", font=normal_font)
    style.configure("TLabel", background="#0f172a", foreground="#e5e7eb", font=normal_font)
    style.configure("Header.TLabel", background="#0f172a", foreground="#f8fafc", font=button_font)
    style.configure("Muted.TLabel", background="#0f172a", foreground="#94a3b8", font=normal_font)

    style.configure("Card.TFrame", background="#111827")
    style.configure("CardSelected.TFrame", background="#1f2937")

    style.configure("TEntry", fieldbackground="#111827", foreground="#f8fafc")
    style.configure("TCombobox", fieldbackground="#111827", foreground="#f8fafc")
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", "#111827")],
        foreground=[("readonly", "#f8fafc")],
    )

    style.configure("Primary.TButton", foreground="#FFFFFF", background="#1FB355", padding=(12, 7), font=button_font, borderwidth=0)
    style.map(
        "Primary.TButton",
        foreground=[("disabled", "#D1FAE5"), ("!disabled", "#FFFFFF")],
        background=[("disabled", "#15803D"), ("pressed", "#15803D"), ("active", "#15803D"), ("!disabled", "#1FB355")],
    )

    style.configure("Secondary.TButton", foreground="#042F2E", background="#51DFC9", padding=(12, 7), font=button_font, borderwidth=0)
    style.map(
        "Secondary.TButton",
        foreground=[("disabled", "#0F766E"), ("!disabled", "#042F2E")],
        background=[("disabled", "#2A9D8F"), ("pressed", "#00A68C"), ("active", "#00A68C"), ("!disabled", "#51DFC9")],
    )

    style.configure("Save.TButton", foreground="#000000", background="#FFFFFF", padding=(12, 7), font=button_font, borderwidth=0)
    style.map(
        "Save.TButton",
        foreground=[("disabled", "#4B5563"), ("!disabled", "#000000")],
        background=[("disabled", "#D1D5DB"), ("pressed", "#E5E7EB"), ("active", "#F3F4F6"), ("!disabled", "#FFFFFF")],
    )

    style.configure("Danger.TButton", foreground="#FFFFFF", background="#6B7280", padding=(12, 7), font=button_font, borderwidth=0)
    style.map(
        "Danger.TButton",
        foreground=[
            ("disabled", "#E5E7EB"),
            ("active", "#FFFFFF"),
            ("pressed", "#FFFFFF"),
            ("!disabled", "#FFFFFF"),
        ],
        background=[
            ("disabled", "#374151"),
            ("active", "#4B5563"),
            ("pressed", "#374151"),
            ("!disabled", "#6B7280"),
        ],
    )

    style.configure(
        "Horizontal.TProgressbar",
        background="#51DFC9",
        troughcolor="#1f2937",
        bordercolor="#1f2937",
        lightcolor="#51DFC9",
        darkcolor="#51DFC9",
    )

    return style
