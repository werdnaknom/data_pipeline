from __future__ import annotations

import typing as t
from collections import OrderedDict
from dataclasses import dataclass, asdict, field

import datetime

IDTYPE = t.Optional[str]


@dataclass
class _EntityBase:
    _id: IDTYPE = None
    modified_date: datetime.datetime = field(
        default=datetime.datetime.utcnow(), repr=False, compare=False)
    created_date: datetime.datetime = field(
        default=datetime.datetime.utcnow(), repr=False, compare=False)

    @classmethod
    def get_type(cls):
        return cls._type

    @classmethod
    def get_collection(cls):
        return cls.get_type()


@dataclass
class Entity:

    @property
    def descriptor(self) -> str:
        raise NotImplementedError

    @classmethod
    def format_without_spaces(cls, word: str):
        return word.replace(" ", "")

    @classmethod
    def format_id(cls, **kwargs) -> str:
        raise NotImplementedError

    @classmethod
    def _from_dict(cls, adict: dict) -> Entity:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, adict: dict) -> Entity:
        return cls(**adict)

    def to_dict(self) -> dict:
        return asdict(self)

    def get_filter(self) -> dict:
        raise NotImplementedError

    @classmethod
    def search_filter(cls, **kwargs) -> dict:
        raise NotImplementedError

    @classmethod
    def from_dataframe_row(cls, df_row) -> Entity:
        raise NotImplementedError

    def to_result(self) -> OrderedDict:
        raise NotImplementedError

    @classmethod
    def format_test_category(cls, word: str):
        return word.replace(" ", "").lower()

    @classmethod
    def verify_int_not_valueError(cls, input: int):
        '''
        Some inputs are empty fields (np.NaN) which cannot be converted to
        ints.  This function replaces them with a float value, although we
        could do a random int (i.e. -999999)

        @param input:
        @return:
        '''
        try:
            result = int(input)
        except ValueError:
            result = float(input)
        return result
