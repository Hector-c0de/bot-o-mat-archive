import unittest
from time import monotonic

from src.gui.run import (
    advance_runtime_tick,
    build_runtime_state,
    pause_runtime,
    restore_active_tasks_for_cancel,
    resume_runtime,
)
from src.robot import Robot
from src.scoring import can_robot_do_task
from src.tasks import Task


def _task_desc(task):
    return task.description


def _task_eta(task):
    return task.eta_ms


class TestGuiRun(unittest.TestCase):
    def test_build_runtime_state(self):
        runtime = build_runtime_state([0, 2])
        self.assertEqual(set(runtime.keys()), {0, 2})
        self.assertIsNone(runtime[0]["active_task"])
        self.assertEqual(runtime[0]["started_at"], 0.0)

    def test_pause_and_resume_runtime(self):
        runtime = {
            0: {
                "active_task": Task(description="do the dishes", eta_ms=1000),
                "started_at": monotonic() - 0.2,
                "elapsed_before_pause_ms": 0,
            }
        }
        pause_runtime(runtime)
        self.assertEqual(runtime[0]["started_at"], 0.0)
        self.assertGreater(runtime[0]["elapsed_before_pause_ms"], 0)
        resume_runtime(runtime)
        self.assertGreater(runtime[0]["started_at"], 0.0)

    def test_restore_active_tasks_for_cancel(self):
        robot = Robot(name="Larry", robot_type="Bipedal")
        active_task = Task(description="do the dishes", eta_ms=1000)
        runtime = {0: {"active_task": active_task}}
        restore_active_tasks_for_cancel([robot], runtime)
        self.assertEqual(len(robot.tasks), 1)
        self.assertEqual(robot.tasks[0].description, "do the dishes")

    def test_advance_runtime_tick_starts_task(self):
        robot = Robot(name="Larry", robot_type="Bipedal")
        robot.tasks = [Task(description="do the dishes", eta_ms=1000)]
        robots = [robot]
        active_indices = {0}
        runtime = build_runtime_state([0])

        last_status, logs = advance_runtime_tick(
            robots=robots,
            active_run_indices=active_indices,
            runtime_state=runtime,
            task_desc_fn=_task_desc,
            task_eta_fn=_task_eta,
            can_robot_do_task_fn=can_robot_do_task,
        )
        self.assertIn("started", last_status)
        self.assertEqual(len(logs), 1)
        self.assertIsNotNone(runtime[0]["active_task"])
        self.assertEqual(len(robot.tasks), 0)

    def test_advance_runtime_tick_completes_task(self):
        robot = Robot(name="Larry", robot_type="Bipedal")
        active_task = Task(description="do the dishes", eta_ms=50)
        robots = [robot]
        active_indices = {0}
        runtime = {
            0: {
                "active_task": active_task,
                "started_at": monotonic() - 1,
                "elapsed_before_pause_ms": 0,
            }
        }

        last_status, logs = advance_runtime_tick(
            robots=robots,
            active_run_indices=active_indices,
            runtime_state=runtime,
            task_desc_fn=_task_desc,
            task_eta_fn=_task_eta,
            can_robot_do_task_fn=can_robot_do_task,
        )

        self.assertIn("completed", last_status)
        self.assertEqual(len(logs), 1)
        self.assertEqual(len(robot.completed_tasks), 1)
        self.assertEqual(active_indices, set())
        self.assertNotIn(0, runtime)


if __name__ == "__main__":
    unittest.main()
