"""Persistence helpers for BOT-O-MAT GUI state (save/load/reset)."""

import json
from pathlib import Path
from typing import Callable

from ..robot import Robot
from ..tasks import Task


def task_to_dict(task: Task | dict) -> dict:
    if isinstance(task, dict):
        description = task.get("description")
        eta_ms = task.get("eta_ms", task.get("eta"))
        return {"description": description, "eta_ms": eta_ms}
    return {"description": task.description, "eta_ms": task.eta_ms}


def _task_from_dict(task_data: dict) -> Task | None:
    description = task_data.get("description")
    eta_ms = task_data.get("eta_ms", task_data.get("eta"))
    if description is None or eta_ms is None:
        return None
    return Task(description=description, eta_ms=eta_ms)


def build_state_payload(
    robots: list[Robot],
    selected_robot_index: int | None,
    pending_tasks_provider: Callable[[int], list[Task]],
) -> dict:
    return {
        "robots": [
            {
                "name": robot.name,
                "robot_type": robot.robot_type,
                "tasks": [task_to_dict(task) for task in pending_tasks_provider(idx)],
                "completed_tasks": [task_to_dict(task) for task in robot.completed_tasks],
            }
            for idx, robot in enumerate(robots)
        ],
        "selected_robot_index": selected_robot_index,
    }


def save_state_payload(state_file: Path, payload: dict) -> bool:
    try:
        state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def load_state_payload(state_file: Path) -> dict | None:
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def parse_state_payload(payload: dict) -> tuple[list[Robot], int | None]:
    robots: list[Robot] = []
    for robot_data in payload.get("robots", []):
        name = robot_data.get("name")
        robot_type = robot_data.get("robot_type")
        if not name or not robot_type:
            continue

        robot = Robot(name=name, robot_type=robot_type)
        robot.tasks = [
            task
            for task in (_task_from_dict(t) for t in robot_data.get("tasks", []))
            if task is not None
        ]
        robot.completed_tasks = [
            task
            for task in (_task_from_dict(t) for t in robot_data.get("completed_tasks", []))
            if task is not None
        ]
        robots.append(robot)

    requested_index = payload.get("selected_robot_index")
    if isinstance(requested_index, int) and 0 <= requested_index < len(robots):
        selected_robot_index: int | None = requested_index
    elif robots:
        selected_robot_index = 0
    else:
        selected_robot_index = None

    return robots, selected_robot_index


def delete_state_file(state_file: Path) -> bool:
    try:
        state_file.unlink()
        return True
    except OSError:
        return False
