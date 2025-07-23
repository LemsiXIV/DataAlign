from app import create_app, db

# Create Flask app using the app factory
app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

