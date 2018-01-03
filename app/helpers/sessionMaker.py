"""

Helper function that returns a session object

# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()

"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from database_setup import Base
import os
from contextlib import contextmanager

from settings import settings

def newSession():
	engine = create_engine(settings.DATABASE_URL)
	Base.metadata.bind = engine
	DBSession = sessionmaker(bind=engine)

	session = DBSession()

	return session


def scoppedSession():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)

    Session = scoped_session(DBSession)

    return Session

@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = newSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope_threaded(Thread_session):
    """Provide a transactional scope around a series of operations.
    This is for factory method threaded sessions where the
    factory is passed as an argument
    """
    session = Thread_session()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()