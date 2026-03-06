from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digitization.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Example model for digitized items
class DigitizedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'created_at': str(self.created_at)
        }

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "Welcome to Digitization Project!"

@app.route('/items', methods=['GET'])
def get_items():
    items = DigitizedItem.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/items', methods=['POST'])
def add_item():
    data = request.get_json()
    new_item = DigitizedItem(
        title=data['title'],
        description=data.get('description'),
        file_path=data.get('file_path')
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201

if __name__ == '__main__':
    app.run(debug=True)