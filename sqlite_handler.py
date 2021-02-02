import logging
import sqlite3
import sys

from settings import db, tables

logging.basicConfig(
    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s",
    level=logging.WARNING,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# create_persons = '''
# CREATE TABLE persons (id INTEGER PRIMARY KEY, tg_user INTEGER, name text, UNIQUE(tg_user, name) );
# '''
# test_persons = '''
# insert into  persons (name, tg_user) VALUES('William', 500);
# '''
# create_marks = '''
# CREATE TABLE MARKS (id INTEGER PRIMARY KEY, person_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, mark CHECK(mark == 1 or mark == -1), comment text, FOREIGN KEY (person_id)
#        REFERENCES persons (id) )
# '''

# test_marks = '''
# insert into marks (person_id, mark, comment) values(1, 2, 'cool');
# '''


def insert_new_person(table, **kwargs):
    try:
        table_fields = tables[table]
    except KeyError as e:
        logger.exception(e)
        return False
    if set(table_fields) != set(kwargs):
        logger.warning(
            f"table_fields not like kwargs: tf:{table_fields} | kw:{kwargs}"
        )
        return False
    with sqlite3.connect(db) as conn:
        query = f"insert into {table} ({','.join(table_fields)}) values ({','.join(['?']*len(table_fields))})"
        c = conn.cursor()
        c.execute(query, [kwargs[k] for k in table_fields])
        if c.rowcount > 0:
            return True
        else:
            False


def update_data(person_id, new_name):
    try:
        with sqlite3.connect(db) as conn:
            query = "update persons SET name = :new_name where id = :person_id"
            c = conn.cursor()
            c.execute(query, {"person_id": person_id, "new_name": new_name})
            return True
    except Exception as e:
        logger.exception(e)
        return False


def select_persons(tg_user):
    with sqlite3.connect(db) as conn:
        query = "select id, name from persons where tg_user=?"
        c = conn.cursor()
        c.execute(query, (tg_user,))
        return c.fetchall()


def insert_new_mark(person_id, mark, comment):
    try:
        with sqlite3.connect(db) as conn:
            query = (
                "insert into  marks (person_id, mark, comment) "
                "VALUES (:person_id, :mark, :comment)"
            )
            c = conn.cursor()
            c.execute(
                query,
                {"person_id": person_id, "mark": mark, "comment": comment},
            )
            logger.info("Я в инсерте")
            logger.warning(f"{person_id} {mark} {comment}")
            return True
    except Exception as e:
        logger.exception(e)
        return False


# insert_data("persons", **{"name": "Igor1", "tg_user": 12123122})
