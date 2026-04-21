from dataclasses import dataclass, field
from time import sleep
from typing import List

from .tasks import Task


@dataclass
class Robot:
    name: str
    robot_type: str
    tasks: List[Task] = field(default_factory=list)
    completed_tasks: List[Task] = field(default_factory=list)

    def assign_tasks(self, tasks: List[Task]) -> None:
        self.tasks.extend(tasks)

    def complete_next_task(self) -> Task | None:
        if not self.tasks:
            return None

        task = self.tasks.pop(0)
        sleep(task.eta_ms / 1000)
        self.completed_tasks.append(task)
        return task

    def run_all_tasks(self) -> List[Task]:
        finished: List[Task] = []
        while self.tasks:
            completed = self.complete_next_task()
            if completed:
                finished.append(completed)
        return finished