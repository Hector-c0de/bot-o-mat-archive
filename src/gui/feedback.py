"""Feedback helpers for toast messages, notifications, and run-end sounds."""


def notify(app, title: str, message: str):
    app.root.bell()
    app._log_event(f"{title}: {message}")
    show_toast(app, message, tone="info", duration_ms=2800)


def show_toast(app, message: str, tone: str = "info", duration_ms: int = 2800):
    palette = {
        "info": ("#0f172a", "#f8fafc"),
        "success": ("#14532d", "#f0fdf4"),
        "warning": ("#78350f", "#fffbeb"),
        "error": ("#7f1d1d", "#fef2f2"),
    }
    bg, fg = palette.get(tone, palette["info"])
    app.toast_var.set(message)
    app.toast_label.configure(bg=bg, fg=fg)
    app.toast_label.grid()

    if app.toast_job is not None:
        app.root.after_cancel(app.toast_job)
    app.toast_job = app.root.after(duration_ms, app._clear_toast)


def clear_toast(app):
    app.toast_job = None
    app.toast_var.set("")
    app.toast_label.grid_remove()


def play_run_end_sound(app, sound_event: str):
    if sound_event == "completed":
        app.root.bell()
        app.root.after(120, app.root.bell)
    elif sound_event == "canceled":
        app.root.bell()
