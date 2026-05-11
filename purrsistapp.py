from app import app
from app.models import seed_cats


if __name__ == '__main__':
    with app.app_context():
        seed_cats()
        
    app.run(debug=True)

