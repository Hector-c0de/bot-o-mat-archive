from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    description: str
    eta_ms: int


TASK_CATALOG = [
    Task(description="do the dishes", eta_ms=1000),
    Task(description="sweep the house", eta_ms=3000),
    Task(description="do the laundry", eta_ms=10000),
    Task(description="take out the recycling", eta_ms=4000),
    Task(description="make a sammich", eta_ms=7000),
    Task(description="mow the lawn", eta_ms=20000),
    Task(description="rake the leaves", eta_ms=18000),
    Task(description="give the dog a bath", eta_ms=14500),
    Task(description="bake some cookies", eta_ms=8000),
    Task(description="wash the car", eta_ms=20000),
]