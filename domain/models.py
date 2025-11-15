from dataclasses import dataclass

@dataclass(frozen=True)
class Repository:
    repo_id: int
    full_name: str
    stars: int
