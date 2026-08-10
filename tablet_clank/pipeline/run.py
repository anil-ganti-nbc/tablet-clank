import json
from dataclasses import asdict
from . import process

def execute(db, collector, fixture_mode=False):
    return process(db, collector, fixture_mode)
