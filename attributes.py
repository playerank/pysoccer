from enum import Enum
from dataclasses import dataclass
from typing import List


@dataclass
class Point:
    """
    Class defining a point on the pitch.
    """
    x: float
    y: float

class ResultType(Enum):
    """Class defining the possible results of an event.
    """
    SUCCESS = 'SUCCESS'
    NEUTRAL = 'NEUTRAL'
    FAILURE = 'FAILURE'
    UNDEFINED = 'UNDEFINED'

@dataclass
class Substitution():
    """
    Class defining a substitution during a match.
    """
    player_in: int
    player_out: int
    timestamp: float
    

@dataclass
class Player():
    """
    Class defining a soccer player.
    """
    player_id: int
    played_minutes: int
    yellow_cards: int
    red_cards: int
    own_goals: int
    goals: int


@dataclass
class Formation():
    """
    Class defining the formation of a given team in a match.
    """
    lineup: List[Player]
    bench: List[Player]


@dataclass
class Team():
    """
    Class defining a soccer team.
    """
    team_id: int
    coach_id: int
    score: int
    formation: Formation
    substitutions: List[Substitution]