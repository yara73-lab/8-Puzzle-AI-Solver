"""
Common result format for all search algorithms.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional

State = tuple[int, ...]

SearchStatus = Literal["success", "failure", "cutoff"]


@dataclass
class SearchResult:
    algorithm: str
    status: SearchStatus

    path: list[State] = field(default_factory=list)
    moves: list[str] = field(default_factory=list)

    path_cost: Optional[int] = None
    nodes_expanded: int = 0
    search_depth: Optional[int] = None
    running_time: float = 0.0

    @property
    def solved(self) -> bool:
        return self.status == "success"