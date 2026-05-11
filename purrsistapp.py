from app import create_app, db
from app.config import DeploymentConfig
from flask_migrate import Migrate
from app.models import seed_cats

app = create_app(DeploymentConfig)
migration = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        seed_cats()
        
    app.run(debug=True)

