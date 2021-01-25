from abc import ABC, abstractmethod
from typing import List

from pysoccer.event import Event

class EventSerializer(ABC):
    """
    Class to wrap all the event serializers.
    """

    @abstractmethod
    def serialize(self, input: List):
        """Function that serializes the events given in input.
        """
        raise NotImplementedError

class MatchSerializer(ABC):
    """
    Class to wrap all the match serializers.
    """

    @abstractmethod
    def serialize(self, input: List):
        """Functoin that serializes the matches given in input.
        """
        raise NotImplementedError