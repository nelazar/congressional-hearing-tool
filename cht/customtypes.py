"""
Types defined for this specific tool
"""


from typing import TypedDict, Literal


class Congress(TypedDict):
    congress: int
    total: int
    parsed: int
    txts: int
    pdfs: int
    xmls: int


class File(TypedDict):
    id: str
    congress: str
    format: Literal['txt', 'pdf', 'xml']