#!/usr/bin/env python

import logging

import openai
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from typing_extensions import Annotated

from .config import Settings, read_settings
from .crud import create_completion, get_completions
from .database import DbSession
from .schemas import Completion, CompletionCreate

app = FastAPI()


def _get_db_session():
    session = DbSession()
    try:
        yield session
    finally:
        session.close()


@app.get('/')
def root():
    return {'message': 'Hello World'}


@app.post('/', response_model=Completion)
def suggest_dinner_menus(
    ingredient: str,
    settings: Annotated[Settings, Depends(read_settings)],
    db_session: Session = Depends(_get_db_session)
):
    logger = logging.getLogger('uvicorn')
    completion_kwargs = {
        'model': settings.openai_completion_model_id,
        'prompt':
        _generate_prompt_to_suggest_dinner_menus(ingredient=ingredient),
        'temperature': settings.openai_completion_temperature
    }
    logger.info(f'completion_kwargs: {completion_kwargs}')
    completion_result = openai.Completion.create(**completion_kwargs)
    logger.info(f'completion_result: {completion_result}')
    return create_completion(
        db_session=db_session,
        completion=CompletionCreate(
            completion_model=completion_kwargs['model'],
            completion_prompt=completion_kwargs['prompt'],
            completion_temperature=completion_kwargs['temperature'],
            completion_result=completion_result
        )
    )


@app.get('/completions/', response_model=list[Completion])
def get_past_comletions(
    skip: int = 0, limit: int = 100,
        db_session: Session = Depends(_get_db_session)
):
    return get_completions(db_session=db_session, skip=skip, limit=limit)


def _generate_prompt_to_suggest_dinner_menus(ingredient: str):
    return f'''
Suggest dinner menus based on a given ingredient in 100 characters or less.

Ingredient: Chicken breasts
Menus: Grilled Chicken Caesar Salad or Chicken Alfredo Pasta
Ingredient: Tofu
Menus: Tofu Stir-Fry or Miso Soup with Tofu
Ingredient: {ingredient.capitalize()}
Menues: '''
