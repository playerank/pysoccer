import abc

class Feature(object):
    """
    Class to wrap all the scripts/method to aggregate features from the database
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def createFeature(self,collectionName,param):
        """
        Method to define how a feature/set of features is computed.

        :param param: contains eventual parameters for querying database competion, subset of teams, whatever 
        :param collectionName: best practice: features have to be stored into a collection of documents in the form:
            {_id:
            {match: (numeric) unique identifier of the match,
            name: (string) name of the feature,
            entity: (string) name of the entity target of the aggregation. It could be teamId, playerID, teamID + role or whatever significant for an aggregation},
            value: (numeric) the count for the feature}

        :return: the name of the collection where the features have been stored
        """

        return 

class Aggregation(object):
    """
    Defines the methods to aggregate one/more collection of features  for each match
    it have to provide results as a dataframe, 
    e.g. it is used to compute relative feature for each match
    match -> team (or entity) -> featureTeam - featureOppositor  
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractproperty
    def get_features(self):
        
        return 'Should never get here'

    @abc.abstractproperty
    def set_features(self, collection_list):
        """
        Set the list of collection to use for relative features computing
        
        :param collection_list: list of collection. E.g. we could have a collection of quality features, one for quantity features, one for goals scored etc
        """

        return 
    
    @abc.abstractmethod
    def aggregate(self):
        """
        Merge the collections of feature and aggregate by match and team, computing the relative value for each team
        e.g. match -> team (or entity) -> featureTeam - featureOppositor
        
        :return: a dataframe 
        """

        return 