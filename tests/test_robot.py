import unittest
from unittest.mock import patch

from src.robot import Robot
from src.tasks import Task


class TestRobot(unittest.TestCase):
    def test_assign_tasks_appends(self):
        robot = Robot(name="Larry", robot_type="Bipedal")
        tasks = [Task(description="do the dishes", eta_ms=1)]
        robot.assign_tasks(tasks)
        self.assertEqual(len(robot.tasks), 1)

    @patch("src.robot.sleep", return_value=None)
    def test_complete_next_task_moves_task_to_completed(self, _sleep_mock):
        robot = Robot(name="Larry", robot_type="Bipedal")
        robot.tasks = [Task(description="do the dishes", eta_ms=1)]
        completed = robot.complete_next_task()
        self.assertIsNotNone(completed)
        self.assertEqual(len(robot.tasks), 0)
        self.assertEqual(len(robot.completed_tasks), 1)

    @patch("src.robot.sleep", return_value=None)
    def test_run_all_tasks_completes_all(self, _sleep_mock):
        robot = Robot(name="Larry", robot_type="Bipedal")
        robot.tasks = [
            Task(description="do the dishes", eta_ms=1),
            Task(description="sweep the house", eta_ms=1),
        ]
        finished = robot.run_all_tasks()
        self.assertEqual(len(finished), 2)
        self.assertEqual(len(robot.tasks), 0)
        self.assertEqual(len(robot.completed_tasks), 2)


if __name__ == "__main__":
    unittest.main()
