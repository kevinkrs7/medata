""" 
** backend documentation: **

1. [[__init__.py]]
2. [[acm_scraper.py]]
3. [[api.py]]
4. [[app.py]]
5. [[create_init_data.py]]
6. [[models.py]]

------
"""

""" 
** app.py ** 
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from models import db
from api import api
from create_init_data import create_init_data



#configuration
DEBUG = True

#instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
#/// for relative location of db file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(api)

#enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


#create real data
#try:
#    with app.app_context():
#        db.create_all()
#        create_init_data()
#except Exception as e:
#    print(e)



if __name__ == '__main__':
    app.run(host = "0.0.0.0")
