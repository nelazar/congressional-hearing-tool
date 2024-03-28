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
    def create(self) -> None:
        
        # Create congresses table
        self.cursor.execute(
            """
            CREATE TABLE congresses (
                number          INT         PRIMARY KEY,
                total_docs      INT         NOT NULL,
                parsed_docs     INT         NOT NULL,
                txts            INT         NOT NULL,
                pdfs            INT         NOT NULL,
                xmls            INT         NOT NULL
            )
            """
        )

        # Create documents table
        self.cursor.execute(
            """
            CREATE TABLE documents (
                id              TEXT        PRIMARY KEY,
                title           TEXT        NOT NULL,
                committee       TEXT        NOT NULL,
                subcommittee    TEXT,
                congress        INT         NOT NULL,
                chairperson     TEXT,
                complete        INT         NOT NULL,

                FOREIGN KEY (congress) REFERENCES congress(number),
                FOREIGN KEY (chairperson) REFERENCES participants(id)
            )
            """
        )

        # Create legislators table
        self.cursor.execute(
            """
            CREATE TABLE legislators (
                bioguide        TEXT        NOT NULL,
                congress        INT         NOT NULL,
                first_name      TEXT        NOT NULL,
                last_name       TEXT        NOT NULL,
                gender          TEXT        NOT NULL,
                state           TEXT        NOT NULL,
                party           TEXT        NOT NULL,

                PRIMARY KEY (bioguide, congress)
            )
            """
        )

        # Create participants table
        self.cursor.execute(
            """
            CREATE TABLE participants (
                id              TEXT        PRIMARY KEY,
                first_name      TEXT        NOT NULL,
                last_name       TEXT        NOT NULL,
                title           TEXT,
                state           TEXT,
                role            TEXT        NOT NULL,
                bioguide        TEXT,

                FOREIGN KEY (bioguide) REFERENCES legislators(bioguide)
            )
            """
        )

        # Create participants-documents table
        self.cursor.execute(
            """
            CREATE TABLE participants_documents (
                participant     TEXT        NOT NULL,
                document        TEXT        NOT NULL,

                PRIMARY KEY (participant, document),

                FOREIGN KEY (participant) REFERENCES participants(id),
                FOREIGN KEY (document) REFERENCES documents(id)
            )
            """
        )

        # Create entries table
        self.cursor.execute(
            """
            CREATE TABLE entries (
                document        TEXT        NOT NULL,
                date            TEXT        NOT NULL,
                participant     TEXT,
                content         TEXT        NOT NULL,

                FOREIGN KEY (document) REFERENCES documents(id),
                FOREIGN KEY (participant) REFERENCES participants(id)
            )
            """
        )

        # Create file reference table
        self.cursor.execute(
            """
            CREATE TABLE files (
                id              TEXT        NOT NULL,
                format          TEXT        NOT NULL,
                congress        TEXT        NOT NULL,
                path            TEXT        NOT NULL,

                PRIMARY KEY (id, format),

                FOREIGN KEY (congress) REFERENCES congresses(number)
            )
            """
        )

    # Check if tables have been created yet
    def created(self) -> bool:
        tables = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        if len(tables) > 0:
            return True
        else:
            return False


    ########## congresses table ##########
    # Get congresses
    def get_congresses(self) -> list[Congress]:
        return []