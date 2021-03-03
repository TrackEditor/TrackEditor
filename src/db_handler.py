import sqlite3
import logging
import pandas as pd

LOGGER = logging.getLogger(__name__)


class DbHandler:
    def __init__(self):
        self.conn = None
        self.cur = None

    def open_db(self):
        self.conn = sqlite3.connect('db_track_editor.sqlite')
        self.cur = self.conn.cursor()
        try:
            self.cur.execute("""CREATE TABLE Tiles (zoom INTEGER,
                                                       x INTEGER,
                                                       y INTEGER,
                                                  status BOOLEAN,
                                                    path TEXT,
                                                    size INTEGER)
                             """)
        except sqlite3.OperationalError as e:
            if 'table Tiles already exists' in str(e):
                LOGGER.info(e)
            else:
                LOGGER.error(f'Unexpected error initializing database: {e}')
                return False

        return True

    def close_db(self):
        self.cur.close()

    def insert_tile(self, zoom: int, xtile: int, ytile: int, status: bool,
                    path: str, size: int):
        if not self.cur or not self.conn:
            LOGGER.error('No connection with data base')
            return False  # not connected

        if not status:
            size = 0

        if not self._tile_exists(zoom, xtile, ytile):
            query = """INSERT OR IGNORE INTO Tiles
                        (zoom, x, y, status, path, size)
                        VALUES(?, ?, ?, ?, ?, ?)
                    """
            self.cur.execute(query, (zoom, xtile, ytile, status, path, size))
            self.conn.commit()

        return True

    def clean_tiles(self):
        self.cur.execute('DROP TABLE IF EXISTS Tiles')
        self.conn.commit()

    def update_tile_status(self, zoom: int, xtile: int, ytile: int,
                           status: bool, size: int) -> bool:
        if not self.cur or not self.conn:
            LOGGER.error('No connection with data base')
            return False  # not connected

        query = """UPDATE Tiles SET
                        status=?,
                        size=?
                    WHERE
                        x=? AND
                        y=? AND
                        zoom=?
                """
        self.cur.execute(query, (status, size, xtile, ytile, zoom))
        self.conn.commit()
        return True

    def print_tiles(self, verbose=True) -> pd.DataFrame:
        query = 'SELECT * FROM Tiles'
        try:
            df_tiles = pd.read_sql(query, self.conn)

            if verbose:
                print(df_tiles)

            return df_tiles

        except pd.io.sql.DatabaseError as e:
            print('No Tiles db to print')
            if 'no such table: Tiles' in str(e):
                LOGGER.info(e)
            else:
                LOGGER.error(f'Unexpected error initializing database: {e}')
            return pd.DataFrame()

    def get_tile_size(self, zoom: int, xtile: int, ytile: int) -> int:
        if self._tile_exists(zoom, xtile, ytile):
            query = 'SELECT size FROM Tiles WHERE zoom=? AND x=? AND y=?'
            size_query = self.cur.execute(query, (zoom, xtile, ytile))
            size = size_query.fetchone()[0]
            return size
        else:
            return 0

    def get_tile_status(self, zoom: int, xtile: int, ytile: int) -> int:
        if self._tile_exists(zoom, xtile, ytile):
            query = 'SELECT status FROM Tiles WHERE zoom=? AND x=? AND y=?'
            status_query = self.cur.execute(query, (zoom, xtile, ytile))
            status = status_query.fetchone()[0]
            return status
        else:
            return 0

    def remove_tile(self, zoom: int, xtile: int, ytile: int) -> bool:
        if not self.cur or not self.conn:
            LOGGER.error('No connection with data base')
            return False  # not connected

        if self._tile_exists(zoom, xtile, ytile):
            query = 'DELETE FROM Tiles WHERE zoom=? AND x=? and y=?'
            self.cur.execute(query, (zoom, xtile, ytile))
            return True
        else:
            LOGGER.warning(
                f'Trying to remove non-existing tile: ({zoom},{xtile},{ytile})'
            )
            return False

    def _tile_exists(self, zoom: int, xtile: int, ytile: int) -> bool:
        if not self.cur or not self.conn:
            LOGGER.error('No connection with data base')
            return False  # not connected

        query = 'SELECT COUNT(*) FROM Tiles WHERE zoom=? AND x=? AND y=?'
        elements = self.cur.execute(query, (zoom, xtile, ytile))
        count = elements.fetchone()[0]
        if count == 1:
            return True
        elif count > 1:
            LOGGER.error(
                f'More than one coincidence for tile ({zoom},{xtile},{ytile})')
            return True
        else:
            LOGGER.warning(
                f'Input tile ({zoom},{xtile},{ytile}) is already in  db.')
            return False
