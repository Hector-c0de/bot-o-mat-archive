import tempfile
import unittest
from pathlib import Path

from src.gui.state import (
    build_state_payload,
    delete_state_file,
    load_state_payload,
    parse_state_payload,
    save_state_payload,
    task_to_dict,
)
from src.robot import Robot
from src.tasks import Task


class TestGuiState(unittest.TestCase):
    def test_task_to_dict_supports_task_and_dict(self):
        task = Task(description="do the dishes", eta_ms=1000)
        self.assertEqual(task_to_dict(task), {"description": "do the dishes", "eta_ms": 1000})
        task_map = {"description": "sweep the house", "eta": 3000}
        self.assertEqual(task_to_dict(task_map), {"description": "sweep the house", "eta_ms": 3000})

    def test_build_and_parse_state_payload_roundtrip(self):
        robot = Robot(name="Larry", robot_type="Bipedal")
        robot.tasks = [Task(description="do the dishes", eta_ms=1000)]
        robot.completed_tasks = [Task(description="take out the recycling", eta_ms=4000)]
        payload = build_state_payload(
            robots=[robot],
            selected_robot_index=0,
            pending_tasks_provider=lambda _idx: robot.tasks,
        )

        loaded_robots, selected_index = parse_state_payload(payload)
        self.assertEqual(selected_index, 0)
        self.assertEqual(len(loaded_robots), 1)
        self.assertEqual(loaded_robots[0].name, "Larry")
        self.assertEqual(loaded_robots[0].robot_type, "Bipedal")
        self.assertEqual(loaded_robots[0].tasks[0].description, "do the dishes")
        self.assertEqual(loaded_robots[0].completed_tasks[0].description, "take out the recycling")

    def test_save_load_and_delete_state_file(self):
        payload = {"robots": [], "selected_robot_index": None}

        with tempfile.TemporaryDirectory() as tmp_dir:
            state_file = Path(tmp_dir) / "state.json"
            self.assertTrue(save_state_payload(state_file, payload))
            loaded = load_state_payload(state_file)
            self.assertEqual(loaded, payload)
            self.assertTrue(delete_state_file(state_file))
            self.assertIsNone(load_state_payload(state_file))


if __name__ == "__main__":
    unittest.main()
