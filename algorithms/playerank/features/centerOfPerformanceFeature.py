import json
import glob
import numpy as np
from collections import defaultdict

from pysoccer.algorithms.playerank.features.abstract import Feature
from pysoccer.algorithms.playerank.features.wyscoutEventsDefinition import *

class centerOfPerformanceFeature(Feature):


    def createFeature(self, serialized_events, players_file, select = None):
        """
        Compute centerOfPerformanceFeatures

        :param serialiazed_events: folder path of events file
        :param players_file: file path of players data file
        :param select: function  for filtering matches collection. Default: aggregate over all matches
        :param entity: it could either 'team' or 'player'.
            It selects the aggregation for qualityFeatures among teams or players qualityfeatures. 
            Note: aggregation by team is exploited during learning phase, 
            for features weights estimation, while aggregation by players is involved for rating phase.

        :return: list of json docs dictionaries in the format: {matchId : int , entity : int, feature: string , value}
        """


        players =  json.load(open(players_file))
        goalkeepers_ids = {player['wyId']:'GK' for player in players
                                if player['role']['name']=='Goalkeeper'}
        events = []
        for event in serialized_events:
            if event.player_id != 0 and event.player_id not in goalkeepers_ids:
                events.append(event)
        print ("[centerOfPerformanceFeature] added %s events"%len(events))

        MIN_EVENTS = 10
        players_positions = defaultdict(lambda : defaultdict(list))
        for evt in events:
            player = evt.player_id
            match = evt.match_id
            position = (evt.start_position.x,evt.start_position.y)
            players_positions[match][player].append(position)



        #formatting features as json document
        results = []
        for match,players_pos in players_positions.items():
            for p in players_pos:
                positions = players_pos[p]
                x,y,count = np.mean([x[0] for x in positions]),np.mean([x[1] for x in positions]),len(positions)
                if count>MIN_EVENTS:
                    documents = [
                        {'feature':'avg_x','entity':p,'match':match,'value':int(x)},
                        {'feature':'avg_y','entity':p,'match':match,'value':int(y)},
                        {'feature':'n_events','entity':p,'match':match,'value':count},

                    ]
                    results+=documents

        return results
