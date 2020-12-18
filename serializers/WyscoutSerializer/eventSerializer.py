from typing import List
from pysoccer.event import *
from pysoccer.attributes import *
from pysoccer.base import EventSerializer
from pysoccer.serializers.WyscoutSerializer.wyscoutAttributes import *
from pysoccer.serializers.WyscoutSerializer.phaseDetection import get_play_actions
from pysoccer.serializers.WyscoutSerializer.phaseFeatures import possessing_team


class WyscoutEventSerializer(EventSerializer):
    """
    Class that implements a serializer for Wyscout events.
    """

    def get_outcome(self, event, events, curr_phase, next_phase, tags):
        """ Fuction that computes the outcome of an event.

        :param event: event whose outcome is beign computed
        :param events: list containing the match's events
        :param phases: list containing the possession phases
        :param tags: list containing the event's tags
        :return: the outcome of the event
        """
        tags.sort()
        for tag in tags:
            if tag == NEUTRAL:
                return 'neutral'
            elif tag in [WON, ACCURATE]:
                return 'success'
            elif tag in [LOST,NOT_ACCURATE]:
                return 'failure'
        if event['eventId'] == OTHERS_ON_BALL:
            if (curr_phase[1].index(event)+1) == len(curr_phase[1]):
                if next_phase == None:
                    # this is the last phase of the match
                    return 'neutral'
                if possessing_team(curr_phase) != possessing_team(next_phase):
                    return 'success'
            return 'failure'
        if event['subEventId'] == GOAL_KICK:
            next_event = events[events.index(event)+1]
            if event['teamId'] == next_event['teamId']:
                return 'success'
            else:
                return 'failure'
        return 'undefined'
        
    
    def get_receiver(self, event, tags, events):
        """ Fuction that calculates the receiver of a pass.

        :param event: pass event whose receiver is beign calculated
        :param tags: list containing the event's tags
        :param events: list containing the match's events
        :return: the receiver if the pass was accurate, None otherwise
        """
        if 1801 in tags:
            next_event = events[events.index(event)+1]
            if event['teamId'] == next_event['teamId']:
                return next_event['playerId']
        else:
            return None


    def get_goal_position(self, event):
        """ Function that calculate where a shot ended.
        The goal is divided in a 3x3 with the zones named .
        Then there is a zone over the bar and two on the sides of the posts.

        :param event: shot event that the function computes
        :return: the position where the shot ended
        """
        for tag in event['tags']:
            if tag['id'] in SHOT_POSITIONS:
                if tag['id'] in OUT_HIGH:
                    position = 'H'
                elif tag['id'] in OUT_LEFT:
                    position = 'L'
                elif tag['id'] in OUT_RIGHT:
                    position = 'R'
                elif tag['id'] in GOAL_POSITIONS:
                    position = GOAL_POSITIONS[tag['id']]
            elif tag['id'] == BLOCKED:
                position = 'BLK'
        try:
            return position
        except UnboundLocalError:
            return None



    def get_challenged_player(self, index, events):
        """ Function that computes the callenged player in a duel event.
        It search for a corresponding duel event. If there isn't it search for
        the closest opponent team's event and assume the player involved in that event
        as the callenged one.
        Separate if clause are needed to accurately separe the cases.

        :param index: index of the duel event
        :param events: list containing the match's events
        :return: the challenged player if there's one, None otherwise
        """
        if events[index-1]['eventId'] == 1:
            return events[index-1]['playerId']
        if events[index+1]['eventId'] == 1:
            return events[index+1]['playerId']
        if events[index-1]['teamId'] != events[index]['teamId']:
            return events[index-1]['playerId']
        if events[index+1]['teamId'] != events[index]['teamId']:
            return events[index+1]['playerId']
        return None


    def get_label(self, event, tags, outcome) -> str:
        """ Function that computes the event label.
        It append the event name to the sub event name separated by a minus.
        Then in the same way it appends the event's tag names.
        Finally the event's outcome is appended.

        :param event: the event we're creating the label for
        :param tags: the event's tags
        :param outcome: the event's outcome
        """
        label = event['eventName']
        if type(event['subEventName']) == str:
            label+="-%s"%event['subEventName']
        for tag in tags:
            if tag in tag2name:
                label+="-%s"%(tag2name[tag])
        label+="-%s"%outcome
        return label



    def serialize(self, input: List):
        """ Serializer that convert a list of Wyscout events in a list of standardized events.
        
        :param input: list containing the Wyscout events
        :return: list containing the standardized events
        """        
        events = []
        match_id = input[0]['matchId']
        possession_phases = get_play_actions(input,match_id)

        for phase in possession_phases:
            curr_phase_end = phase[0]
            curr_phase_id = possession_phases.index(phase)
            curr_phase_possessing_team = possessing_team(phase)
            curr_phase = phase
            try:
                next_phase = possession_phases[curr_phase_id+1]
            except IndexError:
                # this is the last phase of the match
                next_phase = None

            for event in phase[1]:

                if event['eventId']<0:
                    continue

                start = Point(event['positions'][0]['x'], event['positions'][0]['y'])
                try:
                    end = Point(event['positions'][1]['x'], event['positions'][1]['y'])
                except IndexError:
                    end = None

                tag_list = [tag['id'] for tag in event['tags']]

                calculated_outcome = self.get_outcome(event, input, curr_phase, next_phase, tag_list)

                event_label = self.get_label(event, tag_list, calculated_outcome)

                event_args = dict(
                    event_id = event['id'],
                    team_id = event['teamId'],
                    match_id = event['matchId'],
                    player_id = event['playerId'],
                    period = event['matchPeriod'],
                    timestamp = event['eventSec'],
                    start_position = start,
                    end_position = end,
                    outcome = calculated_outcome,
                    label = event_label,
                    tags = tag_list,
                    phase_id = curr_phase_id,
                    phase_end = curr_phase_end,
                    phase_possessing_team = curr_phase_possessing_team
                )

                # event is PossessionEvent
                if event['subEventId'] in POSSESSION_EVENTS:
                    poss_event_args = dict()
                    if event['eventId'] in [10,3]:
                        goal_flag = (101 in tag_list)
                        position = self.get_goal_position(event)
                        shot_flag = (position != None)
                        poss_event_args = dict(
                            is_shot = shot_flag,
                            goal_position = position,
                            is_goal = goal_flag,                        
                        )
                    elif event['eventId'] == 8:
                        receiver = self.get_receiver(event, tag_list, input)
                        assist_flag = (301 in tag_list)
                        keypass_flag = (302 in tag_list)
                        poss_event_args = dict(
                            is_pass = True,
                            receiver_player_id = receiver,
                            is_assist = assist_flag,
                            is_keypass = keypass_flag
                        )
                    elif event['eventId'] == 1:
                        challenged = self.get_challenged_player(input.index(event),input)
                        poss_event_args = dict (
                            is_duel = True,
                            challenged_player = challenged
                        )
                    serialized_event = PossessionEvent(**poss_event_args, **event_args)
                
                # event is NotPossessionEvent
                else:
                    not_poss_event_args = dict()
                    if event['eventId'] == 1:
                        challenged = self.get_challenged_player(input.index(event),input)
                        not_poss_event_args = dict(
                            is_duel = True,
                            challenged_player = challenged
                        )
                    elif event['eventId'] == 2:
                        if 1701 in tag_list:
                            card = 'red card'
                        elif 1702 in tag_list:
                            card = 'yellow card'
                        elif 1703 in tag_list:
                            card = 'second yellow card'
                        else:
                            card = None
                        not_poss_event_args = dict(
                            is_foul = True,
                            card = card
                        )
                    serialized_event = NotPossessionEvent(**event_args, **not_poss_event_args)
                
                events.append(serialized_event)
        
        print ("[WyscoutEventSerializer] event serialized. %s events processed"%(len(events)))

        return events


    def get_team_possession_time (self, events: List, team: int) -> float:
        """ Function that computes the possession time of a single team

        :param events: the list of events
        :param team: the team whose possession is computed
        :return: the minutes of possession
        """
        begin_time, total_time = 0, 0
        curr_phase = None
        curr_period = '1H'
        for event in events:
            if curr_phase == event.phase_id:
                curr_time = event.timestamp
                continue
            
            if curr_period != event.period:
                phase_time = curr_time - begin_time
                total_time += phase_time

                curr_phase = event.phase_id
                begin_time = event.timestamp
                curr_period = event.period

            elif event.phase_possessing_team == team:
                curr_phase = event.phase_id
                begin_time = event.timestamp
                curr_period = event.period
            else:
                phase_time = event.timestamp - begin_time
                total_time += phase_time
            
        return total_time