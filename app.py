"""Coffee Snark HTTP API. POST /comment with coffee_type and datetime."""
import os
from pathlib import Path
import re
from typing import Annotated

from fastapi import FastAPI, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator

from generator import CoffeeModel, CommentGenerator, WEIGHTS


class BrewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    coffee_type: Annotated[str, Field(strict=True, min_length=1, max_length=80)]
    timestamp: AwareDatetime = Field(alias='datetime', description='ISO 8601 date-time with Z or an explicit UTC offset.')

    @field_validator('timestamp', mode='before')
    @classmethod
    def require_iso_string(cls, value):
        if not isinstance(value, str) or not re.fullmatch(
                r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,6})?)?(?:Z|[+-]\d{2}:\d{2})', value):
            raise ValueError('Use an ISO date-time with an offset, for example 2026-11-04T16:30:00+01:00.')
        return value


class CommentResponse(BaseModel):
    comment: str


def create_app(*, history_db=None, timezone=None, weights_path=None):
    model = CoffeeModel(weights_path or os.environ.get('WEIGHTS_PATH', WEIGHTS),
                        timezone or os.environ.get('COFFEE_TIMEZONE', 'Europe/Copenhagen'))
    history = history_db or os.environ.get('HISTORY_DB', str(Path(__file__).resolve().parent / 'data' / 'history.sqlite3'))
    generator = CommentGenerator(model, history)
    application = FastAPI(
        title='Coffee Snark', version='1.0.0',
        description='Generate a short, office-friendly coffee comment from the drink and local time.')
    application.state.generator = generator

    @application.get('/health')
    def health():
        return {'status': 'ok'}

    @application.get('/coffee-types')
    def coffee_types():
        return {'coffee_types': list(model.data['coffee_types']), 'timezone': str(model.timezone)}

    @application.post('/comment', response_model=CommentResponse)
    def comment(request: BrewRequest):
        try:
            text = generator.comment(request.coffee_type, request.timestamp)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return CommentResponse(comment=text)

    return application
