from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
from collections import defaultdict
import glob

TOUCH_TAGS = [1401, 1302, 201, 1901, 1301, 2001, 301]
EVENTS = ['Duel', 'Foul', 'Free Kick', 'Goalkeeper leaving line', 'Offside', 'Others on the ball', 'Pass', 'Shot']

class qualityFeatures(Feature):
    """
    Quality features are the count of events with outcomes.
    E.g.
    - number of accurate passes
    - number of wrong passes
    ...
    """
    def createFeature(self,serialized_events,players_file,entity = 'team',select = None):
        """
        compute qualityFeatures
        parameters:
        -serialized_events: file path of events file
        -select: function  for filtering events collection. Default: aggregate over all events
        -entity: it could either 'team' or 'player'. It selects the aggregation for qualityFeatures among teams or players qualityfeatures

        Output:
        list of dictionaries in the format: matchId -> entity -> feature -> value
        """

        aggregated_features = defaultdict(lambda : defaultdict(lambda: defaultdict(int)))

        players =  json.load(open(players_file))
        #  filtering out all the events from goalkeepers
        goalkeepers_ids = [player['wyId'] for player in players
                                if player['role']['name']=='Goalkeeper']

        events = []
        for event in serialized_events:
            if event.period in ['1H','2H'] and event.player_id not in goalkeepers_ids:
                events.append(event)
        print ("[qualityFeatures] added %s events"%len(events))

        for evt in events:
            labelSplit = evt.label.split("-")
            if labelSplit[0] in EVENTS: 
                ent = evt.team_id
                if entity == 'player':
                    ent = evt.player_id

                aggregated_features[evt.match_id][ent]["%s"%evt.label]+=1


        result =[]
        for match in aggregated_features:
            for entity in aggregated_features[match]:
                for feature in aggregated_features[match][entity]:
                    document = {}
                    document['match'] = match
                    document['entity'] = entity
                    document['feature'] = feature
                    document['value'] = aggregated_features[match][entity][feature]
                    result.append(document)

        return result