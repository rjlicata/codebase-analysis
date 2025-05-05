from typing import Any, Dict, List, Tuple

import psycopg2

TABLES = {
    "files": """CREATE TABLE IF NOT EXISTS files (
        id SERIAL PRIMARY KEY,
        path TEXT NOT NULL
    );""",
    "functions": """CREATE TABLE IF NOT EXISTS functions (
        id SERIAL PRIMARY KEY,
        file_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        summary TEXT,
        embedding VECTOR(),
        FOREIGN KEY (file_id) REFERENCES files(id)
    );""",
    "classes": """CREATE TABLE IF NOT EXISTS classes (
        id SERIAL PRIMARY KEY,
        file_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        summary TEXT,
        embedding VECTOR(),
        FOREIGN KEY (file_id) REFERENCES files(id)
    );""",
    "methods": """CREATE TABLE IF NOT EXISTS methods (
        id SERIAL PRIMARY KEY,
        class_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        summary TEXT,
        embedding VECTOR(),
        FOREIGN KEY (class_id) REFERENCES classes(id)
    );""",
}


class dbHandler:
    """Database handler class to manage database connections and operations"""

    def __init__(self, config: Dict[str, Any], embedding_dim: int = 384, init: bool = True):
        """initialize the database handler with the given configuration.

        :param config: database config
        :type config: Dict[str, Any]
        :param embedding_dim: dimension of the embedding, defaults to 384
        :type embedding_dim: int, optional
        :param init: whether to initialize the database, defaults to True
        :type init: bool, optional
        """
        self.config = config
        self._embedding_dim = embedding_dim
        self.conn = None
        self.cursor = None
        self.connect(init=init)

    def connect(self, init: bool):
        """establish a connection to the PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.config["name"],
                user=self.config["user"],
                password=self.config["password"],
                host=self.config["host"],
                port=self.config["port"],
            )
            self.cursor = self.conn.cursor()
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            if init:
                self._create_tables()
                self.clear()
        except Exception as e:
            print(f"Error connecting to the database: {e}")

    def _create_tables(self):
        """create the necessary tables in the database."""
        for table_name, create_statement in TABLES.items():
            try:
                self.cursor.execute(
                    create_statement.replace("VECTOR()", f"VECTOR({self._embedding_dim})")
                )
                self.conn.commit()
            except Exception as e:
                print(f"Error creating table {table_name}: {e}")

    def clear(self):
        """clear all tables in the database."""
        try:
            self.cursor.execute("TRUNCATE files CASCADE;")
            self.conn.commit()
            print("All tables cleared successfully.")
        except Exception as e:
            # self.rollback()
            print("Error clearing tables:", e)

    def _add_file(self, path: str):
        """add a row to the specified table.

        :param table: Name of the table to insert into.
        :param columns: Comma-separated string of column names.
        :param values: Comma-separated string of values to insert.
        """
        try:
            self.cursor.execute(f"INSERT INTO files (path) VALUES ('{path}') RETURNING id;")
            _id = self.cursor.fetchone()[0]
            self.conn.commit()
            return _id
        except Exception as e:
            print(f"Error inserting into files: {e}")

    def _process_functions(self, functions: Dict[str, Any], file_id: int) -> Tuple[str, str]:
        """process functions to extract columns and values for insertion.

        :param functions: functions with their attributes
        :type functions: Dict[str, Any]
        :param file_id: id of the file to which the functions belong
        :type file_id: int
        :return: columns and values as strings for SQL insertion
        :rtype: Tuple[str, str]
        """
        for func, attrs in functions.items():
            try:
                self.cursor.execute(
                    f"INSERT INTO functions (file_id, name, code, summary, embedding) VALUES (%s, %s, %s, %s, %s);",
                    (file_id, func, attrs["text"], attrs["summary"], attrs["embedding"]),
                )
                self.conn.commit()
            except Exception as e:
                print(f"Error inserting into files: {e}")

    def _process_methods(self, methods: Dict[str, Any], class_id: int) -> Tuple[str, str]:
        """process functions to extract columns and values for insertion.

        :param functions: functions with their attributes
        :type functions: Dict[str, Any]
        :param class_id: id of the class to which the functions belong
        :type class_id: int
        :return: columns and values as strings for SQL insertion
        :rtype: Tuple[str, str]
        """
        for method, attrs in methods.items():
            try:
                self.cursor.execute(
                    f"INSERT INTO methods (class_id, name, code, summary, embedding) VALUES (%s, %s, %s, %s, %s);",
                    (class_id, method, attrs["text"], attrs["summary"], attrs["embedding"]),
                )
                self.conn.commit()
            except Exception as e:
                print(f"Error inserting into files: {e}")

    def _process_classes(self, classes: Dict[str, Any], file_id: int) -> Tuple[str, str]:
        """process functions to extract columns and values for insertion.

        :param functions: functions with their attributes
        :type functions: Dict[str, Any]
        :param file_id: id of the file to which the functions belong
        :type file_id: int
        :return: columns and values as strings for SQL insertion
        :rtype: Tuple[str, str]
        """
        for _class, attrs in classes.items():
            try:
                self.cursor.execute(
                    f"INSERT INTO classes (file_id, name, code, summary, embedding) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                    (file_id, _class, attrs["text"], attrs["summary"], attrs["embedding"]),
                )
                _id = self.cursor.fetchone()[0]
                self.conn.commit()
                self._process_methods(
                    attrs["methods"],
                    _id,
                )
            except Exception as e:
                print(f"Error inserting into files: {e}")

    def add_file(self, file_path: str, breakdown: Dict[str, Any]) -> None:
        """add a file to the database

        :param file_path: path to the file
        :type file_path: str
        :param breakdown: breakdown of the file
        :type breakdown: Dict[str, Any]
        """
        file_id = self._add_file(file_path)
        self._process_functions(breakdown["functions"], file_id)
        self._process_classes(breakdown["classes"], file_id)

    def _query_sim(self, table: str, vector: List[float]) -> List[Any]:
        """query the database for similar items based on the given vector

        :param table: table to query
        :type table: str
        :param vector: embedding vector to search for
        :type vector: List[float]
        :return: list of similar items
        :rtype: List[Any]
        """
        query = f"""
            SELECT *, (embedding <=> %s::vector) AS distance FROM {table}
            WHERE (embedding <=> %s::vector) <= 0.5
            ORDER BY distance
            LIMIT 3;
        """
        try:
            self.cursor.execute(query, (vector, vector))
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def run_similarity(self, vector: List[float]) -> Dict[int, Dict[str, str]]:
        """finds most similar functions, classes, and methods to the given vector

        :param vector: embedding vector to search for
        :type vector: List[float]
        :return: dictionary of results with their ids, names, code, and summary
        :rtype: Dict[int, Dict[str, str]]
        """
        results = {}
        for _type in ["functions", "classes", "methods"]:
            temp = self._query_sim(_type, vector)
            for row in temp:
                results[f"{_type}_{row[0]}"] = {
                    "id": row[0],
                    "name": row[2],
                    "code": row[3],
                    "summary": row[4],
                    "cos_dist": row[6],
                    "type": _type,
                }
        return results

    def run_basic_query(self, query: str) -> List[Any]:
        """query the database for similar items based on the given vector

        :param table: table to query
        :type table: str
        :param vector: embedding vector to search for
        :type vector: List[float]
        :return: list of similar items
        :rtype: List[Any]
        """
        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
