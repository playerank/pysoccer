from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict
import glob


class goalScoredFeatures(Feature):
    """
    goals scored by each team in each match
    """
    def createFeature(self,serialized_matches,select = None):
        """
        stores qualityFeatures on database
        parameters:
        -serialized_matches: file path of matches file
        -select: function  for filtering matches collection. Default: aggregate over all matches

        Output:
        list of documents in the format: match: matchId, entity: team, feature: feature, value: value
        """

        print("[GoalScored features] added %s matches"%len(serialized_matches))
        result =[]

        for id,match in serialized_matches.items():
            for team in [match.home_team, match.away_team]:
                document = {}
                document['match'] = id
                document['entity'] = team.team_id
                document['feature'] = 'goal-scored'
                document['value'] = team.score
                result.append(document)


        return result
