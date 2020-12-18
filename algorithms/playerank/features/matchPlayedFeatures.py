from .abstract import Feature
from .wyscoutEventsDefinition import *
import json
import glob


class matchPlayedFeatures(Feature):

    def createFeature(self,serialized_matches,players_file,select = None):
        """
        It computes, for each player and match, total time (in minutes) played,
        goals scored and


        Input:
        -serialized_matches: folder with json files corresponding to matches data
        -select: function  for filtering matches collection. Default: aggregate over all matches

        Output:

        a collection of documents in the f
        ormat _id-> {'match': this.wyId, 'player' : player,
        'name': 'minutesPlayed'|'team'|'goalScored'|'timestamp'},value: <float>|<string>;

        """
        players =  json.load(open(players_file))
        #  filtering out all the events from goalkeepers
        goalkeepers_ids = [player['wyId'] for player in players
                                if player['role']['name']=='Goalkeeper']
        
        print ("[matchPlayedFeatures] processing %s matches"%len(serialized_matches))
        result = []
        for id,match in serialized_matches.items():
            timestamp = match.date_utc

            for team in [match.home_team, match.away_team]:
                minutes_played = {}
                goals_scored = {}
                for player in team.formation.lineup+team.formation.bench:
                    minutes_played[player.player_id] = player.played_minutes
                    goals_scored[player.player_id] = player.goals

                for player,min in minutes_played.items():
                    if player not in goalkeepers_ids:
                        document = {'match':id,'entity':player,'feature':'minutesPlayed',
                                'value': min}
                        result.append (document)

                for player,gs in goals_scored.items():
                    if player not in goalkeepers_ids:
                        try:
                            gs = int(gs)
                        except:
                            gs = 0
                        document = {'match':id,'entity':player,'feature':'goalScored',
                                'value': gs}
                        result.append (document)
                        ## adding timestamp and team for each player
                        document = {'match':id,'entity':player,'feature':'timestamp',
                            'value': timestamp}

                        result.append (document)
                        ## adding timestamp and team for each player
                        document = {'match':id,'entity':player,'feature':'team',
                                'value': team.team_id}
                        result.append (document)
        print ("[matchPlayedFeatures] matches features computed. %s features processed"%(len(result)))
        return result
