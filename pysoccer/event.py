from typing import List
from dataclasses import dataclass

from pysoccer.attributes import Point, ResultType

@dataclass
class Event():
    """
    Class defining a standardized event.
    """
    event_id: int
    team_id: int
    player_id: int
    match_id: int
    period: str
    timestamp: float
    start_position: Point
    end_position: Point
    outcome: ResultType
    label: str
    tags: List[str]
    phase_id: int
    phase_end: str
    phase_possessing_team: int

    def get_position(self, pitch_length: int, pitch_width: int, pitch_side: str):
        """
        Function that computes a player's position on the field.

        :param pitch_length: the pitch's length
        :param pitch_width: the pitch's width
        :param pitch_side: the pitch's side of the player's team
        """
        if pitch_side not in ['L', 'R']:
            raise ValueError('Use "L" or "R" to chose the side of the pitch!')
        if pitch_side == 'R':
            x = (self.start_position.x * pitch_length)/100
            y = (self.start_position.y * pitch_width)/100
        elif pitch_side == 'L':
            x = ((100-self.start_position.x) * pitch_length)/100
            y = ((100-self.start_position.y) * pitch_width)/100
        return Point(x, y)

    def to_dict(self):
        return self.__dict__

@dataclass
class PossessionEvent(Event):
    """
    Class that specifies an event of a player of the possessing team.
    """
    is_duel : bool = False
    challenged_player: str = None

    is_shot: bool = False
    goal_position: str = None
    is_goal: bool = False

    is_pass: bool = False
    receiver_player_id: int = None
    is_assist : bool = False
    is_keypass : bool = False


@dataclass
class NotPossessionEvent(Event):
    """
    Class that specifies an event of a player of the not possessing team.
    """
    is_duel: bool = False
    challenged_player: str = None

    is_foul: bool = False
    card : str = None