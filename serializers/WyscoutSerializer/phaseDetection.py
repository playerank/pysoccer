

## CONSTANTS IDENTIFYING PARTICULAR EVENTS
INTERRUPTION = 5
FOUL = 2
OFFSIDE = 6
DUEL = 1
SHOT = 10
SAVE_ATTEMPT = 91
REFLEXES = 90
TOUCH = 72
CLEARANCE = 71
DANGEROUS_BALL_LOST = 2001
MISSED_BALL = 1302
PASS = 8
PENALTY = 35
FREE_KICK_SHOT = 33
ACCURATE_PASS = 1801
GOAL, OWN_GOAL = 101,102

END_OF_GAME_EVENT = {
    u'eventName': -1,
    u'eventId': -1,
 u'eventSec': 7200,
 u'id': -1,
 u'matchId': -1,
 u'matchPeriod': u'END',
 u'playerId': -1,
 u'positions': [],
 u'subEventName': -1,
 u'subEventId': -2,
 u'tags': [],
 u'teamId': -1
}

START_OF_GAME_EVENT = {
    u'eventName': -2,
    u'eventId': -2,
 u'eventSec': 0,
 u'id': -2,
 u'matchId': -2,
 u'matchPeriod': u'START',
 u'playerId': -2,
 u'positions': [],
 u'subEventName': -2,
 u'subEventId': -2,
 u'tags': [],
 u'teamId': -2
}

START_2ND_HALF = {
    u'eventId': -2,
 u'eventSec': 0,
 u'id': -2,
 u'matchId': -2,
 u'matchPeriod': u'2H',
 u'playerId': -2,
 u'positions': [],
 u'subEventName': -2,
 u'subEventId': -2,
 u'tags': [],
 u'teamId': -2
}



def get_tag_list(event):
    return [tags_names_df[tags_names_df.Tag == tag['id']].Description.values[0] for tag in event['tags']]

def pre_process(events):
    """
    Duels appear in pairs in the streamflow: one event is by a team and the other by
    the opposing team. This can create
    """

    filtered_events, index, prev_event = [], 0, {'teamId': -1}

    while index < len(events) - 1:
        current_event, next_event = events[index], events[index + 1]

        # if it is a duel
        if current_event['eventId'] == DUEL:

            if current_event['teamId'] == prev_event['teamId']:
                filtered_events.append(current_event)
            else:
                filtered_events.append(next_event)
            index += 1

        else:
            # if it is not a duel, just add the event to the list
            filtered_events.append(current_event)
            prev_event = current_event

        index += 1
    return filtered_events

def is_interruption(event, current_half):
    """
    Verify whether or not an event is a game interruption. A game interruption can be due to
    a ball our of the field, a whistle by the referee, a fouls, an offside, a goal, the end of the
    first half or the end of the game.

    :param event: dict
        a dictionary describing the event
    :param current_half: str
        the current half of the match (1H = first half, 2H == second half)

    :return: True is the event is an interruption, False otherwise
    """

    event_id, match_period = event['eventId'], event['matchPeriod']

    if event_id in [INTERRUPTION, FOUL, OFFSIDE] or match_period != current_half or event_id == -1:

        return True
    return False

def is_pass(event):
    return event['eventId'] == PASS

def is_accurate_pass(event):
    return ACCURATE_PASS in [tag['id'] for tag in event['tags']]

def is_shot(event):
    """
    Verify whether or not the event is a shot. Sometimes, a play action can continue
    after a shot if the team gains again the ball. We account for this case by looking
    at the next events of the game.

    :param event: dict
        a dictionary describing the event

    :return: True is the event is a shot, False otherwise
    """

    event_id = event['eventId']
    return event_id == 10 or event["subEventId"] == FREE_KICK_SHOT


def is_goal(event):
    """
    Check if it is a goal or own goal. To detect sudden goal form not usual event types (touches acceleration whatever)
    """

    return GOAL in [tag['id'] for tag in event['tags']] or OWN_GOAL in [tag['id'] for tag in event['tags']]

def is_other(event):
    """
    Check for cleareance and touches
    """

    return event['subEventId'] == TOUCH or event['subEventId'] == CLEARANCE

def is_save_attempt(event):
    return event['subEventId'] == SAVE_ATTEMPT

def is_reflexes(event):
    return event['subEventId'] == REFLEXES

def is_touch(event):
    return event['subEventId'] == TOUCH

def is_duel(event):
    return event['eventId'] == DUEL

def is_ball_lost(event, previous_event):
    #if DANGEROUS_BALL_LOST in tags or MISSED_BALL in tags:
    #    return True
    #if event['eventName'] == PASS:
    #    if 'Not accurate' in tags:
    #        return True
    """
    note: not considering touch and cleareance as possession event
    """

    if previous_event is not None and event['teamId'] != previous_event['teamId'] and previous_event['teamId'] != -2 and event['eventId'] !=1 and event["subEventId"] not in [71,72]:
        return True

    return False

def is_penalty(event):
    return event['subEventId'] == PENALTY



def get_period_offset(db):

    events = list(filter(lambda x:  x['matchPeriod'] in ['1H', '2H'],db))
    available_periods = set([x['matchPeriod'] for x in events])
    half_offset = {'2H' : max([x['eventSec'] for x in events if x['matchPeriod']=='1H']),
                  '1H':0}
    if "E1" in available_periods:
        half_offset['E1'] = half_offset["2H"] + max([x['eventSec'] for x in events if x['matchPeriod']=='2H'])
    if "E2" in available_periods:
        half_offset['E2'] = half_offset["E1"] + max([x['eventSec'] for x in events if x['matchPeriod']=='E1'])
    if "P" in available_periods:
        half_offset['P'] = half_offset["E2"] + max([x['eventSec'] for x in events if x['matchPeriod']=='E2'])

    return half_offset

def get_play_actions(db, verbose=False):
    """
    Given a list of events of a single match,
    it splits the events
    into possession phases using the following principle:
    - an action begins when a team gains ball possession
    - an action ends if one of two cases occurs:
    -- there is interruption of the match, due to: 1) end of first half or match; 2) ball
    out of the field 3) offside 4) foul
    -- ball is played by the opposite team w.r.t. to the team who is owning the ball
    
    :return: a list, where each item is a tuple including:
        - event outcome: ball lost | shot | interruption | penalty
        - phase events list
    """

    try:

        events = list(filter(lambda x: x['matchPeriod'] in ['1H', '2H'],db)) #not considering extended time
        half_offset = {'2H' : max([x['eventSec'] for x in events if x['matchPeriod']=='1H']),
                      '1H':0}
        events = sorted(events, key = lambda x: x['eventSec'] + half_offset[x['matchPeriod']])
        first_secondhalf_evt = sorted(filter(lambda x: x['matchPeriod'] == '2H',events), key = lambda x: x['eventSec'])[0]
        ## add a fake event representing the start and end of the game and the second half start
        events.insert(0, START_OF_GAME_EVENT)
        events.insert(events.index(first_secondhalf_evt),START_2ND_HALF)
        events.append(END_OF_GAME_EVENT)

        play_actions = []

        time, index, current_action, current_half = 0.0, 1, [], '1H'
        previous_event = events[0]

        while index < len(events) - 2:

            current_event = events[index]


            # if the action stops by an game interruption
            if is_interruption(current_event, current_half):

                if current_event['eventId'] not in [-1,-2]: #delete fake events
                  current_action.append(current_event)
                play_actions.append(('interruption', current_action))
                current_action = []

            elif is_penalty(current_event):
                next_event = events[index + 1]

                if is_save_attempt(next_event) or is_reflexes(next_event):
                    index += 1
                    current_action.append(current_event)

                    play_actions.append(('penalty', current_action))
                    current_action = []
                else:
                    current_action.append(current_event)

            elif is_shot(current_event) or is_goal(current_event):
                next_event = events[index + 1]

                if is_interruption(next_event, current_half):
                    index += 1
                    current_action.append(current_event)
                    if next_event['eventId'] not in [-1,-2]: #delete fake events

                      current_action.append(next_event)
                    play_actions.append(('shot', current_action))
                    current_action = []

                if is_other(next_event): #deviation after shot.
                    index+=1

                    current_action.append(current_event)
                    current_action.append(next_event)
                    #if next_event["subEventId"] == 72 and next_event['eventSec'] == 522.294312:
                    #    print (current_action)
                    current_event = next_event
                    next_event = events[index + 1]

                ## IF THERE IS A SAVE ATTEMPT OR REFLEXES; GO TOGETHER
                if is_save_attempt(next_event) or is_reflexes(next_event) :
                    index += 1
                    current_action.append(current_event)
                    current_action.append(next_event)
                    play_actions.append(('shot', current_action))
                    current_action = []

                else:
                    current_action.append(current_event)
                    play_actions.append(('shot', current_action))
                    current_action = []

            elif is_ball_lost(current_event, previous_event):
                
                current_action.append(current_event)
                play_actions.append(('ball lost', current_action))
                current_action = [current_event]

            else:
                current_action.append(current_event)

            time = current_event['eventSec']
            current_half = current_event['matchPeriod']
            index += 1
            #previous_event = events[index-1]
            if not is_duel(current_event):
                previous_event = current_action[-1] if len(current_action) >0 else None

        events.remove(START_OF_GAME_EVENT)
        events.remove(END_OF_GAME_EVENT)
        events.remove(START_2ND_HALF)

        return play_actions
    except TypeError:

        return []
