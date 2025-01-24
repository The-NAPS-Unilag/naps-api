from app.extensions import ma
from app.models.api_key import APIKey

class APIKeySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = APIKey
        load_instance = True