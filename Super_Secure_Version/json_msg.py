import json
from enum import Enum

class CODES(Enum):
    SUCCESS = "SUCCESS"
    WRITE_BACK = "WRITE_BACK"
    NO_WRITE_BACK = "NO_WRITE_BACK"
    AUTHENTICATED = "AUTH"
    EXIT = "EXIT"
    ERROR = "ERROR"
    SALT = "SALT"  # New code for salt exchange

"""
This class holds a CODE and a string. It can be created from a json dict
or two strings. It can create a json representation of msg to send.
"""
class msg:
    def __init__(self, code: str, msg: str):
        """
        Initialize a Msg object with code and msg.
        """
        self.code = code
        self.msg = msg

    @classmethod
    def from_json_dict(cls, json_dict):
        """
        Create a Msg object from a JSON dictionary.
        """
        return cls(json_dict.get("code"), json_dict.get("msg"))

    def to_json_str(self) -> str:
        """
        Convert the Msg object to a JSON string.
        """
        return self.__str__()

    def to_dict(self) -> dict:
        """
        Convert the Msg object to a JSON string.
        """
        return json.loads(self.__str__())

    def __str__(self) -> str:
        """
        Return a string representation of the Msg object.
        """
        return f'{{"code": "{self.code}", "msg": "{self.msg}"}}'