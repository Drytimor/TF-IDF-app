import db


def init_db():
    db.Base.metadata.create_all(bind=db.engine)




if __name__ == "__main__":
    init_db()