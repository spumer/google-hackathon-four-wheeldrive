from app import db

DATABASE = db.database
IGNORE = [model.get_meta().name for model in db.abstract_models]
