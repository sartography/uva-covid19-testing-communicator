from sqlalchemy import func
from datetime import datetime

import marshmallow
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from communicator import db
from communicator.models.notification import Notification
class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_added = db.Column(db.DateTime(timezone=False), default=func.now())
    amount = db.Column(db.Integer)
    notes = db.Column(db.String)
class DepositSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Deposit
        load_instance = True
        include_relationships = True
        include_fk = True  # Includes foreign keys