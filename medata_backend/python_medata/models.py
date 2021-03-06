""" 
** backend documentation: **

1. [[__init__.py]]
2. [[acm_scraper.py]]
3. [[api.py]]
4. [[app.py]]
5. [[create_init_data.py]]
6. [[models.py]]

------
"""

"""
** models.py ** 

* this module contains the model for our database
* variables like insight, categories etc. are always refered to with: ' '
* e.g.:
    * we have one 'insight' called "accuracy" 
    * this 'insight' supports the 'category' "supervised learning by classification"
    * on all acm papers in the 'category' "supervised learning by classification" exists one 'information' related to the 'insight'
    * all those 'information' can have multiple answers (because the value for accuracy is not the same in all papers)

** Classes: **

1. Insights 
2. Categories 
3. Information
4. Answers

------

"""

from enum import unique

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import backref

db = SQLAlchemy()


# === Insights ===
class Insights(db.Model):
    """ 
        ** Explanation: **

        * an 'insight' object has it's unique name
        * typo errors (e.g. spelling mistakes) are counted in typo_error
        * 'insight' has a one-to-many relationship with 'categories' -> one insight is supported for multiple 'categories'
        * 'insight' has a one-to-many relationship with 'information' -> 'information' saves additional data for a specific acm-paper (see 'information')
        * the to_dict method is very powerful and returns basically the whole db, used only for testing

    """
    __tablename__ = 'insights'  

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30), unique=True)
    typo_error = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    categories = db.relationship('Categories', backref = 'insights', lazy = True)
    information = db.relationship('Information', backref = 'insights', lazy = True)

    def to_dict(self):
        """ 
            ** Returns: **

            * json: returns name and all linked 'information' (with 'answers') and 'categories'
        """
        return dict(id = self.id,
        name = self.name,
        categories=[category.to_dict() for category in self.categories],
        information=[info.to_dict() for info in self.information]
        )

    def __repr__(self):
        return f'id: {self.id}, name: {self.name}'



# ---------------------------------------------------------
 
# === Categories ===
class Categories(db.Model):
    """ 

        **Explanation:**

        * 'categories' keep track of the supported categories for a specific 'insight'
        * 'categories' are linked to an insight via insight_id
        * name stores the name of the category
        * downvote_category indicates the relevance of an 'insight' for a specific 'category' (the less downvotes, the better)
        * to_dict is used only for testing

    """
    __tablename__ = 'categories'

    insight_id = db.Column(db.Integer, db.ForeignKey('insights.id'))
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    downvote_category = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    
    def to_dict(self):
        return dict(category_name = self.name)

    def __repr__(self):
         return f'category_id: {self.category_id}, insight_id: {self.insight_id}, name: {self.name}, downvote_category: {self.downvote_category}, timestamp: {self.timestamp} '


# ---------------------------------------------------------
 
# === Information ===
class Information(db.Model):
    """ 
    
        **Explanation:**

        * an 'information' is a more specific representation of an 'insight', which saves additional data related to one paper from acm
        * insight_id is determined by a foreign key, it links the 'information' with it's 'insight'
        * insight_name is doubled but necessary - otherwise we run into problems as two foreign keys are used
        * paper_id is the link to the paper stored as a String
        * insight_up/downvotes is selfexplanatory
        * title, authors, authors_profile_link and conference of the acm-paper are saved in our db
        * 'information' has a one-to-many relationship with 'answers'

    """
    __tablename__ = 'information'

    information_id = db.Column(db.Integer, primary_key=True)
    insight_id = db.Column(db.Integer, db.ForeignKey('insights.id'))
    insight_name = db.Column(db.String(30))
    #url -> String
    paper_id = db.Column(db.String(50), default = "")
    insight_upvotes = db.Column(db.Integer, default = 0)
    insight_downvotes = db.Column(db.Integer, default = 0)
    title = db.Column(db.String(200), default = "")
    authors = db.Column(db.String(200), default = "")
    authors_profile_link = db.Column(db.Text, default = "")
    conference = db.Column(db.String(200), default = "")
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    answers = db.relationship('Answers', order_by = 'desc(Answers.answer_score)', backref = 'information', lazy = True)

    def to_dict(self):
        """ 

            * answers are limited by limit_answers()

            **Returns:**

            * json: all relevant columns of 'information' and the for most relevant 'answers'
        """
        return dict(id = self.insight_id,
        name = self.insight_name, 
        paper_id = self.paper_id,
        title = self.title,
        conference = self.conference,
        authors = self.authors,
        authors_profile_link = self.authors_profile_link,
        insight_upvotes = self.insight_upvotes,
        insight_downvotes = self.insight_downvotes,
        answer = self.limit_answers()
        )

    def limit_answers(self):
        """ 
        
            * limit the returned 'answers' to answer_limit

            **Returns:**

            * list: of answer.to_dict() ranked by descending answer score, if two 'answers' have the same score, the newer one is preferred 
        """
        answer_limit = 4
        limited_answers = Answers.query.filter(Answers.information_id==self.information_id).order_by(Answers.answer_score.desc(), Answers.timestamp.desc()).limit(answer_limit).all()
        return [answer.to_dict() for answer in limited_answers]

    def __repr__(self):
        return f'insight_id: {self.insight_id}, information_id: {self.information_id}, paper_id: {self.paper_id}, authors: {self.authors}'


# ---------------------------------------------------------
 
# === Answers ===
class Answers(db.Model):
    """ 

        **Explanation:**

        * information_id links the 'answer' to one 'information'
        * 'answer' is the actual answer to the 'insight'/'information' asked for in the paper, stored as a string
        * answer_up/downvotes selfexplanatory
        * answer_score makes it easier to rank the 'answers'
    """
    __tablename__ = 'answers'

    answer_id = db.Column(db.Integer, primary_key=True)
    information_id = db.Column(db.Integer, db.ForeignKey('information.information_id'), nullable=False)
    answer = db.Column(db.String(30), default = "")
    answer_upvotes = db.Column(db.Integer, default = 0)
    answer_downvotes = db.Column(db.Integer, default = 0)
    answer_score = db.Column(db.Integer, default = 0)
    timestamp = db.Column(db.DateTime, default = datetime.utcnow)

    def to_dict(self):
        """ 

            **Returns:**
            * dict: all information stored in this object
        """
        return dict(
        answer = self.answer,
        answer_upvotes = self.answer_upvotes,
        answer_downvotes = self.answer_downvotes,
        answer_score = self.answer_score
        )

    def __repr__(self):
        return f'answer: {self.answer}, answer_upvotes: {self.answer_upvotes}, answer_downvotes: {self.answer_downvotes}'
