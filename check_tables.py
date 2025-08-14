#!/usr/bin/env python3
from crunevo.app import create_app
from crunevo.extensions import db
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Total tables: {len(tables)}")
    print(f"Forum question table exists: {'forum_question' in tables}")
    print(f"Forum answer table exists: {'forum_answer' in tables}")
    print(f"Forum tag table exists: {'forum_tag' in tables}")

    if "forum_question" not in tables:
        print("\nForum tables are missing! Need to run migrations.")
    else:
        print("\nForum tables exist.")

    # Try to query forum question to see if there are any other issues
    try:
        from crunevo.models.forum import ForumQuestion

        count = ForumQuestion.query.count()
        print(f"Forum questions count: {count}")
    except Exception as e:
        print(f"Error querying forum questions: {e}")
