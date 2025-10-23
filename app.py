from flask import Flask, render_template

app = Flask(__name__)

# Import routes after app initialization
from routes import *

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
