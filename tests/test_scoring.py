import unittest

from src.scoring import calculate_score, can_robot_do_task
from src.tasks import Task


class TestScoring(unittest.TestCase):
    def test_can_robot_do_task_true_for_supported_task(self):
        self.assertTrue(can_robot_do_task("Unipedal", "do the dishes"))

    def test_can_robot_do_task_false_for_unsupported_task(self):
        self.assertFalse(can_robot_do_task("Unipedal", "wash the car"))

    def test_unknown_robot_type_defaults_to_true(self):
        self.assertTrue(can_robot_do_task("UnknownType", "anything"))

    def test_calculate_score_counts_only_supported_tasks(self):
        completed = [
            Task(description="do the dishes", eta_ms=1000),
            Task(description="wash the car", eta_ms=20000),
            Task(description="take out the recycling", eta_ms=4000),
        ]
        self.assertEqual(calculate_score("Unipedal", completed), 2)


if __name__ == "__main__":
    unittest.main()
