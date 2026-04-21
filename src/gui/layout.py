"""Layout builder for the BOT-O-MAT Tkinter GUI.

Creates and assigns all widgets onto the provided app instance.
"""

import tkinter as tk
from tkinter import ttk


def build_gui_layout(app, robot_types):
    container = ttk.Frame(app.root, padding=12)
    container.grid(sticky="nsew")
    app.root.columnconfigure(0, weight=1)
    app.root.rowconfigure(0, weight=1)

    container.columnconfigure(0, weight=0, minsize=300)
    container.columnconfigure(1, weight=1)
    container.rowconfigure(0, weight=1)

    left = ttk.LabelFrame(container, text="Robots", padding=10)
    center = ttk.LabelFrame(container, text="Mission Command", padding=10)

    left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    center.grid(row=0, column=1, sticky="nsew")

    left.columnconfigure(0, weight=1)
    left.rowconfigure(5, weight=1)

    ttk.Label(left, text="Robot Name").grid(row=0, column=0, sticky="w")
    app.name_var = tk.StringVar()
    app.name_entry = ttk.Entry(left, textvariable=app.name_var)
    app.name_entry.grid(row=1, column=0, sticky="ew", pady=(2, 8))

    ttk.Label(left, text="Robot Type").grid(row=2, column=0, sticky="w")
    type_values = list(robot_types.values()) if isinstance(robot_types, dict) else list(robot_types)
    app.type_var = tk.StringVar(value=type_values[0] if type_values else "")
    app.type_combo = ttk.Combobox(left, textvariable=app.type_var, values=type_values, state="readonly")
    app.type_combo.grid(row=3, column=0, sticky="ew", pady=(1, 8))

    left_btns = ttk.Frame(left)
    left_btns.grid(row=4, column=0, sticky="ew", pady=(0, 6))
    left_btns.columnconfigure(0, weight=1)
    left_btns.columnconfigure(1, weight=1)
    left_btns.rowconfigure(0, weight=1)
    left_btns.rowconfigure(1, weight=1)

    app.add_robot_button = ttk.Button(left_btns, text="ADD", command=app.add_robot, style="Secondary.TButton")
    app.add_robot_button.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))

    app.update_robot_button = ttk.Button(left_btns, text="EDIT", command=app.update_selected_robot, style="Secondary.TButton")
    app.update_robot_button.grid(row=1, column=0, sticky="ew", padx=(0, 2))

    app.remove_robot_button = ttk.Button(left_btns, text="REMOVE", command=app.remove_selected_robot, style="Danger.TButton")
    app.remove_robot_button.grid(row=1, column=1, sticky="ew", padx=(2, 0))

    cards_container = ttk.Frame(left)
    cards_container.grid(row=5, column=0, sticky="nsew")
    cards_container.columnconfigure(0, weight=1)
    cards_container.rowconfigure(0, weight=1)

    app.cards_canvas = tk.Canvas(cards_container, bg="#0f172a", highlightthickness=0)
    app.cards_scrollbar = ttk.Scrollbar(cards_container, orient="vertical", command=app.cards_canvas.yview)
    app.cards_inner = ttk.Frame(app.cards_canvas)
    app.cards_inner.columnconfigure(0, weight=1)

    app.cards_inner.bind(
        "<Configure>",
        lambda _event: app.cards_canvas.configure(
            scrollregion=(
                0,
                0,
                (app.cards_canvas.bbox("all") or (0, 0, 0, 0))[2],
                (app.cards_canvas.bbox("all") or (0, 0, 0, 0))[3],
            )
        ),
    )

    app.cards_window = app.cards_canvas.create_window((0, 0), window=app.cards_inner, anchor="nw")
    app.cards_canvas.bind(
        "<Configure>",
        lambda event: app.cards_canvas.itemconfigure(app.cards_window, width=event.width),
    )
    app.cards_canvas.configure(yscrollcommand=app.cards_scrollbar.set)

    app.cards_canvas.grid(row=0, column=0, sticky="nsew")
    app.cards_scrollbar.grid(row=0, column=1, sticky="ns")

    app.root.bind_all("<MouseWheel>", app._on_cards_mousewheel, add="+")
    app.root.bind_all("<Button-4>", app._on_cards_mousewheel, add="+")
    app.root.bind_all("<Button-5>", app._on_cards_mousewheel, add="+")

    center.columnconfigure(0, weight=1)
    center.rowconfigure(7, weight=1)

    app.running_robots_var = tk.StringVar(value="Running robots: none")
    ttk.Label(center, textvariable=app.running_robots_var, style="Muted.TLabel").grid(row=0, column=0, sticky="w")

    app.last_saved_var = tk.StringVar(value="Last saved: never")
    ttk.Label(center, textvariable=app.last_saved_var, style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(2, 8))

    task_btns = ttk.Frame(center)
    task_btns.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    task_btns.columnconfigure(0, weight=1)
    task_btns.columnconfigure(1, weight=1)

    app.assign_tasks_button = ttk.Button(task_btns, text="ASSIGN 5 TASKS", command=app.assign_tasks, style="Secondary.TButton")
    app.assign_tasks_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    app.assign_tasks_all_button = ttk.Button(
        task_btns,
        text="ASSIGN 5 TASKS TO ALL",
        command=app.assign_tasks_to_all,
        style="Secondary.TButton",
    )
    app.assign_tasks_all_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    run_btns = ttk.Frame(center)
    run_btns.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    run_btns.columnconfigure(0, weight=1)
    run_btns.columnconfigure(1, weight=1)
    run_btns.columnconfigure(2, weight=1)
    run_btns.columnconfigure(3, weight=1)
    run_btns.columnconfigure(4, weight=1)

    app.start_all_button = ttk.Button(run_btns, text="START ALL", command=app.start_all_tasks, style="Primary.TButton")
    app.start_all_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    app.start_selected_button = ttk.Button(run_btns, text="START SELECTED", command=app.start_selected_tasks, style="Secondary.TButton")
    app.start_selected_button.grid(row=0, column=1, sticky="ew", padx=2)

    app.pause_button = ttk.Button(run_btns, text="PAUSE", command=app.pause_runs, style="Secondary.TButton")
    app.pause_button.grid(row=0, column=2, sticky="ew", padx=2)

    app.resume_button = ttk.Button(run_btns, text="RESUME", command=app.resume_runs, style="Secondary.TButton")
    app.resume_button.grid(row=0, column=3, sticky="ew", padx=2)

    app.cancel_button = ttk.Button(run_btns, text="CANCEL", command=app.cancel_runs, style="Danger.TButton")
    app.cancel_button.grid(row=0, column=4, sticky="ew", padx=(4, 0))

    misc_btns = ttk.Frame(center)
    misc_btns.grid(row=4, column=0, sticky="ew", pady=(0, 8))
    misc_btns.columnconfigure(0, weight=1)
    misc_btns.columnconfigure(1, weight=1)

    app.save_now_button = ttk.Button(misc_btns, text="SAVE", command=app.save_now, style="Save.TButton")
    app.save_now_button.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    app.reset_state_button = ttk.Button(
        misc_btns,
        text="RESET",
        command=app.reset_saved_state,
        style="Danger.TButton",
    )
    app.reset_state_button.grid(row=0, column=1, sticky="ew", padx=(4, 0))

    ttk.Label(center, text="All Robots Progress", style="Header.TLabel").grid(row=5, column=0, sticky="w")
    app.progress_summary_var = tk.StringVar(value="Progress: no tasks assigned")
    ttk.Label(center, textvariable=app.progress_summary_var, style="Muted.TLabel").grid(row=5, column=0, sticky="e")
    app.all_robot_progress_container = ttk.Frame(center)
    app.all_robot_progress_container.grid(row=6, column=0, sticky="ew", pady=(2, 8))
    app.all_robot_progress_container.columnconfigure(0, weight=1)
    app.all_robot_progress_container.rowconfigure(0, weight=1)

    app.all_robot_progress_canvas = tk.Canvas(
        app.all_robot_progress_container,
        height=180,
        bg="#0f172a",
        highlightthickness=0,
    )
    app.all_robot_progress_scrollbar = ttk.Scrollbar(
        app.all_robot_progress_container,
        orient="vertical",
        command=app.all_robot_progress_canvas.yview,
    )
    app.all_robot_progress_frame = ttk.Frame(app.all_robot_progress_canvas)

    app.all_robot_progress_frame.bind(
        "<Configure>",
        lambda _event: app.all_robot_progress_canvas.configure(
            scrollregion=app.all_robot_progress_canvas.bbox("all")
        ),
    )

    app.all_robot_progress_window = app.all_robot_progress_canvas.create_window(
        (0, 0),
        window=app.all_robot_progress_frame,
        anchor="nw",
    )
    app.all_robot_progress_canvas.bind(
        "<Configure>",
        lambda event: app.all_robot_progress_canvas.itemconfigure(app.all_robot_progress_window, width=event.width),
    )
    app.all_robot_progress_canvas.configure(yscrollcommand=app.all_robot_progress_scrollbar.set)

    app.all_robot_progress_canvas.grid(row=0, column=0, sticky="nsew")
    app.all_robot_progress_scrollbar.grid(row=0, column=1, sticky="ns")

    app.root.bind_all("<MouseWheel>", app._on_progress_mousewheel, add="+")
    app.root.bind_all("<Button-4>", app._on_progress_mousewheel, add="+")
    app.root.bind_all("<Button-5>", app._on_progress_mousewheel, add="+")

    selected_tasks = ttk.Frame(center)
    selected_tasks.grid(row=7, column=0, sticky="nsew")
    selected_tasks.columnconfigure(0, weight=1)
    selected_tasks.columnconfigure(1, weight=1)
    selected_tasks.rowconfigure(1, weight=1)

    ttk.Label(selected_tasks, text="Selected Robot Pending", style="Header.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Label(selected_tasks, text="Leaderboard", style="Header.TLabel").grid(row=0, column=1, sticky="w")

    app.pending_lb = tk.Listbox(selected_tasks, height=8)
    app.pending_lb.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
    app.pending_lb.config(
        bg="#171919",
        fg="#ffffff",
        selectbackground="#1d4ed8",
        selectforeground="#ffffff",
        font=app.normal_font,
    )

    app.leaderboard_lb = tk.Listbox(selected_tasks, height=8)
    app.leaderboard_lb.grid(row=1, column=1, sticky="nsew")
    app.leaderboard_lb.config(
        bg="#171919",
        fg="#ffffff",
        selectbackground="#1d4ed8",
        selectforeground="#ffffff",
        font=app.normal_font,
    )

    app.status_var = tk.StringVar(value="Ready")
    ttk.Label(center, textvariable=app.status_var).grid(row=8, column=0, sticky="w", pady=(8, 0))

    app.toast_var = tk.StringVar(value="")
    app.toast_label = tk.Label(
        center,
        textvariable=app.toast_var,
        anchor="w",
        bg="#0f172a",
        fg="#f8fafc",
        font=app.normal_font,
        padx=8,
        pady=4,
    )
    app.toast_label.grid(row=9, column=0, sticky="ew", pady=(6, 0))
    app.toast_label.grid_remove()
