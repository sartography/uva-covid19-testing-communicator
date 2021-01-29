from sqlalchemy import func

from communicator import db
import marshmallow
from marshmallow import EXCLUDE
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from communicator.models.notification import Notification


class IvyFile(db.Model):
    file_name = db.Column(db.String, primary_key=True)
    date_added = db.Column(db.DateTime(timezone=True), default=func.now())
    sample_count = db.Column(db.Integer)
class IvyFileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = IvyFile
        load_instance = True
        include_relationships = True
        include_fk = True  # Includes foreign keys
 
