"""
fleaker_config
~~~~~~~~~~~~~~

Main entrypoint and the entire application for fleaker_config. All you can
really do is update a config, and view your config.
"""
from flask import jsonify, request
from fleaker import App


def create_app():
    """Create the standard app for ``fleaker_config`` and register the two
    routes required.
    """
    app = App.create_app(__name__)
    app.configure('.configs.settings')

    # yes, I should use blueprints; but I don't really care for such a small
    # toy app
    @app.route('/config')
    def get_config():
        """Get the current configuration of the app."""
        return jsonify(app.config)

    @app.route('/put_config', methods=['PUT'])
    def put_config():
        """Add to the current configuration of the app.

        Takes any JSON body and adds all keys to the configs with the provided
        values.
        """
        data = request.json()

        for key, val in data.items():
            app.config[key] = val

        return jsonify({'message': 'Config updated!'})

    return app

if __name__ == '__main__':
    create_app().run()
