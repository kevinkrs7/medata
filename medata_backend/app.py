from enum import unique
import uuid

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
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
#one2many relationship with informtion (one for each paper_id)
#one2many realtionship with categories (onw row in categories for each supported category (more efficent soluton??))
class Insights(db.Model):
    __tablename__ = 'insights'
    #constructor
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)

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



#table where all supported categories are listed
class Categories(db.Model):
    __tablename__ = 'categories'

    insight_id = db.Column(db.Integer, db.ForeignKey('insights.id'))
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))

    
    def to_dict(self):
        return dict(category_name = self.name)

    def __repr__(self):
         return f'CategoryId: {self.category_id}, name: {self.name}'


#actual information, linked to paaperId and an insight 
#add author, articel no., title, publication date, update defaults!
class Information(db.Model):
    __tablename__ = 'information'

    information_id = db.Column(db.Integer, primary_key=True)
    insight_id = db.Column(db.Integer, db.ForeignKey('insights.id'))
    insight_name = db.Column(db.String(30))
    paper_id = db.Column(db.Integer, default=0)
    insight_upvotes = db.Column(db.Integer, default = 0)
    insight_downvotes = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    answers = db.relationship('Answers', order_by = 'desc(Answers.answer_score)', backref = 'information', lazy = True)

    def to_dict(self):
        return dict(id = self.insight_id,
        name = self.insight_name, 
        paper_id = self.paper_id,
        insight_upvotes = self.insight_upvotes,
        insight_downvotes = self.insight_downvotes,
        #answer = [answer.to_dict() for answer in self.answers]
        answer = self.limit_answers()
        )

    def limit_answers(self):
        four_answers = Answers.query.filter(Answers.information_id==self.information_id).order_by(Answers.answer_score.desc()).limit(4).all()
        return [answer.to_dict() for answer in four_answers]

    def __repr__(self):
         return f'insight_id: {self.insight_id}, paper_id: {self.paper_id}'


class Answers(db.Model):
    __tablename__ = 'answers'

    answer_id = db.Column(db.Integer, primary_key=True)
    information_id = db.Column(db.Integer, db.ForeignKey('information.information_id'), nullable=False)
    answer = db.Column(db.String(30), default = "")
    answer_upvotes = db.Column(db.Integer, default = 0)
    answer_downvotes = db.Column(db.Integer, default = 0)
    answer_score = db.Column(db.Integer, default = 0)

    def to_dict(self):
        return dict(
        answer = self.answer,
        answer_upvotes = self.answer_upvotes,
        answer_downvotes = self.answer_downvotes,
        )

    def __repr__(self):
        return f'answer: {self.answer}, answer_upvotes: {self.answer_upvotes}, answer_downvotes: {self.answer_downvotes}'


#enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})


#sanity check route
@app.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')

#test method, no application, returns db 
@app.route('/get_all', methods=['GET'])
def get_all():
    response_object = {'status':     'success'}
    print(Insights.query.count())
    for x in range(0,Insights.query.count()):
        response_object[f'insight {x}'] = Insights.query.get(x).to_dict()
    
    return jsonify(response_object)


#returns relevant insights with information
#step1: get id's of all supported insights
#step2: if (information for paper_id does not exist) create information with paper_id
#setp3: get relevant information (paper_id==paper_id)
@app.route('/get_specific', methods=['POST'])
def get_specific():
    url = request.get_json().get('url')
    response_object = []
    response_object.append({'status':     'success'})
    relevant_categories = ['laboratory experiments']
    paper_id = 50
    
    #step1 information filtered by category
    matching_insight = Insights.query.join(Insights.categories).filter(or_(Categories.name==x for x in relevant_categories)).all()

    #step 2
    for x in matching_insight:
        if (Information.query.filter(Information.insight_id==int(x.id)).filter(Information.paper_id==paper_id).count()==0):
            i = Information(insight_id = x.id, insight_name=x.name, paper_id=paper_id)
            db.session.add(i)
    db.session.commit()

    #step3 information filtered by (paper)id
    filtered_information_all = Information.query.filter(or_(Information.insight_id==int(x.id) for x in matching_insight)).filter(Information.paper_id==paper_id).all()
    for x in filtered_information_all:
        response_object.append(x.to_dict())

    return jsonify(response_object)
    
#adds insight for specific categories    
@app.route('/add_insight', methods =["POST"])
def add_insight():
    response_object = {'status': 'success'}
    post_data = request.get_json()
    in_insight_name = post_data.get('insight')
    in_categories = post_data.get('categories')
    in_paper_id = post_data.get('paper_id')

    #if insight does not yet exist, add insight, add categories
    if (Insights.query.filter(Insights.name==in_insight_name).count()==0):
        i = Insights(name = str(in_insight_name))
        db.session.add(i)
        db.session.commit()
        for category in in_categories:
            c = Categories(insight_id = i.id, name = str(category))
            db.session.add(c)
        inf = Information(insight_id=i.id, insight_name=i.name, paper_id=in_paper_id)
        db.session.add(inf)
        db.session.commit()
    #if insight already exists, add categories if they do no yet exist
    else:
        i = Insights.query.filter(Insights.name==in_insight_name).first()
        for category in in_categories:
            #check if category already exists, if not -> add, answer logic needs to be added here
            if (Categories.query.filter(Categories.insight_id==i.id).filter(Categories.name == str(category)).count()==0):
                c = Categories(insight_id = i.id, name = str(category))
                db.session.add(c)
        db.session.commit()
    return jsonify(response_object)

#adds answer to specific insight(information)        
@app.route('/add_answer', methods = ["POST"])
def add_answer():
    response_object = {'status': 'success'}
    post_data = request.get_json()
    in_paper_id = post_data.get('paper_id')
    in_insight_name = post_data.get('insight')
    in_answer = post_data.get('answer')
    #get relevant information repr
    inf = Information.query.filter(Information.paper_id==in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()
    #get all answers for information
    ans = Answers.query.filter(Answers.information_id==inf.information_id).all()
    print(inf)
    print(ans)
    answer_already_exists = False

    for a in ans:
        if (a.answer==in_answer):
            answer_already_exists = True

    if (answer_already_exists==False):
        new_answer = Answers(information_id=inf.information_id, answer = in_answer, answer_upvotes = 1, answer_score = 1)
        db.session.add(new_answer)
        db.session.commit()

    return jsonify(response_object)

#rates answer of specific insight(information)
@app.route('/rate_answer', methods = ["POST"])
def rate_answer():
    response_object = {'status': 'success'}
    put_data = request.get_json()
    in_insight_name = put_data.get('insight')
    in_paper_id = put_data.get('paper_id')
    in_upvote = put_data.get('upvote')
    in_answer =put_data.get('answer')

    #get relevant information repr
    inf = Information.query.filter(Information.paper_id == in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()
    #get answers
    ans = Answers.query.filter(Answers.information_id==inf.information_id).all()

    #upvote correct answer
    if (in_upvote):
        for a in ans:
            if (a.answer==in_answer):
                a.answer_upvotes = a.answer_upvotes + 1
                a.answer_score = a.answer_score + 1

    #downvote correct answer
    else :
        for a in ans:
            if (a.answer==in_answer):
                a.answer_upvotes = a.answer_upvotes - 1
                a.answer_score = a.answer_score - 1
    db.session.commit()
    return jsonify(response_object)

#rates ralevance of specific insight(information)
@app.route('/rate_relevance_insight', methods = ["POST"])
def rate_relevance_insight():
    response_object = {'status': 'success'}
    put_data = request.get_json()
    in_insight_name = put_data.get('insight')
    in_paper_id = put_data.get('paper_id')
    in_upvote = put_data.get('upvote')
    #get relevant information repr
    inf = Information.query.filter(Information.paper_id == in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()

    #upvote insight
    if (in_upvote):
        inf.insight_upvotes = inf.insight_upvotes + 1
    #downvote insight
    else :
        inf.insight_upvotes = inf.insight_upvotes - 1
    db.session.commit()

    return jsonify(response_object)

    


if __name__ == '__main__':
    app.run()
