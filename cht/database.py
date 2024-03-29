"""
Functions to interact with the database
"""


import sqlite3 as sql
from typing import Self
import traceback
from pathlib import Path

from dotenv import load_dotenv

from cht import DOTENV_PATH, DB_PATH
from cht.customtypes import Congress, Participant, Document, File, format_str


class Database:

    def __init__(self) -> None:
        load_dotenv(DOTENV_PATH)

    def __enter__(self) -> Self:
        self.connection = sql.connect(DB_PATH)
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
                path            TEXT,

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


    # Get congresses
    # def get_congresses(self) -> list[Congress]:
    #     congresses = self.cursor.execute(
    #         """
    #         SELECT number, total_docs, parsed_docs, txts, pdfs, xmls
    #             FROM congresses ORDER BY number
    #         """
    #     ).fetchall()
    #     return [{'congress': row[0], 'total': row[1], 'parsed': row[2], 'txts': row[3],
    #              'pdfs': row[4], 'xmls': row[5]} for row in congresses]

    # # Check if congress in congresses
    # def has_congress(self, congress: int) -> bool:
    #     result = self.cursor.execute(
    #         "SELECT number FROM congresses WHERE number=?", (congress,)
    #     )

    #     return result is not None
    
    # # Add a new congress to the congresses database
    # def add_congress(self, congress: int, total: int) -> None:
    #     data = (congress, total, 0, 0, 0, 0)
    #     self.cursor.execute(
    #         "INSERT OR REPLACE INTO congresses VALUES (?, ?, ?, ?, ?, ?)", data
    #     )
    #     self.connection.commit()

    # # Update the document count for the given format
    # def update_congress_format(self, congress: int, format: format_str) -> None:
    #     documents = self.cursor.execute(
    #         "SELECT id FROM files WHERE format=? AND congress=?", (format, congress)
    #     ).fetchall()
    #     self.cursor.execute(
    #         f"UPDATE congresses SET {format}s=? WHERE number=?", (len(documents), congress)
    #     )
    #     self.connection.commit()
        

    # Get all congresses in documents table
    def get_documents_congresses(self) -> list[int]:
        response = self.cursor.execute(
            """
            SELECT DISTINCT congress FROM documents
            """
        ).fetchall()
        return list(map(lambda x: int(x[0]), response))

    # Get all document records
    def get_documents(self, congress: int|None=None, complete: bool|None=None) -> list[Document]:
        if congress is None and complete is None:
            response = self.cursor.execute(
                """
                SELECT id, title, committee, subcommittee, congress, chairperson, complete
                    FROM documents
                """
            ).fetchall()
        elif congress is None:
            response = self.cursor.execute(
                """
                SELECT id, title, committee, subcommittee, congress, chairperson, complete
                    FROM documents WHERE complete=?
                """, (complete,)
            ).fetchall()
        elif complete is None:
            response = self.cursor.execute(
                """
                SELECT id, title, committee, subcommittee, congress, chairperson, complete
                    FROM documents WHERE congress=?
                """, (congress,)
            ).fetchall()
        else:
            response = self.cursor.execute(
                """
                SELECT id, title, committee, subcommittee, congress, chairperson, complete
                    FROM documents WHERE congress=? AND complete=?
                """, (congress, complete)
            ).fetchall()
        result: list[Document] = []
        for row in response:
            chairperson = self.get_participant(row[5])
            is_complete = row[6] == 1
            document: Document = {
                'id': row[0],
                'title': row[1],
                'committee': row[2],
                'subcommittee': row[3],
                'congress': row[4],
                'chairperson': chairperson,
                'complete': is_complete
            }
            result.append(document)

        return result
    

    # Get participant by ID
    def get_participant(self, id: str) -> Participant | None:
        response = self.cursor.execute(
            """
            SELECT id, first_name, last_name, title, state, bioguide, role
                FROM participants WHERE id=?
            """, (id,)
        ).fetchone()
        if response is None:
            return None
        
        participant: Participant = {
            'id': response[0],
            'first_name': response[1],
            'last_name': response[2],
            'title': response[3],
            'state': response[4],
            'bioguide': response[5],
            'role': response[6]
        }

        return participant


    # Check if a document has already been downloaded
    def file_status(self, id: str, format: format_str) -> int:
        doc_path = self.cursor.execute(
            """
            SELECT path FROM files
                WHERE id=? AND format=?
            """, (id, format)
        ).fetchone()

        # If file has not be downloaded
        if doc_path is None or doc_path[0] is None:
            return 0
        else:

            # Check if file exists in path
            if Path(doc_path[0]).exists():
                return 1
            else:
                return 2

    # Insert a record of a downloaded file
    def add_file(self, id: str, format: format_str, congress: int, path: Path|None) -> None:
        data = (id, format, congress, str(path) if path is not None else None)
        self.cursor.execute(
            "INSERT OR IGNORE INTO files VALUES (?, ?, ?, ?)", data
        )
        self.connection.commit()

    # Delete a given file record
    def delete_file(self, id: str, format: format_str) -> None:
        self.cursor.execute(
            """
            DELETE FROM files WHERE id=? AND format=?
            """, (id, format)
        )
        self.connection.commit()

    # Get all congresses in files table
    def get_files_congresses(self, format: format_str|None=None) -> list[int]:
        if format is None:
            response = self.cursor.execute(
                """
                SELECT DISTINCT congress FROM files
                """
            ).fetchall()
        else:
            response = self.cursor.execute(
                """
                SELECT DISTINCT congress FROM files WHERE format=?
                """, (format,)
            )
        return list(map(lambda x: int(x[0]), response))

    # Get all text file records
    def get_files(self, format: format_str|None=None,
                  congress: int|None=None, downloaded: bool|None=None) -> list[File]:
        
        if format is None:
            if congress is None and downloaded is None: # All documents
                response = self.cursor.execute(
                    """
                    SELECT id, format, congress, path FROM files
                    """
                ).fetchall()
            elif congress is None:
                if downloaded: # All formats, all congresses, downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NOT NULL
                        """
                    ).fetchall()
                else: # All formats, all congresses, not downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NULL
                        """
                    ).fetchall()
            elif downloaded is None: # All formats, one congress, downloaded or not
                response = self.cursor.execute(
                    """
                    SELECT id, format, congress, path FROM files
                        WHERE congress=?
                    """, (congress,)
                ).fetchall()
            else:
                if downloaded: # All formats, one congress, downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NOT NULL AND congress=?
                        """, (congress,)
                    ).fetchall()
                else: # All formats, one congress, not downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NULL AND congress=?
                        """, (congress,)
                    ).fetchall()
        else:
            if congress is None and downloaded is None: # All documents
                response = self.cursor.execute(
                    """
                    SELECT id, format, congress, path FROM files
                    """
                ).fetchall()
            elif congress is None:
                if downloaded: # One format, all congresses, downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NOT NULL AND format=?
                        """, (format,)
                    ).fetchall()
                else: # One format, all congresses, not downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NULL AND format=?
                        """, (format,)
                    ).fetchall()
            elif downloaded is None: # One format, one congress, downloaded or not
                response = self.cursor.execute(
                    """
                    SELECT id, format, congress, path FROM files
                        WHERE congress=? AND format=?
                    """, (congress, format)
                ).fetchall()
            else:
                if downloaded: # One format, one congress, downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NOT NULL AND congress=? AND format=?
                        """, (congress, format)
                    ).fetchall()
                else: # One format, one congress, not downloaded
                    response = self.cursor.execute(
                        """
                        SELECT id, format, congress, path FROM files
                            WHERE path IS NULL AND congress=? AND format=?
                        """, (congress, format)
                    ).fetchall()
        
        return [{'id': row[0], 'format': row[1], 'congress': row[2],
                 'path': (Path(row[3]) if row[3] is not None else None)}
                for row in response]
    
    # Update the path of the given document
    def update_path(self, id: str, format: format_str, path: Path) -> None:
        self.cursor.execute(
            "UPDATE OR IGNORE files SET path=? WHERE id=? AND format=?", (str(path), id, format)
        )
        self.connection.commit()

    # Refresh file paths
    def refresh_paths(self):
        files = self.get_files()
        for file in files:
            if self.file_status(file['id'], file['format']) == 2: # File has been deleted/moved
                self.cursor.execute(
                    """
                    UPDATE files SET PATH=NULL WHERE id=? AND format=?
                    """, (file['id'], file['format'])
                )
                self.connection.commit()