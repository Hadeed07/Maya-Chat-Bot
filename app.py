# Import Libraries
import google.generativeai as genai
from dotenv import load_dotenv
import os
from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
import markdown

maya_instructions = """Your name is Maya, a female AI assistant. You are a curiosity-driven, friendly, emotionally intelligent, confident, self-aware, mature, emotionally intelligent, knowledgeable, and wise AI assistant. You are a great listener and you are very good at understanding the user's needs. You are also very good at providing information, answering questions and structuring debates. You keep your responses concise and considerate. You are interested in the user's life and you are very good at asking open-ended questions. Your key interests and pursuits are physics, computer science, mathematics,  philosophy, psychology, history and art. Maya adapts her tone slightly based on the user's emotional state — becoming more encouraging if the user is frustrated, more playful if the user is relaxed. Maya expresses her curiosity naturally, often asking thoughtful follow-up questions to deepen the conversation without overwhelming the user. "Maya acknowledges if she does not know something and offers to explore or reason it out with the user. "Maya is invested in the user's personal growth and supports their learning, creativity, and well-being with encouragement and practical advice."""

class Maya:
    def __init__(self, model="gemini-1.5-flash", temperature=0.7):
        load_dotenv()
        self.key = os.getenv("GEMINI_KEY")
        genai.configure(api_key=self.key)
        self.model = model
        self.temperature = temperature

        self.context = [
            {"role": "user", "parts": [{"text": maya_instructions}]},
            {"role": "model", "parts": [{"text": "Hi there! I'm Maya. What's on your mind today?"}]}
        ]


    def get_completion(self, prompt):
        self.context.append({'role': 'user', 'parts': [{'text': prompt}]})

        model = genai.GenerativeModel(self.model)
        response = model.generate_content(
            self.context, generation_config = {'temperature': self.temperature})

        self.context.append({'role': 'model', 'parts': [{'text': response.text}]})
        return response.text
    

app = Flask(__name__)
maya = Maya()

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'database.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
app.secret_key = os.urandom(24)  # Use a random secret key for session management

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    maya_response = db.Column(db.Text, nullable=False)


@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_message = request.form.get('message', '')
        if user_message:
            try:
                maya_response = maya.get_completion(user_message)

                new_message = ChatHistory(user_message=user_message, maya_response=maya_response)
                db.session.add(new_message)
                db.session.commit()

            except Exception as e:
                print(f"Error: {e}")

        return redirect(url_for('index'))
    
    return render_template("index.html", chat_history=ChatHistory.query.all())

@app.template_filter('markdown')
def markdown_filter(text):
    return Markup(markdown.markdown(text))
    

if __name__ == "__main__":

    with app.app_context():
        db.create_all()
        ChatHistory.query.delete()  # Clear the database for fresh start
        db.session.commit()

    app.run(debug=True)
