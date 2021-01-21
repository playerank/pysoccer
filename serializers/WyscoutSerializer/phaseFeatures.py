from scipy.spatial.distance import euclidean
import numpy as np
from joblib import dump, load
from pysoccer.serializers.WyscoutSerializer.phaseDetection import *


INTERRUPTION = 5
FOUL = 2
OFFSIDE = 6
DUEL = 1
SHOT = 10
SAVE_ATTEMPT = 91
REFLEXES = 90
TOUCH = 72
DANGEROUS_BALL_LOST = 2001
MISSED_BALL = 1302
PASS = 8
PENALTY = 35
ACCURATE_PASS = 1801


from scipy.spatial.distance import euclidean
import numpy as np

def possessing_team(phase):
    """
    returns the possessing team of the phase
    """

    possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,8,10]]
    if len(possessing_team) > 0:
        return max(set(possessing_team), key=possessing_team.count)
    return None

def players_involved(phase):
    """
    returns the players involved in each phase
    """

    players = []
    for ev in phase[1][:]:
        if ev["playerId"] != 0:
            players.append((ev["playerId"], ev["teamId"]))

    return players

def invasion(phase, verbose = False):
  """
  it computes the invasion of each possesion phase
  invasion index is the maximum closeness, across a possession phase, between the ball and opponents goal.
  it is the closest point, w.r.t. opponents goal, where the possessing team manages to bring the ball
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8,10] ]
  speeds = []
  if len(possessing_team)>0:
    start_ev = phase[1][0]
    start_pos = start_ev['positions'][0]
    start_time = start_ev['eventSec']

    max_cateto = 113
    max_distance = euclidean([100,164],[101,34])

    #formula for ang distance: ipotenusa * (ipotenusa/cateto)
    distances = []
    for ev in phase[1][:]:
      if ev['teamId']==possessing_team[0]:
        pos = [ev['positions'][0]['x'], ev['positions'][0]['y']*0.68]
        angle = euclidean(pos,[101,34]) / float(110 - pos[0])
        ang_dist = ((euclidean(pos,[101,34]) ) * angle )


        if verbose:
            print ("event pos", pos, " angular dist stop", ang_dist,
                  "max distance", max_distance )
        distances.append(max_distance - ang_dist)

    return max(distances)

def speed_step(phase):
  """
  it computes the space gain speed for each step of the phase. For each step (pass etc) it computes relative space gain / elapsed time
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8,10] ]
  speeds = []
  if len(possessing_team)>0:
    start_ev = phase[1][0]
    start_pos = start_ev['positions'][0]
    start_time = start_ev['eventSec']

    for ev in phase[1][1:]:
      if ev['teamId']==possessing_team[0]:
        pos = [ev['positions'][0]['x'], ev['positions'][0]['y']*0.68]
        angle_stop = euclidean(pos,[101,50*0.68]) / float(113 - pos[0])
        ang_dist_stop = ((euclidean(pos,[101,50*0.68]) ) * angle_stop )

        pos = [start_pos['x'], start_pos['y']*0.68]
        angular_start = euclidean(pos,[101,50*0.68]) / float(113 - pos[0])
        angular_dist_start = ((euclidean(pos,[101,50*0.68]) ) * angle_start )


        elapsed_time = ev['eventSec'] - start_time
        if elapsed_time > 0:
          if abs((angular_dist_stop - angular_dist_start)/elapsed_time)<100:
            speeds.append((angular_dist_stop - angular_dist_start)/elapsed_time)

        #update start
        start_pos = ev['positions'][0]
        start_time = ev['eventSec']

  return speeds



def pass_length(phase):
  """
  average lenght of all the passes within the phase
  """

  pass_l = []
  for e in phase[1]:
    if e['eventId'] == 8 and len(e['positions'])>1:
      pass_l.append(euclidean([e['positions'][0]['x'],e['positions'][0]['y']],[e['positions'][1]['x'],e['positions'][1]['y']]))

  if len(pass_l)>0:
    return np.mean(pass_l),max(pass_l)
  else:
    return 0,0

def phase_wideness(phase):
  """
  average and std y of each ball position to asses pitch usage on y dimension
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8]]
  if len(possessing_team)>0:
    y_pos = [x['positions'][0]['y'] for x in list(filter(lambda x:  x['teamId'] == possessing_team[0],phase[1]))]
    return np.mean(y_pos), np.std(y_pos)
  else:
    return 0,0


def duration(phase):
  """
  duration of possessing events
  """

  possessing_evts= [x for x in phase[1] if x['eventId'] in [3,7,8,10] ]
  if len(possessing_evts) > 0:
      return possessing_evts[-1]['eventSec']- possessing_evts[0]['eventSec']
  return 0

def timestamp(phase, offset):
  """
  return the absolute timestamp of the first event of the phase

  :param phase: a list of events corresponding to a possesion phase
  :param offest: dictionary with offset for each period of the match
  """
  
  return phase[1][0]['eventSec']+offset[phase[1][0]['matchPeriod']]

def start_x(phase):
  """
  return starting x position of the possesion phase
  """

  team = possessing_team(phase)
  if team:
      first_event = [x for x in phase[1] if x['teamId'] == team][0]

      return first_event['positions'][0]['x']
  return -1

def passes_direction(phase):
  """
  counting forward, lateral and back passes
  """

  fwpass, backpass, lateralpass = 0,0,0
  for e in phase[1]:
    if e['eventId'] == 8 and len(e['positions'])>1:
      delta_y = e['positions'][1]['y'] - e['positions'][0]['y']
      delta_x = e['positions'][1]['x'] - e['positions'][0]['x']
      if abs(delta_y)>abs(delta_x): lateralpass += 1
      elif delta_x > 0: fwpass += 1
      else: backpass += 1
  return fwpass,  lateralpass, backpass



def duels_count(phase):
  #count the duels for the possessing team
  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8]]
  if len(possessing_team)>0:
    return len(list(filter(lambda x: x['eventId'] == 1 and x['teamId'] != possessing_team[0],phase[1])))
  else:
    return 0

def duels(phase):
  """
  duels on 1st third: n. of passess conceded with origin x in [66,100]
  duels on 2nd third: n. of passess conceded with origin x in [33,66]
  duels on 3d third: n. of passess conceded with origin x in [0,33]
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8]]
  duels_1st_third, duels_2nd_third, duels_3d_third = 0, 0, 0
  for e in phase[1]:
    if len(possessing_team)>0:
      if e['eventId'] == DUEL and e['teamId'] != possessing_team[0]:
        if e['positions'][0]['x'] >= 66:
          duels_1st_third += 1
        elif e['positions'][0]['x'] >= 33:
            duels_2nd_third += 1
        else:
          duels_3d_third += 1
  return duels_1st_third, duels_2nd_third, duels_3d_third

def cleareances(phase):
  """
  cleareances: n. of clearances
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8]]
  if len(possessing_team)>0:
    try:
        return len(list(filter(lambda x: x['subEventId'] == 71 and x['teamId'] != possessing_team[0], phase[1])))
    except:
        print (phase[1])
        return 0
  else:
    return 0

def fouls(phase):
  """
  fouls: n. of fouls
  """

  return len(list(filter(lambda x: x['eventId'] == FOUL, phase[1])))

def d(start, stop):
  """
  angular distance difference between start ant stop events
  we consider first position as event position

  :param start: event positions
  :param stop: event positions
  """

  pos = [stop[0]['x'], stop[0]['y']*0.68]
  angle_stop = euclidean(pos,[101,50*0.68]) / float(113 - pos[0])
  angular_dist_stop = ((euclidean(pos,[101,50*0.68]) ) * angle_stop )

  pos = [start[0]['x'], start[0]['y']*0.68]
  angle_start = euclidean(pos,[101,50*0.68]) / float(113 - pos[0])
  angular_dist_start = ((euclidean(pos,[101,50*0.68]) ) * angle_start )

  return angular_dist_start - angular_dist_stop

def space_gain_speed(phase):
  """
  it computes space gained between start and tertile_i of the phase.
  It returns the speed in this segment of the phase.
  Segments are computed according to the duration
  """

  poss_team = possessing_team(phase)
  if poss_team:

    poss_team_events = [x for i,x in enumerate(phase[1]) if  x['teamId']==poss_team]
    #adding 0.1 second to avoid events recorded at the same time
    distances = [(d(poss_team_events[i-1]['positions'],x['positions']), x['eventSec']-poss_team_events[i-1]['eventSec']+0.1)
                for i,x in enumerate(poss_team_events) if i>0 ]

    tertile_idx =[i*3 for i in range(int(len(distances)/3)+1)]

    try:

        speed_tertile_1 = 0
        if len(tertile_idx)>1:

          speed_tertile_1 = np.mean([x[0]/x[1] for x in distances[ tertile_idx[0]: tertile_idx[1]]])

          if abs(speed_tertile_1)>30:
              speed_tertile_1 = 0 # outlier
        speed_tertile_2 = 0
        if len(tertile_idx)>2:
          speed_tertile_2 = np.mean([x[0]/x[1] for x in distances[ tertile_idx[1]: tertile_idx[2]]])
          if abs(speed_tertile_2)>20:
              speed_tertile_2 = 0 # outlier
        speed_tertile_3 = 0

        if len(tertile_idx)>3:
          speed_tertile_3 = np.mean([x[0]/x[1] for x in distances[ tertile_idx[2]: tertile_idx[3]]])
          if abs(speed_tertile_3)>10:
              speed_tertile_3 = 0 # outlier

        return speed_tertile_1, speed_tertile_2, speed_tertile_3

    except:
        print (tertile_idx)
        print (distances)

        raise
  return -1,-1, -1

def space_gain(phase):
  """
  it computes space gained between start and stop of the phase. It returns the gain and the final position of the phase
  """

  possessing_team = [x['teamId'] for x in phase[1] if x['eventId'] in [3,7,8,10] ]
  if len(possessing_team)>0:
    start,stop = [x['positions'] for x in phase[1] if x['teamId']==possessing_team[0]][0],[x['positions'] for x in phase[1] if x['teamId']==possessing_team[0]][-1]
    angular_dist_start = euclidean([start[0]['x'],start[0]['y']],[100,50])**2 / float(101 - start[0]['x'])
    angular_dist_stop = euclidean([stop[0]['x'],stop[0]['y']],[100,50])**2 / float(101 - stop[0]['x'])

    return angular_dist_stop - angular_dist_start, angular_dist_stop,[stop[0]['x'],stop[0]['y']]

  return -1,-1, -1


def shots_distance(phase):

  shots = list(filter(lambda x: x['eventId'] == 10,phase[1]))
  #formula: ipotenusa / cateto on short side * ipotenusa. shorter is better

  if len(shots)>0:
    pos = shots[-1]['positions']
    shots_angular_dist = euclidean([pos[0]['x'],pos[0]['y']*0.68],[100,50*0.68])**2 / (101 - pos[0]['x'])
  else:
    shots_angular_dist = -1

  return shots_angular_dist

def shots(phase):
  """
  shots: n. of shots conceded
  """

  return len(list(filter(lambda x: x['eventId'] == SHOT, phase[1])))

def goal_count(phase):
  """
  it counts the number of goals in a phase, excluding save attempts events (eventId = 9)
  """

  if len(list(filter(lambda x: (({'id':101} in x['tags'] or {'id':102} in x['tags'] ) and x['eventId'] != 9) ,phase[1]))) > 0:
    return 1
  else:
    return 0



def last_ball_location(shot,prev_events,time_window = 3):
  """
  it computes the average distance from shots location to previous <time_window> events.
  it could be useful to distinguish among high and low pressure situation

  :param shot: a shot event
  :param prev_Events: a list of previous events
  :param time_window: previous time window to consider (in seconds)
  """

  if shot["subEventId"]!=100:
    return -1
  shooting_team = shot["teamId"]
  prev_events = [x for x in prev_events if abs( x["eventSec"]-shot["eventSec"] )< time_window]
  distances = []
  for ev in prev_events:
    ev_pos = ev["positions"][0]
    if ev["teamId"]!=shooting_team:
      ev_pos["x"] = 100 - ev_pos["x"]
      ev_pos["y"] = 100 - ev_pos["y"]
    distances.append(euclidean([ev_pos["x"],ev_pos["y"]],
                                          [shot['positions'][0]['x'],shot['positions'][0]['y']]))

  return np.mean(distances) if len(distances)>0 else -1

def compute_shot_features(phase):
  """
  it computes the features of a shot / free kick event, for xg computation
  """

  shots_loc = []
  evt_list = [x for x in phase[1] if x['playerId'] != 0]
  for i,ev in enumerate(evt_list):

      if ev['subEventId'] in [33,35,100] : # freekick shot, penalty and shots
          doc = {}

          doc['event'] = ev['subEventName']
          doc['GOAL'] = {'id' : 101 } in ev['tags']

          doc['headed'] = {'id' : 403} in ev['tags']
          doc['opportunity'] = {'id' : 201} in ev['tags']
          x = ev['positions'][0]['x'] if ev['subEventName']!="Penalty" else 90
          y = ev['positions'][0]['y'] if ev['subEventName']!="Penalty" else 50
          doc["prev_ball_distance"] = last_ball_location(ev, evt_list[i-10:i])
          doc["distance"] = euclidean([x,y], [100,50])
          doc["player"] = ev["playerId"]
          ## looking for related goalkeeper
          if len(evt_list)>i+1 and evt_list[i+1]["eventId"] == 9:
              doc["goalkeeper"] = evt_list[i+1]["playerId"]
          shots_loc.append(doc)

  return shots_loc



def expected_goals(phase, model, label_encoder):
  """
  computing expected goals for a phase according to input model

  :param phase: phase object, tuple
  :param model: sklearn model
  """

  features = ['distance','opportunity','prev_ball_distance','event_label','headed']

  shots_list = compute_shot_features(phase)


  import pandas as pd
  if len(shots_list)>0:
      data = pd.DataFrame(shots_list)
      data["event_label"] = label_encoder.transform(data["event"])
      data['probability'] = model.predict_proba(data[features])[:,1]
      return np.max(data.probability)
  else:
      return 0


def create_xg_model(events_list,matches, tree_fname = "xg_model.joblib",
                      encoder_fname = "label_encoder.joblib"):
  """
  creation of a sklearn model
  """

  from tqdm import tqdm

  shots_list = []
  phase_list = []
  print ("computing shots features")
  for match_id in tqdm(matches):
      match_events = [x for x in events_list if x["matchId"]==match_id["wyId"]]
      if len(match_events) > 0:
          phase_list+= get_play_actions(match_events)


  for p in phase_list:
      shots_list+= compute_shot_features(p)

  from sklearn import preprocessing
  from sklearn import metrics
  from sklearn.model_selection import GridSearchCV
  from sklearn.tree import DecisionTreeClassifier
  import pandas as pd

  data_regression = pd.DataFrame(shots_list)
  data_regression['GOAL'] = data_regression['GOAL'].apply(int)
  event_label = preprocessing.LabelEncoder()
  data_regression["event_label"] = event_label.fit_transform(data_regression.event)
  features = ['distance','opportunity','prev_ball_distance','event_label','headed']

  X = data_regression[features].values
  y = data_regression['GOAL']

  param_dist = {"max_depth": [3,5,8,10,12,15],
            "max_features": range(1,len(features)),
            "min_samples_leaf": range(1,10),
            "criterion": ["gini", "entropy"]}

  clf_tree = GridSearchCV(DecisionTreeClassifier(), param_dist, scoring = "f1_weighted")

  clf_tree.fit(X,y)
  tree = clf_tree.best_estimator_
  tree.fit(X,y)
  data_regression["goal_predicted"] = tree.predict(data_regression[features])
  acc = metrics.accuracy_score(data_regression["GOAL"], data_regression["goal_predicted"])
  prec = metrics.precision_score(data_regression["GOAL"], data_regression["goal_predicted"],average = None)
  recall = metrics.recall_score(data_regression["GOAL"], data_regression["goal_predicted"], average = None)
  f1 = metrics.f1_score(data_regression["GOAL"], data_regression["goal_predicted"])

  print("The xg model performance for input dataset set")
  print("--------------------------------------")
  print('Accuracy is {}'.format(acc))
  print('Precision is {}'.format(prec))
  print('Recall score is {}'.format(recall))
  print('F1 score is {}'.format(f1))

  dump(tree, tree_fname)
  dump(event_label,encoder_fname)
  print ("xg_model stored on ",tree_fname)

  return tree, event_label
