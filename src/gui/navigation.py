"""Keyboard navigation helpers for deterministic tab traversal."""

from tkinter import ttk


def setup_keyboard_navigation(app):
    app.cards_canvas.configure(takefocus=1)
    app.all_robot_progress_canvas.configure(takefocus=1)
    app.pending_lb.configure(takefocus=1, exportselection=False)
    app.leaderboard_lb.configure(takefocus=1, exportselection=False)

    app.focus_order = [
        app.name_entry,
        app.type_combo,
        app.add_robot_button,
        app.update_robot_button,
        app.remove_robot_button,
        app.cards_canvas,
        app.assign_tasks_button,
        app.assign_tasks_all_button,
        app.start_all_button,
        app.start_selected_button,
        app.pause_button,
        app.resume_button,
        app.cancel_button,
        app.save_now_button,
        app.reset_state_button,
        app.all_robot_progress_canvas,
        app.pending_lb,
        app.leaderboard_lb,
    ]

    for widget in app.focus_order:
        widget.bind("<Tab>", app._focus_next_widget, add="+")
        widget.bind("<Shift-Tab>", app._focus_prev_widget, add="+")
        widget.bind("<ISO_Left_Tab>", app._focus_prev_widget, add="+")

    button_widgets = [w for w in app.focus_order if isinstance(w, ttk.Button)]
    for button in button_widgets:
        button.bind("<Return>", lambda _event, btn=button: btn.invoke(), add="+")


def focus_next_widget(app):
    current = app.root.focus_get()
    if current not in app.focus_order:
        if app.focus_order:
            app.focus_order[0].focus_set()
        return "break"

    idx = app.focus_order.index(current)
    next_idx = (idx + 1) % len(app.focus_order)
    app.focus_order[next_idx].focus_set()
    return "break"


def focus_prev_widget(app):
    current = app.root.focus_get()
    if current not in app.focus_order:
        if app.focus_order:
            app.focus_order[-1].focus_set()
        return "break"

    idx = app.focus_order.index(current)
    prev_idx = (idx - 1) % len(app.focus_order)
    app.focus_order[prev_idx].focus_set()
    return "break"
