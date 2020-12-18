from pysoccer.attributes import Team
from dataclasses import dataclass


@dataclass
class Match():
    """
    Class defining a match.
    """
    competition_id: int
    round_id: int
    season_id: int
    date_utc: str
    match_id: int
    label: str
    home_team: Team
    away_team: Team
    additional_attributes: list()
    