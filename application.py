from flask import Flask
from dotenv import load_dotenv
from extensions.database import db, jwt
from api.routes import register_routes
import os
import logging

load_dotenv()

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

application = Flask(__name__)



application.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')

db.init_app(application)
jwt.init_app(application)


register_routes(application)

with application.app_context():
    db.create_all() 

if __name__ == '__main__':
    application.run(host = "0.0.0.0", port = 5000, debug = True)
