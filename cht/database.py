"""
Functions to interact with the database
"""


import sqlite3 as sql
from pathlib import Path
from typing import Self
import traceback

from dotenv import load_dotenv

from cht.customtypes import Congress


class Database:

    def __init__(self) -> None:
        load_dotenv(Path("./data/.env"))

    def __enter__(self) -> Self:
        path = Path("./data/cht.db")
        self.connection = sql.connect(path)
        self.cursor = self.connection.cursor()
        return self
    
    def __exit__(self, exc_type, exc_value, tb) -> None:
        if exc_type is not None:
            traceback.print_exception(exc_type, exc_value, tb)
        self.connection.close()


    # Create the tables for the database or abort if they exist
    def create(self):
        pass


    ########## congresses table ##########
    # Get congresses
    def get_congresses(self) -> list[Congress]:
        return []