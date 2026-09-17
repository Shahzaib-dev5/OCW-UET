from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.mysql import BIGINT

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()

BigIntegerUnsigned = BIGINT(unsigned=True)
