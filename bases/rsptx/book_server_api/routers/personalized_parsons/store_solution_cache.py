import sqlite3
import os
def create_cache(db_path):
    if not os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS existing_personalized_solution_fix (
                    id INTEGER PRIMARY KEY,
                    buggy_code TEXT,
                    personalized_solution TEXT
                )
            ''')
        print("Cache created")

def add_personalized_code(buggy_code, personalized_solution, db_path="personalized_solution_cache.db"):
    # check if dp_path exists
    create_cache(db_path)
    # Check if the buggy_code already exists
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*)
            FROM existing_personalized_solution_fix
            WHERE buggy_code = ?
        ''', (buggy_code,))

        count_existing = cursor.fetchone()[0]

        if count_existing == 0:
            # If the buggy_code does not exist, then insert the record
            cursor.execute('''
                INSERT INTO existing_personalized_solution_fix (buggy_code, personalized_solution)
                VALUES (?, ?)
            ''', (buggy_code, personalized_solution))
            conn.commit()
            print("Record added successfully.")
        else:
            # If the buggy_code already exists, do not add the record
            print("Record with the same buggy_code already exists. Not adding.")


def get_solution_from_cache(buggy_code, db_path="personalized_solution_cache.db"):
    create_cache(db_path)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
    SELECT personalized_solution FROM existing_personalized_solution_fix
    WHERE buggy_code = ?
    ''', (buggy_code,))
        result = cursor.fetchone()
        print("result-get_solution", result)
        return result[0] if result else None