"""
Types defined for this specific tool
"""

from typing import TypedDict, Literal, Optional
from pathlib import Path


State = Literal['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
                'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
                'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
                'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
                'AS', 'DC', 'GU', 'MH', 'MP', 'PR', 'VI', '']


class Congress(TypedDict):
    congress: int
    total: int
    parsed: int
    txts: int
    pdfs: int
    xmls: int


class Participant(TypedDict):
    id: str
    first_name: str
    last_name: str
    title: Optional[str]
    state: Optional[State]
    bioguide: Optional[str]
    role: Literal['legislator', 'witness']


class Document(TypedDict):
    id: str
    title: str
    committee: str
    subcommittee: Optional[str]
    congress: int
    chairperson: Optional[Participant]
    complete: bool


class Legislator(TypedDict):
    bioguide: str
    congress: int
    first_name: str
    last_name: str
    gender: Literal['M', 'F', 'O', 'X']
    state: State
    party: Literal['D', 'I', 'R']


format_str = Literal['txt', 'pdf', 'xml']

class File(TypedDict):
    id: str
    congress: str
    format: format_str
    path: Optional[Path]