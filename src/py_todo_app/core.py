from psycopg import Connection
from psycopg.rows import tuple_row


class TodoModel:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection
        if connection.row_factory is not tuple_row:
            name = type(self).__name__
            raise ValueError(
                f"{name} requires connection.row_factory to be psycopg.rows.tuple_row"
            )

    def add(self, text: str) -> int:
        with self.connection.cursor() as cur:
            cur.execute(
                "INSERT INTO todos (text, done) VALUES (%s, %s) RETURNING id",
                (text, False),
            )
            if todo_id := cur.fetchone():
                return todo_id[0]
            else:
                raise RuntimeError("Added todo id was not returned")

    def get_all(self) -> list[tuple[int, int, str, bool]]:
        with self.connection.cursor() as cur:
            cur.execute(
                "SELECT id, ROW_NUMBER() OVER (ORDER BY id) AS row_num, text, done FROM todos"
            )
            return cur.fetchall()

    def set_status(self, id: int, status: bool) -> bool:
        with self.connection.cursor() as cur:
            cur.execute("UPDATE todos SET done=%s WHERE id = %s", (status, id))
            return cur.rowcount == 1

    def remove(self, id: int) -> bool:
        with self.connection.cursor() as cur:
            cur.execute("DELETE FROM todos WHERE id = %s", (id,))
            return cur.rowcount == 1

    def remove_done(self) -> int:
        with self.connection.cursor() as cur:
            cur.execute("DELETE FROM todos WHERE done")
            return cur.rowcount
