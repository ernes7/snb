"""Versus blueprint routes."""
from __future__ import annotations

from flask import render_template

from . import versus_bp
from .services import build_versus_page


@versus_bp.route('/versus')
def versus() -> str:
    data = build_versus_page()
    return render_template('versus.html', **data)
