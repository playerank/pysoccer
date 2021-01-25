from typing import List

from pysoccer.match import Match
from pysoccer.attributes import Player, Formation, Substitution, Team
from pysoccer.base import MatchSerializer

class WyscoutMatchSerializer(MatchSerializer):
    """
    Class that implements the match serializer for Wyscout matches.
    """

    def get_played_minutes(self, match: dict, id: str, player_id: int) -> int:
        """Function that computes a player's played minutes.

        :param match: the played match
        :param id: the player's team id
        :param player_id: the player's id
        :return: the played minutes
        """
        for sub in match['teamsData'][id]['formation']['substitutions']:
            if player_id == sub['playerIn']:
                return sub['minute']
            elif player_id == sub['playerOut']:
                if match['duration'] == 'Regular':
                    return 90-sub['minute']
                else:
                    return 120-sub['minute']
        if match['duration'] == 'Regular':
            return 90
        else:
            return 120
        return -1


    def get_player(self, player: dict, match: dict, id: str) -> Player:
        """Function that initializes a Player object containing a player's attributes.

        :param player: a dictionary containing the player's attributes
        :param match: a dictionary containing the match's attributes
        :param id: the player's team id
        :return: a Player object
        """
        plr = Player(
            player_id = player['playerId'],
            played_minutes = self.get_played_minutes(match, id, player['playerId']),
            yellow_cards = player['yellowCards'],
            red_cards = player['redCards'],
            own_goals = player['ownGoals'],
            goals = player['goals']
        )
        return plr


    def get_formation(self, match: dict, id: str) -> Formation:
        """Function that initializes a Formation object contaning a team's
        formation attributes.

        :param match: a dictionary containing the match's attributes
        :param id: the team's id
        :return: a Formation object
        """
        formation = match['teamsData'][id]['formation']
        frm = Formation(lineup = [], bench = [])
        for player in formation['bench']:
            plr = self.get_player(player, match, id)
            frm.bench.append(plr)
        for player in formation['lineup']:
            plr = self.get_player(player, match, id)
            frm.lineup.append(plr)
        return frm


    def get_substitutions(self, match: dict, id: str):
        """ Function that computes the substitions made during the match.

        :param match: a dictionary containing the match's attributes
        :param id: the team's id
        :return: a list of substitutions
        """
        substitutions = match['teamsData'][id]['formation']['substitutions']
        subs = []
        for sub in substitutions:
            curr = Substitution(
                player_in = sub['playerIn'],
                player_out = sub['playerOut'],
                timestamp = sub['minute']
            )
            subs.append(curr)
        return subs
        

    def get_team_data(self, match: dict, id: str) -> Team:
        """ Function that initializes a Team object containing a team's attributes.

        :param match: a dictionary containing the match's attributes
        :param id: the team's id
        :return: a Team object
        """
        frm = self.get_formation(match, id)
        subs = self.get_substitutions(match, id)
        team = Team(
                team_id = id,
                coach_id = match['teamsData'][id]['coachId'],
                score = match['teamsData'][id]['score'],
                formation = frm,
                substitutions = subs
        )
        return team

    def get_match_attributes(self, match:dict):
        """Function that computes the additional attributes of a match.

        :param match: a dictionary containing the match's attributes
        :return: a list of dictionary containing the attributes
        """
        attributes = [
            {'winner':match['winner']},
            {'status':match['status']},
            {'duration':match['duration']},
            {'gameweek':match['gameweek']}
        ]
        for ref in match['referees']:
            attributes.append({ref['role']:ref['refereeId']})
        return attributes


    def serialize(self, match: List):
        """Serializer that converts a list of Wyscout matches in a list of standardized match objects.

        :param match: a list containing the Wyscout matches
        :return: a list containing the standardized events
        """
        matches = {}
        
        for match in match.values():

            for team in match['teamsData'].values():
                if team['side'] == 'home':
                    home_id = str(team['teamId'])
                else:
                    away_id = str(team['teamId'])

            attributes = self.get_match_attributes(match)

            match_args = dict(
                competition_id = match['competitionId'],
                round_id = match['roundId'],
                season_id = match['seasonId'],
                date_utc = match['dateutc'],
                match_id = match['wyId'],
                label = match['label'],
                home_team = self.get_team_data(match, home_id),
                away_team = self.get_team_data(match, away_id),
                additional_attributes = attributes
            )
            serialized_match = Match(**match_args)
            matches[match['wyId']] = serialized_match

        return matches