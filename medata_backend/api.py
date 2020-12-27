from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import or_, exists, and_, not_
from datetime import datetime
from models import db, Insights, Information, Answers, Categories
import pandas as pd


api = Blueprint('api', __name__)




@api.route('/ping', methods=['GET'])
def ping_pong():
    """Check if Server is running

    Returns:
        [json]: [just return a string "pong" in json format]
    """
    return jsonify('pong!')

@api.route('/get_all', methods=['GET'])
def get_all():
    """Testing Method to return whole database

    Returns:
        [json]: [complete database sorted by insights]
    """
    response_object = {'status':     'success'}
    print(Insights.query.count())
    for x in range(0,Insights.query.count()):
        response_object[f'insight {x}'] = Insights.query.get(x).to_dict()
    
    return jsonify(response_object)


@api.route('/get_specific', methods=['POST'])
def get_specific():
    """Get all Insights for a specific paperid

    Returns:
        [json]: [if no insights yet an empty string is returned, otherwise a json object with all relevant Insights is returned]
    """
    response_object_length = 7
    response_object = []
    #fetch data from request
    url = request.get_json().get('url')
    print(url)
    #relevant_categories_scraper = acm_scraper.get_leaf_categories(url)
    #print(relevant_categories_scraper)

    #hardcoded for now 
    relevant_categories = ['laboratory experiments', 'supervised learning by classification', 'category3']
    paper_id = "50"
    #for testing conditionals
    #relevant_categories = ['cats']
    #paper_id = "545654645"

    
    #insights filtered by category
    matching_insight = Insights.query.join(Insights.categories).filter(or_(Categories.name==x for x in relevant_categories)).all()

    #if (information for paper_id does not exist) create information with paper_id
    for x in matching_insight:
        if (Information.query.filter(Information.insight_id==int(x.id)).filter(Information.paper_id==paper_id).count()==0):
            i = Information(insight_id = x.id, insight_name=x.name, paper_id=paper_id)
            db.session.add(i)
    db.session.commit()

    #filtered information, ordered by answer_score 
    filtered_information_answers = Information.query.join(Information.answers).filter(or_(Information.insight_id==int(x.id) for x in matching_insight)).filter(Information.paper_id==paper_id).order_by(Answers.answer_score.desc()).all()
    response_object_length = response_object_length - len(filtered_information_answers)
    filtered_information_without_answers = Information.query.filter(or_(Information.insight_id==int(x.id) for x in matching_insight)).filter(Information.paper_id==paper_id).order_by(Information.insight_upvotes-Information.insight_downvotes).limit(response_object_length).all()
    for x in filtered_information_answers:
        response_object.append(x.to_dict())

    for x in filtered_information_without_answers:
        if (x.answers == []):
            response_object.append(x.to_dict())

    if (Information.query.filter(or_(Information.insight_id==int(x.id) for x in matching_insight)).filter(Information.paper_id==paper_id).count()==0):
        #response_object = []
        #response_object.append(relevant_categories)
        return jsonify([])
    else:
        #response_object.append(relevant_categories)
        return jsonify(response_object)


@api.route('/add_insight', methods =["POST"])
def add_insight():
    """Add an insight to a specific category

    Args:
        json: 
            { 
            "insight" : String with the name of the Insight
            "categories" : List of Strings with category names
            "paper_id" : String with the paper_id which is in our case the completet link to the paper
            }


    Returns:       
        json: {"status": "success"}
    """     
    response_object = {'status': 'success'}
    #fetch data from request
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
        #creats empty information
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

#adds new answer        
@api.route('/add_answer', methods = ["POST"])
def add_answer():
    """Add a new answer to an existing Information  

    Args:
        json: 
            { 
            "paper_id" : String with the paper_id which is in our case the completet link to the paper
            "insight" : String with the name of the Insight
            "answer" : String with the Answer
            }


    Returns:       
        json: {"status": "success"}
    """
    response_object = {'status': 'success'}
    #fetch data from request
    post_data = request.get_json()
    in_paper_id = post_data.get('paper_id')
    in_insight_name = post_data.get('insight')
    in_answer = post_data.get('answer')

    try:
        in_answer.strip()
    except Exception as e:
        print(f"{e} - given answer is not a String object!")


    #get information 
    inf = Information.query.filter(Information.paper_id==in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()
    #get answers 
    ans = Answers.query.filter(Answers.information_id==inf.information_id).all()
  
    answer_already_exists = False

    for a in ans:
        if (a.answer==in_answer):
            answer_already_exists = True

    if (answer_already_exists==False):
        #default 1 upvote
        new_answer = Answers(information_id=inf.information_id, answer = in_answer, answer_upvotes = 1, answer_score = 1)
        db.session.add(new_answer)
        db.session.commit()

    return jsonify(response_object)


@api.route('/rate_answer', methods = ["POST"])
def rate_answer():
    """Rate an already given answer

      Args:
        json: 
            { 
            "insight" : String with the name of the Insight
            "paper_id" : String with the paper_id which is in our case the completet link to the paper
            "upvote" : Boolean if the answer was upvoted(= true) or downvoted (= false)
            "answer" : String with the Answer
            }


    Returns:
        json: {"status": "success"}
    """
    response_object = {'status': 'success'}
    #fetch data from request
    post_data = request.get_json()
    in_insight_name = post_data.get('insight')
    in_paper_id = post_data.get('paper_id')
    in_upvote = post_data.get('upvote')
    in_answer = post_data.get('answer')

    #get information 
    inf = Information.query.filter(Information.paper_id == in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()
    #get answers
    ans = Answers.query.filter(Answers.information_id==inf.information_id).all()

    #upvote answer
    if (in_upvote):
        for a in ans:
            if (a.answer==in_answer):
                a.answer_upvotes = a.answer_upvotes + 1
                a.answer_score = a.answer_score + 1

    #downvote answer
    else :
        for a in ans:
            if (a.answer==in_answer):
                a.answer_downvotes = a.answer_downvotes + 1
                a.answer_score = a.answer_score - 1

    db.session.commit()
    return jsonify(response_object)

#rates ralevance of specific insight
@api.route('/rate_relevance_insight', methods = ["POST"])
def rate_relevance_insight():
    """Rate the relevance of an already given Insight for a specific paper

      Args:
        json: 
            { 
            "insight" : String with the name of the Insight
            "paper_id" : String with the paper_id which is in our case the completet link to the paper
            "upvote" : Boolean if the insight was upvoted(= true) or downvoted (= false)
            }


    Returns:
        json: {"status": "success"}
    """
    response_object = {'status': 'success'}
    #fetch data from request
    post_data = request.get_json()
    in_insight_name = post_data.get('insight')
    in_paper_id = post_data.get('paper_id')
    in_upvote = post_data.get('upvote')

    #get information 
    inf = Information.query.filter(Information.paper_id == in_paper_id).filter(Information.insight_name==str(in_insight_name)).first()

    #upvote insight
    if (in_upvote):
        inf.insight_upvotes = inf.insight_upvotes + 1
    #downvote insight
    else :
        inf.insight_downvotes = inf.insight_downvotes + 1

    db.session.commit()
    return jsonify(response_object)



@api.route('/download', methods = ["GET"])
def download():
    #url = request.get_json().get('url')
    url = "50"
    inf = Information.query.join(Information.answers).filter(Information.paper_id==url).filter(Answers.answer_score > 1).order_by(Answers.answer_score.desc()).all()
    #catch aioor
    data = [f"Title: {inf[0].title}", f"Author(s): {inf[0].authors}", f"Link to Profile: {inf[0].authors_profile_link}"]
    data = [["Title: ", inf[0].title], ["Author(s): ", inf[0].authors], ["Link to Profile: ", inf[0].authors_profile_link]]

    for i in inf:
        data.append(["", ""])
        data.append(["Insight: ", i.insight_name])
        for a in i.answers:
            data.append(["Answer: ", a.answer])
            data.append(["Score: ", a.answer_upvotes])

    df = pd.DataFrame(data, columns = ["", "data"])
    print(df)
    df.to_csv(r"medata_backend\exports\export_data.csv")
    return send_file("exports/export_data.csv")