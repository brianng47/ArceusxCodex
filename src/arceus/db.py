from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from arceus.config import Settings


def connect(settings: Settings) -> psycopg.Connection:
    return psycopg.connect(settings.database_url, row_factory=dict_row)
