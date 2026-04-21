from .tasks import Task


SUPPORTED_TASKS_BY_TYPE = {
    "Unipedal": {
        "do the dishes",
        "sweep the house",
        "do the laundry",
        "take out the recycling",
        "make a sammich",
    },
    "Bipedal": {
        "do the dishes",
        "sweep the house",
        "do the laundry",
        "take out the recycling",
        "wash the car",
    },
    "Quadrupedal": {
        "sweep the house",
        "mow the lawn",
        "rake the leaves",
        "give the dog a bath",
        "wash the car",
    },
    "Arachnid": {
        "do the dishes",
        "sweep the house",
        "do the laundry",
        "take out the recycling",
        "give the dog a bath",
    },
    "Radial": {
        "do the dishes",
        "sweep the house",
        "do the laundry",
        "make a sammich",
        "bake some cookies",
    },
    "Aeronautical": {
        "take out the recycling",
        "mow the lawn",
        "rake the leaves",
        "wash the car",
        "bake some cookies",
    },
}


def _task_description(task: Task | dict | str) -> str:
    if isinstance(task, str):
        return task
    if isinstance(task, dict):
        return str(task.get("description", ""))
    return task.description


def can_robot_do_task(robot_type: str, task: Task | dict | str) -> bool:
    supported = SUPPORTED_TASKS_BY_TYPE.get(robot_type)
    if supported is None:
        return True
    return _task_description(task) in supported


def calculate_score(robot_type: str, completed_tasks: list[Task | dict]) -> int:
    return sum(1 for task in completed_tasks if can_robot_do_task(robot_type, task))