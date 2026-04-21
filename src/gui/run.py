from collections.abc import Callable
from time import monotonic

from ..robot import Robot
from ..tasks import Task


def build_runtime_state(run_indices: list[int]) -> dict[int, dict]:
    return {
        idx: {
            "active_task": None,
            "started_at": 0.0,
            "elapsed_before_pause_ms": 0,
        }
        for idx in run_indices
    }


def pause_runtime(runtime_state: dict[int, dict]) -> None:
    now = monotonic()
    for state in runtime_state.values():
        active_task = state.get("active_task")
        started_at = state.get("started_at", 0.0)
        if active_task is not None and started_at > 0:
            elapsed = int((now - started_at) * 1000)
            state["elapsed_before_pause_ms"] = state.get("elapsed_before_pause_ms", 0) + elapsed
            state["started_at"] = 0.0


def resume_runtime(runtime_state: dict[int, dict]) -> None:
    now = monotonic()
    for state in runtime_state.values():
        if state.get("active_task") is not None and state.get("started_at", 0.0) == 0.0:
            state["started_at"] = now


def restore_active_tasks_for_cancel(robots: list[Robot], runtime_state: dict[int, dict]) -> None:
    for idx, state in list(runtime_state.items()):
        active_task = state.get("active_task")
        if active_task is not None and 0 <= idx < len(robots):
            robots[idx].tasks.insert(0, active_task)


def advance_runtime_tick(
    robots: list[Robot],
    active_run_indices: set[int],
    runtime_state: dict[int, dict],
    task_desc_fn: Callable[[Task | dict], str],
    task_eta_fn: Callable[[Task | dict], int],
    can_robot_do_task_fn: Callable[[str, Task | dict], bool],
) -> tuple[str | None, list[str]]:
    now = monotonic()
    last_status: str | None = None
    log_messages: list[str] = []

    for idx in list(active_run_indices):
        if idx >= len(robots):
            active_run_indices.discard(idx)
            runtime_state.pop(idx, None)
            continue

        robot = robots[idx]
        state = runtime_state.get(idx)
        if state is None:
            continue

        active_task = state.get("active_task")
        if active_task is None:
            if robot.tasks:
                next_task = robot.tasks.pop(0)
                state["active_task"] = next_task
                state["started_at"] = now
                state["elapsed_before_pause_ms"] = 0
                last_status = f"{robot.name} started: {task_desc_fn(next_task)}"
                log_messages.append(last_status)
            else:
                active_run_indices.discard(idx)
                runtime_state.pop(idx, None)
            continue

        eta = task_eta_fn(active_task)
        started_at = state.get("started_at", 0.0)
        elapsed_before_pause = state.get("elapsed_before_pause_ms", 0)
        elapsed_ms = elapsed_before_pause + int((now - started_at) * 1000)

        if elapsed_ms >= eta:
            robot.completed_tasks.append(active_task)
            credited = can_robot_do_task_fn(robot.robot_type, active_task)
            if credited:
                last_status = f"{robot.name} completed: {task_desc_fn(active_task)} (credited)"
            else:
                last_status = f"{robot.name} completed: {task_desc_fn(active_task)} (no credit for {robot.robot_type})"
            log_messages.append(last_status)

            state["active_task"] = None
            state["started_at"] = 0.0
            state["elapsed_before_pause_ms"] = 0

            if not robot.tasks:
                active_run_indices.discard(idx)
                runtime_state.pop(idx, None)

    return last_status, log_messages
