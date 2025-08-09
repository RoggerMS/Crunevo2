from crunevo.app import create_app

# Create a Flask app instance specifically for CLI commands
# This is separate from the WSGI application which uses DispatcherMiddleware
app = create_app()

if __name__ == "__main__":
    app.run()
