"""Flask app factory for MVP Cuba 2011 Tournament Tracker."""
from __future__ import annotations

from flask import Flask, render_template

from config import configs
from lib.utils import format_ip
import db as database


def create_app(config_name: str = 'default') -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(configs[config_name])

    database.init_app(app)
    app.jinja_env.globals['format_ip'] = format_ip

    register_blueprints(app)
    register_error_handlers(app)

    return app


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from blueprints.main import main_bp
    from blueprints.teams import teams_bp
    from blueprints.players import players_bp
    from blueprints.schedule import schedule_bp
    from blueprints.games import games_bp
    from blueprints.draft import draft_bp
    from blueprints.playoffs import playoffs_bp
    from blueprints.leaders import leaders_bp
    from blueprints.team_stats import team_stats_bp
    from blueprints.mvp_race import mvp_race_bp
    from blueprints.antesala import antesala_bp
    from blueprints.weekly import weekly_bp
    from blueprints.periodico import periodico_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(players_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(games_bp)
    app.register_blueprint(draft_bp)
    app.register_blueprint(playoffs_bp)
    app.register_blueprint(leaders_bp)
    app.register_blueprint(team_stats_bp)
    app.register_blueprint(mvp_race_bp)
    app.register_blueprint(antesala_bp)
    app.register_blueprint(weekly_bp)
    app.register_blueprint(periodico_bp)


def register_error_handlers(app: Flask) -> None:
    """Register application-level error handlers."""
    @app.errorhandler(404)
    def not_found(e: Exception) -> tuple[str, int]:
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e: Exception) -> tuple[str, int]:
        return render_template('errors/500.html'), 500


if __name__ == '__main__':
    app = create_app('dev')
    app.run(debug=True, port=5000)
