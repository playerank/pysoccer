import json
from collections import defaultdict
import glob

from pysoccer.algorithms.playerank.features.abstract import Feature
from pysoccer.algorithms.playerank.features.wyscoutEventsDefinition import *


class goalScoredFeatures(Feature):
    """
    Goals scored by each team in each match
    """
    def createFeature(self,serialized_matches,select = None):
        """
        Stores qualityFeatures on database
        
        :param serialized_matches: file path of matches file
        :param select: function  for filtering matches collection. Default: aggregate over all matches

        :return: list of documents in the format: match: matchId, entity: team, feature: feature, value: value
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
