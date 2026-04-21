"""Main GUI controller for BOT-O-MAT.

This module wires layout, theming, runtime orchestration, and persistence helpers.
"""

import random
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from pathlib import Path
from time import monotonic
from tkinter import messagebox, ttk

from ..robot import Robot
from ..robot_types import ROBOT_TYPES
from ..scoring import calculate_score, can_robot_do_task
from ..tasks import TASK_CATALOG, Task
from .run import (
    advance_runtime_tick,
    build_runtime_state,
    pause_runtime,
    restore_active_tasks_for_cancel,
    resume_runtime,
)
from .layout import build_gui_layout
from .navigation import focus_next_widget, focus_prev_widget, setup_keyboard_navigation
from .feedback import clear_toast, notify, play_run_end_sound, show_toast
from .state import (
    build_state_payload,
    delete_state_file,
    load_state_payload,
    parse_state_payload,
    save_state_payload,
    task_to_dict,
)
from .theme import apply_gui_theme


STATE_FILE = Path(__file__).resolve().parents[2] / "botomat_state.json"
LEGACY_STATE_FILE = Path(__file__).resolve().parents[1] / "botomat_state.json"


def task_desc(task: Task | dict) -> str:
    return task["description"] if isinstance(task, dict) else task.description


def task_eta(task: Task | dict) -> int:
    return task["eta"] if isinstance(task, dict) else task.eta_ms


class BotOMatGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("BOT-O-MAT")

        self.robots: list[Robot] = []
        self.selected_robot_index: int | None = None

        self.is_running = False
        self.is_paused = False
        self.active_run_indices: set[int] = set()
        self.runtime_state: dict[int, dict] = {}
        self.execution_job: str | None = None
        self.toast_job: str | None = None
        self.reset_confirm_deadline = 0.0
        self.run_complete_announced = False
        self.focus_order: list[tk.Widget] = []
        self.base_font_size = tkfont.nametofont("TkDefaultFont").cget("size")
        self.normal_font_family = "Roboto"
        self.button_font_family = "Roboto"
        self.robot_name_font_family = "Roboto"
        self.named_fonts = [
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
            "TkFixedFont",
        ]
        self.normal_font = tkfont.Font(root=self.root, family=self.normal_font_family, size=self.base_font_size)
        self.button_font = tkfont.Font(root=self.root, family=self.button_font_family, size=self.base_font_size)
        self.robot_name_font = tkfont.Font(root=self.root, family=self.robot_name_font_family, size=self.base_font_size + 1)
        for font_name in self.named_fonts:
            try:
                tkfont.nametofont(font_name).configure(family=self.normal_font_family)
            except tk.TclError:
                pass

        self.all_robot_progress_widgets: dict[int, dict] = {}

        self._configure_styles()
        self._build_ui()
        self._setup_keyboard_navigation()
        self._load_state()
        self._update_action_buttons_state()

    def _configure_styles(self):
        apply_gui_theme(self.root, self.normal_font, self.button_font)

    def _build_ui(self):
        build_gui_layout(self, ROBOT_TYPES)

    def _log_event(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        notifications = getattr(self, "notifications_text", None)
        if notifications is None:
            return
        notifications.config(state="normal")
        notifications.insert("end", f"[{timestamp}] {message}\n")
        notifications.see("end")
        notifications.config(state="disabled")

    def _set_last_saved_now(self):
        self.last_saved_var.set(f"Last saved: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def _notify(self, title: str, message: str):
        notify(self, title, message)

    def _show_toast(self, message: str, tone: str = "info", duration_ms: int = 2800):
        show_toast(self, message, tone=tone, duration_ms=duration_ms)

    def _clear_toast(self):
        clear_toast(self)

    def _setup_keyboard_navigation(self):
        setup_keyboard_navigation(self)

    def _focus_next_widget(self, _event: tk.Event):
        return focus_next_widget(self)

    def _focus_prev_widget(self, _event: tk.Event):
        return focus_prev_widget(self)

    def _update_progress_summary(self):
        completed_count = sum(len(robot.completed_tasks) for robot in self.robots)
        total_count = completed_count + sum(len(self._get_pending_tasks_for_robot(idx)) for idx in range(len(self.robots)))

        if total_count <= 0:
            summary = "Progress: no tasks assigned"
        else:
            summary = f"Progress: {completed_count}/{total_count} tasks completed"

        if self.is_running:
            summary += f" | Active robots: {len(self.active_run_indices)}"

        self.progress_summary_var.set(summary)

    def _update_running_robots_status(self):
        if not self.is_running:
            self.running_robots_var.set("Running robots: none")
            return

        names = [self.robots[idx].name for idx in sorted(self.active_run_indices) if 0 <= idx < len(self.robots)]
        if not names:
            self.running_robots_var.set("Running robots: none")
            return

        prefix = "Paused robots" if self.is_paused else "Running robots"
        self.running_robots_var.set(f"{prefix}: {', '.join(names)}")

    def _update_action_buttons_state(self):
        idle_state = "normal" if not self.is_running else "disabled"

        self.add_robot_button.config(state=idle_state)
        self.update_robot_button.config(state=idle_state)
        self.remove_robot_button.config(state=idle_state)
        self.assign_tasks_button.config(state=idle_state)
        self.assign_tasks_all_button.config(state=idle_state)
        self.start_selected_button.config(state=idle_state)
        self.start_all_button.config(state=idle_state)
        self.save_now_button.config(state=idle_state)
        self.reset_state_button.config(state=idle_state)

        self.name_entry.config(state=idle_state)
        self.type_combo.config(state="readonly" if not self.is_running else "disabled")

        if self.is_running:
            self.pause_button.config(state="normal" if not self.is_paused else "disabled")
            self.resume_button.config(state="normal" if self.is_paused else "disabled")
            self.cancel_button.config(state="normal")
        else:
            self.pause_button.config(state="disabled")
            self.resume_button.config(state="disabled")
            self.cancel_button.config(state="disabled")

    def _is_pointer_over_widget(self, widget: tk.Widget) -> bool:
        if not widget.winfo_ismapped():
            return False

        pointer_x = self.root.winfo_pointerx()
        pointer_y = self.root.winfo_pointery()
        widget_x = widget.winfo_rootx()
        widget_y = widget.winfo_rooty()
        widget_width = widget.winfo_width()
        widget_height = widget.winfo_height()

        return (
            widget_x <= pointer_x < widget_x + widget_width
            and widget_y <= pointer_y < widget_y + widget_height
        )

    def _on_progress_mousewheel(self, event: tk.Event):
        if not self._is_pointer_over_widget(self.all_robot_progress_canvas):
            return

        if getattr(event, "num", None) == 4:
            scroll_units = -1
        elif getattr(event, "num", None) == 5:
            scroll_units = 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return "break"
            scroll_units = -1 if delta > 0 else 1

        self.all_robot_progress_canvas.yview_scroll(scroll_units, "units")
        return "break"

    def _on_cards_mousewheel(self, event: tk.Event):
        if not self._is_pointer_over_widget(self.cards_canvas):
            return

        if getattr(event, "num", None) == 4:
            scroll_units = -1
        elif getattr(event, "num", None) == 5:
            scroll_units = 1
        else:
            delta = getattr(event, "delta", 0)
            if delta == 0:
                return "break"
            scroll_units = -1 if delta > 0 else 1

        top, bottom = self.cards_canvas.yview()
        if scroll_units < 0 and top <= 0.0:
            return "break"
        if scroll_units > 0 and bottom >= 1.0:
            return "break"

        self.cards_canvas.yview_scroll(scroll_units, "units")
        return "break"

    def _task_to_dict(self, task: Task | dict) -> dict:
        return task_to_dict(task)

    def _robot_score(self, robot: Robot) -> int:
        return calculate_score(robot.robot_type, robot.completed_tasks)

    def _robot_status(self, idx: int) -> str:
        if idx in self.active_run_indices:
            return "Paused" if self.is_paused else "Running"

        pending_count = len(self._get_pending_tasks_for_robot(idx))
        if pending_count == 0 and len(self.robots[idx].completed_tasks) > 0:
            return "Completed"
        return "Idle"

    def _robot_overall_progress_data(self, idx: int) -> tuple[float, str]:
        robot = self.robots[idx]
        completed = len(robot.completed_tasks)
        pending = len(robot.tasks)

        state = self.runtime_state.get(idx)
        active_task = state.get("active_task") if state else None
        in_progress = 1 if active_task is not None else 0
        total = completed + pending + in_progress

        if total <= 0:
            return 0.0, "Completed Tasks: no tasks"

        percent = (completed / total) * 100
        return percent, f"Completed Tasks: {completed}/{total}"

    def _robot_task_progress_data(self, idx: int) -> tuple[float, str]:
        state = self.runtime_state.get(idx)
        active_task = state.get("active_task") if state else None
        if active_task is None:
            return 0.0, "Status: idle"

        eta = max(1, task_eta(active_task))
        elapsed_before_pause = state.get("elapsed_before_pause_ms", 0)
        started_at = state.get("started_at", 0.0)
        elapsed_ms = elapsed_before_pause
        if started_at > 0:
            elapsed_ms += int((monotonic() - started_at) * 1000)
        elapsed_ms = min(elapsed_ms, eta)
        remaining_ms = max(0, eta - elapsed_ms)
        percent = (elapsed_ms / eta) * 100

        return percent, f"Task: {task_desc(active_task)} | {remaining_ms / 1000:.1f}s"

    def _render_all_robot_progress_bars(self):
        for child in self.all_robot_progress_frame.winfo_children():
            child.destroy()

        self.all_robot_progress_widgets = {}
        if not self.robots:
            ttk.Label(self.all_robot_progress_frame, text="No robots yet").grid(row=0, column=0, sticky="w")
            return

        progress_columns = 4
        for idx, robot in enumerate(self.robots):
            row_idx = idx // progress_columns
            col_idx = idx % progress_columns
            col = ttk.Frame(self.all_robot_progress_frame, padding=(0, 0, 10, 0))
            col.grid(row=row_idx, column=col_idx, sticky="ew", padx=(0, 4), pady=(0, 6))
            self.all_robot_progress_frame.columnconfigure(col_idx, weight=1, uniform="progress_cols")

            ttk.Label(col, text=f"{robot.name}", font=self.robot_name_font).grid(row=0, column=0, sticky="w")

            ttk.Label(col, text="Current Task").grid(row=1, column=0, sticky="w")
            task_bar = ttk.Progressbar(col, orient="horizontal", mode="determinate", maximum=100)
            task_bar.grid(row=2, column=0, sticky="ew", pady=(2, 2))
            task_text_var = tk.StringVar(value="Status: idle")
            ttk.Label(col, textvariable=task_text_var).grid(row=3, column=0, sticky="w")

            ttk.Label(col, text="Overall").grid(row=4, column=0, sticky="w", pady=(6, 0))
            overall_bar = ttk.Progressbar(col, orient="horizontal", mode="determinate", maximum=100)
            overall_bar.grid(row=5, column=0, sticky="ew", pady=(2, 2))
            overall_text_var = tk.StringVar(value="Overall: 0/0")
            ttk.Label(col, textvariable=overall_text_var).grid(row=6, column=0, sticky="w")
            col.columnconfigure(0, weight=1)

            self.all_robot_progress_widgets[idx] = {
                "task_bar": task_bar,
                "task_text": task_text_var,
                "overall_bar": overall_bar,
                "overall_text": overall_text_var,
            }

        self._update_all_robot_progress_bars()
        self.all_robot_progress_canvas.update_idletasks()
        self.all_robot_progress_canvas.configure(scrollregion=self.all_robot_progress_canvas.bbox("all"))

        first_row_height = 0
        for child in self.all_robot_progress_frame.winfo_children():
            info = child.grid_info()
            if int(info.get("row", 0)) == 0:
                first_row_height = max(first_row_height, child.winfo_reqheight())

        if first_row_height > 0:
            self.all_robot_progress_canvas.configure(height=first_row_height + 8)

    def _update_all_robot_progress_bars(self):
        for idx, widgets in self.all_robot_progress_widgets.items():
            if idx >= len(self.robots):
                continue
            task_percent, task_status = self._robot_task_progress_data(idx)
            overall_percent, overall_status = self._robot_overall_progress_data(idx)
            widgets["task_bar"]["value"] = task_percent
            widgets["task_text"].set(task_status)
            widgets["overall_bar"]["value"] = overall_percent
            widgets["overall_text"].set(overall_status)

    def _render_robot_cards(self):
        for child in self.cards_inner.winfo_children():
            child.destroy()

        if not self.robots:
            ttk.Label(self.cards_inner, text="No robots yet").grid(row=0, column=0, sticky="w")
            return

        badge_colors = {
            "Idle": "#6b7280",
            "Running": "#00a68c",
            "Paused": "#d97706",
            "Completed": "#1fb355",
        }

        for idx, robot in enumerate(self.robots):
            card_style = "CardSelected.TFrame" if idx == self.selected_robot_index else "Card.TFrame"
            frame = ttk.Frame(self.cards_inner, padding=8, style=card_style)
            frame.grid(row=idx, column=0, sticky="ew", pady=(0, 6))
            frame.columnconfigure(0, weight=1)

            status = self._robot_status(idx)
            score = self._robot_score(robot)
            completed = len(robot.completed_tasks)
            pending = len(self._get_pending_tasks_for_robot(idx))
            total = completed + pending
            progress_text = f"{completed}/{total}" if total else "0/0"

            top = ttk.Frame(frame, style=card_style)
            top.grid(row=0, column=0, sticky="ew")
            top.columnconfigure(0, weight=1)

            title_label = ttk.Label(top, text=f"{robot.name} ({robot.robot_type})", font=self.robot_name_font)
            title_label.grid(row=0, column=0, sticky="w")
            badge = tk.Label(
                top,
                text=status,
                bg=badge_colors.get(status, "#6b7280"),
                fg="white",
                padx=6,
                pady=1,
            )
            badge.grid(row=0, column=1, sticky="e")

            subtitle_label = ttk.Label(frame, text=f"Score: {score} | Progress: {progress_text}")
            subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

            for widget in (frame, top, title_label, badge, subtitle_label):
                widget.bind("<Button-1>", lambda _e, card_idx=idx: self.select_robot(card_idx))

    def _get_pending_tasks_for_robot(self, idx: int) -> list[Task]:
        robot = self.robots[idx]
        pending = list(robot.tasks)
        state = self.runtime_state.get(idx)
        if state and state.get("active_task") is not None:
            pending.insert(0, state["active_task"])
        return pending

    def _save_state(self):
        payload = build_state_payload(
            robots=self.robots,
            selected_robot_index=self.selected_robot_index,
            pending_tasks_provider=self._get_pending_tasks_for_robot,
        )

        if save_state_payload(STATE_FILE, payload):
            self._set_last_saved_now()

    def _load_state(self):
        state_file = STATE_FILE
        if not state_file.exists() and LEGACY_STATE_FILE.exists():
            state_file = LEGACY_STATE_FILE

        if not state_file.exists():
            self._refresh_all_views(rebuild_progress=True)
            return

        payload = load_state_payload(state_file)
        if payload is None:
            self.status_var.set("Could not load saved state. Starting fresh.")
            self._refresh_all_views(rebuild_progress=True)
            return

        self.robots, self.selected_robot_index = parse_state_payload(payload)

        self._refresh_all_views(rebuild_progress=True)

        if self.robots:
            self.status_var.set(f"Loaded {len(self.robots)} robot(s) from saved state.")
            self._log_event(f"Loaded {len(self.robots)} robot(s) from saved state")

        if state_file == LEGACY_STATE_FILE and not STATE_FILE.exists():
            save_state_payload(STATE_FILE, payload)

        try:
            timestamp = datetime.fromtimestamp(state_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            self.last_saved_var.set(f"Last saved: {timestamp}")
        except OSError:
            self.last_saved_var.set("Last saved: unknown")

    def _refresh_selected_task_lists(self):
        self.pending_lb.delete(0, tk.END)

        robot = self.get_selected_robot()
        if robot is None or self.selected_robot_index is None:
            return

        state = self.runtime_state.get(self.selected_robot_index)
        if state and state.get("active_task") is not None:
            active = state["active_task"]
            self.pending_lb.insert(tk.END, f"[in progress] {task_desc(active)} ({task_eta(active)} ms)")

        for task in robot.tasks:
            self.pending_lb.insert(tk.END, f"{task_desc(task)} ({task_eta(task)} ms)")

    def _refresh_leaderboard(self):
        self.leaderboard_lb.delete(0, tk.END)
        ranking = sorted(self.robots, key=lambda robot: (-self._robot_score(robot), robot.name.lower()))

        for position, robot in enumerate(ranking, start=1):
            score = self._robot_score(robot)
            completed = len(robot.completed_tasks)
            self.leaderboard_lb.insert(
                tk.END,
                f"{position}. {robot.name} ({robot.robot_type}) - score: {score}, completed: {completed}",
            )

        for idx in range(self.leaderboard_lb.size()):
            self.leaderboard_lb.itemconfig(idx, bg="#171919", fg="#ffffff")

        medal_colors = {1: "#d4af37", 2: "#c0c0c0", 3: "#cd7f32"}
        for position, color in medal_colors.items():
            idx = position - 1
            if idx < self.leaderboard_lb.size():
                self.leaderboard_lb.itemconfig(idx, bg=color, fg="#ffffff")

    def _refresh_all_views(self, rebuild_progress: bool = False):
        self._render_robot_cards()
        self._refresh_selected_task_lists()
        self._refresh_leaderboard()
        self._update_running_robots_status()
        self._update_progress_summary()
        if rebuild_progress:
            self._render_all_robot_progress_bars()
        else:
            self._update_all_robot_progress_bars()

    def select_robot(self, idx: int):
        if self.is_running:
            return
        if 0 <= idx < len(self.robots):
            self.selected_robot_index = idx
            robot = self.robots[idx]
            self.name_var.set(robot.name)
            self.type_var.set(robot.robot_type)
            self._refresh_all_views()
            self._save_state()

    def get_selected_robot(self) -> Robot | None:
        if self.selected_robot_index is None:
            return None
        if self.selected_robot_index >= len(self.robots):
            return None
        return self.robots[self.selected_robot_index]

    def add_robot(self):
        name = self.name_var.get().strip()
        robot_type = self.type_var.get().strip()
        if not name or not robot_type:
            self._show_toast("Enter both name and robot type.", tone="warning")
            return

        if any(robot.name == name for robot in self.robots):
            self._show_toast("Robot names must be unique.", tone="warning")
            return

        self.robots.append(Robot(name=name, robot_type=robot_type))
        self.selected_robot_index = len(self.robots) - 1
        self._refresh_all_views(rebuild_progress=True)
        self._save_state()
        self._log_event(f"Added robot {name} ({robot_type})")

    def update_selected_robot(self):
        robot = self.get_selected_robot()
        if robot is None:
            self._show_toast("Select a robot card first.", tone="warning")
            return

        new_name = self.name_var.get().strip()
        new_type = self.type_var.get().strip()
        if not new_name or not new_type:
            self._show_toast("Enter both name and robot type.", tone="warning")
            return

        if any(idx != self.selected_robot_index and r.name == new_name for idx, r in enumerate(self.robots)):
            self._show_toast("Robot names must be unique.", tone="warning")
            return

        old_name = robot.name
        robot.name = new_name
        robot.robot_type = new_type
        self._refresh_all_views(rebuild_progress=True)
        self._save_state()
        self._log_event(f"Updated robot {old_name} -> {new_name} ({new_type})")

    def remove_selected_robot(self):
        robot = self.get_selected_robot()
        if robot is None:
            self._show_toast("Select a robot card first.", tone="warning")
            return

        confirmed = messagebox.askyesno("Remove Robot", f"Remove {robot.name}?")
        if not confirmed:
            return

        removed_name = robot.name
        del self.robots[self.selected_robot_index]

        if not self.robots:
            self.selected_robot_index = None
            self.name_var.set("")
        else:
            self.selected_robot_index = min(self.selected_robot_index, len(self.robots) - 1)
            selected = self.robots[self.selected_robot_index]
            self.name_var.set(selected.name)
            self.type_var.set(selected.robot_type)

        self._refresh_all_views(rebuild_progress=True)
        self._save_state()
        self._log_event(f"Removed robot {removed_name}")

    def assign_tasks(self):
        if self.is_running:
            self._show_toast("Wait for the current run to finish.", tone="warning")
            return

        robot = self.get_selected_robot()
        if not robot:
            self._show_toast("Add/select a robot first.", tone="warning")
            return

        robot.tasks = random.sample(TASK_CATALOG, k=5)
        self._refresh_all_views()
        self._save_state()
        self.status_var.set(f"Assigned 5 tasks to {robot.name}.")
        self._log_event(f"Assigned 5 tasks to {robot.name}")

    def assign_tasks_to_all(self):
        if self.is_running:
            self._show_toast("Wait for the current run to finish.", tone="warning")
            return

        if not self.robots:
            self._show_toast("Add at least one robot first.", tone="warning")
            return

        shared = random.sample(TASK_CATALOG, k=5)
        for robot in self.robots:
            robot.tasks = [Task(description=task.description, eta_ms=task.eta_ms) for task in shared]

        self._refresh_all_views()
        self._save_state()
        self.status_var.set("Assigned the same 5 tasks to all robots.")
        self._log_event("Assigned same 5 tasks to all robots")

    def _start_runs(self, run_indices: list[int], status: str):
        self.is_running = True
        self.is_paused = False
        self.run_complete_announced = False
        self.active_run_indices = set(run_indices)
        self.runtime_state = build_runtime_state(run_indices)
        self.status_var.set(status)
        self._update_action_buttons_state()
        self._refresh_all_views()
        self._execution_tick()

    def start_selected_tasks(self):
        if self.is_running:
            self._show_toast("A task run is already in progress.", tone="warning")
            return

        if self.selected_robot_index is None:
            self._show_toast("Add/select a robot first.", tone="warning")
            return

        robot = self.get_selected_robot()
        if not robot or not robot.tasks:
            self._show_toast("Assign tasks first.", tone="warning")
            return

        self._start_runs([self.selected_robot_index], f"Starting tasks for {robot.name}...")

    def start_all_tasks(self):
        if self.is_running:
            self._show_toast("A task run is already in progress.", tone="warning")
            return

        run_indices = [idx for idx, robot in enumerate(self.robots) if robot.tasks]
        if not run_indices:
            self._show_toast("Assign tasks to at least one robot first.", tone="warning")
            return

        self._start_runs(run_indices, "Starting all robots in parallel...")

    def pause_runs(self):
        if not self.is_running or self.is_paused:
            return

        pause_runtime(self.runtime_state)

        self.is_paused = True
        self.status_var.set("Execution paused.")
        self._update_action_buttons_state()
        self._refresh_all_views()
        self._save_state()
        self._log_event("Execution paused")

    def resume_runs(self):
        if not self.is_running or not self.is_paused:
            return

        resume_runtime(self.runtime_state)

        self.is_paused = False
        self.status_var.set("Execution resumed.")
        self._update_action_buttons_state()
        self._refresh_all_views()
        self._save_state()
        self._log_event("Execution resumed")

    def cancel_runs(self):
        if not self.is_running:
            return

        restore_active_tasks_for_cancel(self.robots, self.runtime_state)

        self._finish_runs(
            notify_title="Run Canceled",
            notify_message="Active run was canceled.",
            show_notification=False,
            sound_event="canceled",
        )

    def _play_run_end_sound(self, sound_event: str):
        play_run_end_sound(self, sound_event)

    def _finish_runs(
        self,
        notify_title: str,
        notify_message: str,
        show_notification: bool = True,
        sound_event: str | None = None,
    ):
        if self.execution_job is not None:
            self.root.after_cancel(self.execution_job)
            self.execution_job = None

        self.is_running = False
        self.is_paused = False
        self.run_complete_announced = False
        self.active_run_indices = set()
        self.runtime_state = {}

        self._update_action_buttons_state()
        self._refresh_all_views(rebuild_progress=True)
        self._save_state()
        self.status_var.set(notify_message)
        if sound_event is not None:
            self._play_run_end_sound(sound_event)
        if show_notification:
            self._notify(notify_title, notify_message)

    def _execution_tick(self):
        if not self.is_running:
            return

        self.execution_job = None

        if self.is_paused:
            self._refresh_all_views()
            self._schedule_next_tick()
            return

        last_status, log_messages = advance_runtime_tick(
            robots=self.robots,
            active_run_indices=self.active_run_indices,
            runtime_state=self.runtime_state,
            task_desc_fn=task_desc,
            task_eta_fn=task_eta,
            can_robot_do_task_fn=can_robot_do_task,
        )
        for message in log_messages:
            self._log_event(message)

        self._refresh_all_views()
        self._save_state()

        if last_status:
            self.status_var.set(last_status)

        if not self.active_run_indices:
            if self.run_complete_announced:
                return

            self.run_complete_announced = True
            self._finish_runs(
                notify_title="Run Complete",
                notify_message="All scheduled robot tasks completed.",
                show_notification=False,
                sound_event="completed",
            )
            return

        self._schedule_next_tick()

    def _schedule_next_tick(self):
        if self.execution_job is None and self.is_running:
            self.execution_job = self.root.after(100, self._execution_tick)

    def reset_saved_state(self):
        if self.is_running:
            self._show_toast("Cancel or finish current execution first.", tone="warning")
            return

        now = monotonic()
        if now > self.reset_confirm_deadline:
            self.reset_confirm_deadline = now + 4.0
            self._show_toast(
                "Press RESET again within 4 seconds to confirm.",
                tone="warning",
                duration_ms=4000,
            )
            return

        self.reset_confirm_deadline = 0.0

        self.robots = []
        self.selected_robot_index = None

        for state_file in (STATE_FILE, LEGACY_STATE_FILE):
            if state_file.exists() and not delete_state_file(state_file):
                self._show_toast("Could not delete botomat_state.json.", tone="warning")

        self.last_saved_var.set("Last saved: never")

        self.name_var.set("")
        self._refresh_all_views(rebuild_progress=True)
        self.status_var.set("Saved state reset.")
        self._log_event("Saved state reset")
        self._show_toast("State reset.", tone="warning", duration_ms=2800)

    def save_now(self):
        self._save_state()
        self.status_var.set("State saved.")
        self._log_event("State saved")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1320x640")
    app = BotOMatGUI(root)
    root.mainloop()
