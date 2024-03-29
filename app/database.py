#!/usr/bin/env python

import logging
import os

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from .config import read_settings


def execute_sql(sql, return_df=False):
    logger = logging.getLogger('uvicorn')
    logger.info(f'Executing SQL: {sql}')
    try:
        with DbSession() as s:
            df = pd.read_sql_query(text(sql), s.connection())
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    else:
        logger.debug(f'df:{os.linesep}{df}')
        if return_df:
            return df
        else:
            return df.to_dict(orient='records')


def _create_db_engine():
    settings = read_settings()
    return create_engine(
        '{0}://{1}:{2}@{3}:{4}/{5}'.format(
            'postgresql+psycopg2', settings.postgres_user,
            settings.postgres_password, settings.postgres_host,
            settings.postgres_port, settings.postgres_db
        ),
        echo=True
    )


def _create_db_session(engine):
    return scoped_session(
        sessionmaker(autocommit=False, autoflush=False, bind=engine)
    )


DbEngine = _create_db_engine()
DbSession = _create_db_session(engine=DbEngine)
DbBase = declarative_base()
