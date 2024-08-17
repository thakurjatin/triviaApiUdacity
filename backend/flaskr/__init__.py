import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

# pagination for the questions


def paginate_allquestions(request, selection):
    page = request.args.get('page', 1, type=int)
    initial = (page - 1) * QUESTIONS_PER_PAGE
    endvalue = initial + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[initial:endvalue]
    return current_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers",
                             "Content-Type,Authorization,true"
            )
        response.headers.add(
            "Access-Control-Allow-Methods",
                             'GET,PATCH,POST,DELETE,OPTIONS'
                )
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route("/categories")
    def get_available_categories():
        allcategories = Category.query.all()
        categoriesDict = {}
        for category in allcategories:
            categoriesDict[category.id] = category.type
        return jsonify({
            'success': True,
            'categories': categoriesDict
        })

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    
    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def get_allquestions():
        try:
            selection = Question.query.order_by(Question.id).all()
            numberOfQuestions = len(selection)
            currQuestions = paginate_allquestions(request, selection)
            if (len(currQuestions) == 0):
                abort(404)
            allcategories = Category.query.all()
            categoriesDict = {}
            for category in allcategories:
                categoriesDict[category.id] = category.type

            return jsonify({
                'success': True,
                'questions': currQuestions,
                'all_questions': numberOfQuestions,
                'categories': categoriesDict
            })
        except Exception as e:
            print(e)
            abort(400)


    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:id>', methods=['DELETE'])
    def delete_initialquestion(id):
        try:
            questionValue = Question.query.filter_by(id=id).one_or_none()
            if questionValue is None:
                abort(404)
            questionValue.delete()
            selection = Question.query.order_by(Question.id).all()
            currQuestions = paginate_allquestions(request, selection)

            return jsonify({
                'success': True,
            })

        except Exception as e:
            print(e)
            abort(404)



    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route("/questions", methods=['POST'])
    def add_question():
        initialbody = request.get_json()
        currentQuestion = initialbody.get('question', None)
        currentAnswer = initialbody.get('answer', None)
        currentCategory = initialbody.get('category', None)
        currentDifficulty = initialbody.get('difficulty', None)

        try:
            questionValue = Question(question=currentQuestion, answer=currentAnswer,
                                category=currentCategory, difficulty=currentDifficulty)
            questionValue.insert()
            selection = Question.query.order_by(Question.id).all()
            currentQuestions = paginate_allquestions(request, selection)

            return jsonify({
                'success': True,
                'created': questionValue.id,
                'questions': currentQuestions,
                'all_questions': len(selection)
            })
        except Exception as e:
            print(e)
            abort(422)


    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route("/search", methods=['POST'])
    def allsearch():
        initialbody = request.get_json()
        initialsearch = initialbody.get('searchTerm')
        initialquestions = Question.query.filter(
            Question.question.ilike('%'+initialsearch+'%')).all()
        if initialquestions:
            currentQuestions = paginate_allquestions(request, initialquestions)
            return jsonify({
                'success': True,
                'questions': currentQuestions,
                'all_questions': len(initialquestions)
            })
        else:
            abort(404)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route("/categories/<int:id>/questions")
    def allquestions_in_category(id):
        initialcategory = Category.query.filter_by(id=id).one_or_none()
        if initialcategory:
            questionsInCat = Question.query.filter_by(category=str(id)).all()
            currentQuestions = paginate_allquestions(request, questionsInCat)

            return jsonify({
                'success': True,
                'questions': currentQuestions,
                'all_questions': len(questionsInCat),
                'current_category': initialcategory.type
            })
        else:
            abort(404)

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def triviaquiz():
        initialbody = request.get_json()
        initialquizCategory = initialbody.get('quiz_category')
        earlierQuestion = initialbody.get('previous_questions')
        try:
            if (initialquizCategory['id'] == 0):
                questionsQuery = Question.query.all()
            else:
                questionsQuery = Question.query.filter_by(
                    category=initialquizCategory['id']).all()

            index = random.randint(0, len(questionsQuery)-1)
            upcomingQuestion = questionsQuery[index]

            stillQuestions = True
            while upcomingQuestion.id not in earlierQuestion:
                upcomingQuestion = questionsQuery[index]
                return jsonify({
                    'success': True,
                    'question': {
                        "answer": upcomingQuestion.answer,
                        "category": upcomingQuestion.category,
                        "difficulty": upcomingQuestion.difficulty,
                        "id": upcomingQuestion.id,
                        "question": upcomingQuestion.question
                    },
                    'previousQuestion': earlierQuestion
                })
        except Exception as e:
            print(e)
            abort(404)

    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            'error': 400,
            "message": "Bad request"
        }), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return jsonify({
            "success": False,
            'error': 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable_recource(error):
        return jsonify({
            "success": False,
            'error': 422,
            "message": "Unprocessable recource"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            'error': 500,
            "message": "Internal server error"
        }), 500

    @app.errorhandler(405)
    def invalid_method(error):
        return jsonify({
            "success": False,
            'error': 405,
            "message": "Invalid method!"
        }), 405

    return app

