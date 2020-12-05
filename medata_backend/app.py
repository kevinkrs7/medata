from enum import unique
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_marshmallow import Marshmallow

from sqlalchemy.orm import backref


#configuration
DEBUG = True

#instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)
#/// for relative location of db file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#!! Order matters here, SQLAlchemy has to be installed first!
ma = Marshmallow(app)


#models
#__tablename__ needs to be used if refered to tabel not class name 
#
#
#
#Insights with all supported categories and all informations
#one2many relationship with informtion (one for each paperId)
#one2many realtionship with categories (onw row in categories for each supported category (more efficent soluton??))
class Insights(db.Model):
    __tablename__ = 'insights'
    #constructor
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))

    categories = db.relationship('Categories', backref = 'insights', lazy = True)
    information = db.relationship('Information', backref = 'insights', lazy = True)

    def to_dict(self):
        return dict(id = self.id,
        name = self.name,
        categories=[category.to_dict() for category in self.categories],
        information=[info.to_dict() for info in self.information]
        )

    def __repr__(self):

        return f'id: {self.id}, name: {self.name}'


class InsightSchema(ma.Schema):
    class Meta:
        #field which will be returned
        #categories and information are missing here

        fields = ("id", "name")

insight_schema = InsightSchema()
insights_schema = InsightSchema(many=True)


#table where all supported categories are listed
class Categories(db.Model):
    __tableninsame__ = 'categories'

    insightId = db.Column(db.Integer, db.ForeignKey('insights.id'))
    categoryId = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))

    
    def to_dict(self):
        return dict(category_name = self.name)

    def __repr__(self):
         return f'CategoryId: {self.categoryId}, name: {self.name}'

class CategoriesSchema(ma.Schema):
    class Meta:
        #field which will be returned
        fields = ("insightId", "categoryId", "name")

category_schema = CategoriesSchema()
categories_schema = CategoriesSchema(many=True)


#actual information, linked to paaperId and an insight 
#add author, articel no., title, publication date, update defaults!
class Information(db.Model):
    __tablename__ = 'information'

    insightId = db.Column(db.Integer, db.ForeignKey('insights.id'))
    paperId = db.Column(db.Integer, primary_key=True)
    #3 possible answers to insight with up- and downvotes
    answer1 = db.Column(db.String(30))
    answer1_upvotes = db.Column(db.Integer, default = 0)
    answer1_downvotes = db.Column(db.Integer, default = 0)
    answer2 = db.Column(db.String(30))
    answer2_upvotes = db.Column(db.Integer, default = 0)
    answer2_downvotes = db.Column(db.Integer, default = 0)
    answer3 = db.Column(db.String(30))
    answer3_upvotes = db.Column(db.Integer, default = 0)
    answer3_downvotes = db.Column(db.Integer, default = 0)
    #relevance of insight for specific paper
    insight_upvotes = db.Column(db.Integer, default = 0)
    insight_downvotes = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    def to_dict(self):
        return dict(
        paperId = self.paperId,
        answer1 = self.answer1,
        answer1_upvotes = self.answer1_upvotes,
        answer1_downvotes = self.answer1_downvotes,
        answer2 = self.answer2,
        answer2_upvotes = self.answer2_upvotes,
        answer2_downvotes = self.answer2_downvotes,
        answer3 = self.answer3,
        answer3_upvotes = self.answer3_upvotes,
        answer3_downvotes =self.answer3_downvotes,
        insight_upvotes = self.insight_upvotes,
        insight_downvotes = self.insight_downvotes
        )

    def __repr__(self):
         return f'insightId: {self.insightId}, paperId: {self.paperId}'

class InformationSchema(ma.Schema):
    class Meta:
        #fields which will be returned
        fields = ("insightId", "paperId", "answer1", "answer1_upvotes", "answer1_downvotes", 
        "answer2", "answer2_upvotes", "answer2_downvotes", "answer3", "answer3_upvotes", "answer3_downvotes",
        "insight_upvotes", "insight_downvotes", "timestamp")

information_schema = InformationSchema()
informations_schema = InformationSchema(many=True)



#enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


def remove_book(book_id):
    for book in BOOKS:
        if book['id'] == book_id:
            BOOKS.remove(book)
            return True
    return False


#sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

#example method
@app.route('/books', methods=['GET', 'POST'])
def all_books():
    response_object = {'status': 'success'}
    if request.method == 'POST':
        post_data = request.get_json()
        BOOKS.append({
            'id': uuid.uuid4().hex,
            'title': post_data.get('title'),
            'author': post_data.get('author'),
            'read': post_data.get('read')
        })
        response_object['message'] = 'Book added!'
    else:
        response_object['books'] = BOOKS
    return jsonify(response_object)

#example method
@app.route('/books/<book_id>', methods=['PUT', 'DELETE'])
def single_book(book_id):
    response_object = {'status': 'success'}
    if request.method == 'PUT':
        post_data = request.get_json()
        remove_book(book_id)
        BOOKS.append({
            'id': uuid.uuid4().hex,
            'title': post_data.get('title'),
            'author': post_data.get('author'),
            'read': post_data.get('read')
        })
        response_object['message'] = 'Book updated!'
    if request.method == 'DELETE':
        remove_book(book_id)
        response_object['message'] = 'Book removed!'
    return jsonify(response_object)


@app.route('/get_all', methods=['GET'])
def get_all():
    response_object = {'status':     'success'}
    print(Insights.query.count())
    for x in range(0,Insights.query.count()):
        response_object[f'insight {x}'] = Insights.query.get(x).to_dict()
    
    return jsonify(response_object)



@app.route('/get_specific', methods=['GET'])
def get_specific(paper_id, categories):
    response_object = {'status':     'success'}
    for x in range(0,Insights.query.count()):

        response_object[f'insight {x}'] = Insights.query.get(x).to_dict()
    
    return jsonify(response_object)



def test():
    #filters by one category and paperId
    #filter: 'and' but needs to be 'or'
    joined = Insights.query.join(Insights.categories).join(Insights.information).filter(Categories.name=='category3',
    Categories.name=='laboratory experiments').filter(Information.paperId==544).all()
    print(joined)


test()



@app.route('/all', methods = ["GET"])
def all_data():
    response_object = []
    all_categories = Categories.query.all()
    all_insights = Insights.query.all()
    all_information = Information.query.all()

    response_object.append(categories_schema.dump(all_categories))
    response_object.append(insights_schema.dump(all_insights))
    response_object.append(informations_schema.dump(all_information))
    #all data is added to a list which is called response object. This list is then serialized to JSON format 
    #Todo: maybe add titles | Problems:
    return jsonify(response_object)
    


if __name__ == '__main__':
    app.run()
