import logging
import os
import secrets
import subprocess
from pathlib import Path
from urllib.parse import unquote

import boto3
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
from flask import Flask, render_template, request, flash, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from google.generativeai import GenerationConfig

# Constants
DEFAULT_FLASK_SECRET_KEY = "super_secret_key"
DEFAULT_VOICE_ID = "Kendra"
AWS_REGION = "us-east-2"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from a .env file
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# Initialize Flask
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", secrets.token_urlsafe(16))

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///interview_buddy.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Define database models
class InterviewQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_role = db.Column(db.String(100), nullable=False)
    question = db.Column(db.String(500), nullable=False)


class InterviewAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('interview_question.id'), nullable=False)
    answer = db.Column(db.String(2000), nullable=False)
    score = db.Column(db.Integer, nullable=False)


class InterviewTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_role = db.Column(db.String(100), nullable=False)
    tip = db.Column(db.String(500), nullable=False)


# Create tables if they don't exist
with app.app_context():
    db.create_all()

# Configure Gemini API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Create the model
generation_config = GenerationConfig(
    temperature=0.7,
    top_p=0.95,
    top_k=64,
    max_output_tokens=8192,
    response_mime_type="text/plain",
)

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)

# Initialize Amazon Polly
polly_client = boto3.client('polly',
                            region_name=AWS_REGION,
                            aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                            aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        return handle_post_request()
    return render_template('index.html')


def handle_post_request():
    candidate_name = request.form.get('candidate_name', '').strip()
    job_role = request.form.get('job_role', '').strip()
    company_name = request.form.get('company_name', '').strip()

    if not job_role:
        flash("Job role is required.", "error")
        return render_template('index.html')

    question = generate_interview_question(candidate_name, job_role, company_name)
    audio_filename = text_to_speech(question)
    if audio_filename:
        logger.info(f"Redirecting to interview with audio file: {audio_filename}")
        return redirect(
            url_for('interview', candidate_name=candidate_name, job_role=job_role, company_name=company_name,
                    question=question, audio_filename=audio_filename))
    else:
        flash("Error generating audio file.", "error")
        return render_template('index.html')


def convert_audio(input_file, output_format="wav"):
    if not os.path.exists(input_file):
        logger.error(f"Input file does not exist: {input_file}")
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    output_filename = os.path.splitext(input_file)[0] + f".{output_format}"
    command = [
        'ffmpeg',
        '-i', input_file,
        '-y',  # Overwrite existing output file
        output_filename,
    ]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"ffmpeg command failed: {e}")
        raise
    return output_filename


@app.route('/interview/<candidate_name>/<job_role>/<company_name>/<question>/<audio_filename>', methods=['GET', 'POST'])
def interview(candidate_name, job_role, company_name, question, audio_filename):
    question = unquote(question)  # Decode the URL-encoded question
    if request.method == 'POST':
        return handle_audio_upload(request, question)
    return render_template('interview.html', candidate_name=candidate_name, job_role=job_role,
                           company_name=company_name, question=question, audio_filename=audio_filename)


def handle_audio_upload(request, question):
    if 'audio_file' in request.files:
        audio_file = request.files['audio_file']
        save_dir = 'output_audio'
        os.makedirs(save_dir, exist_ok=True)
        audio_path = os.path.join(save_dir, audio_file.filename)
        audio_file.save(audio_path)
        try:
            wav_audio_path = convert_audio(audio_path)
            user_answer = convert_audio_to_text(wav_audio_path)
            score, filler_word_counts, review, perfect_answer = evaluate_answer(question, user_answer)
            save_interview_answer(question, user_answer, score)
            return {"transcription": user_answer, "score": score, "filler_word_counts": filler_word_counts,
                    "review": review, "perfect_answer": perfect_answer}
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            return {"error": "Error processing audio file"}, 500
    else:
        return {"error": "No audio file provided"}, 400


def save_interview_answer(question, user_answer, score):
    question_id = InterviewQuestion.query.filter_by(question=question).first().id
    db.session.add(InterviewAnswer(question_id=question_id, answer=user_answer, score=score))
    db.session.commit()


def generate_interview_question(candidate_name, job_role, company_name):
    prompt = (
        f"Generate a clear and concise interview question for {candidate_name} applying for a {job_role} position at {company_name}. "
        "The question should be relevant to the job role and assess the candidate's skills and experience. "
        "Avoid using special characters, hashtags, or markdown syntax. "
        "The text should flow naturally as if it's meant to be spoken."
    )
    response = model.generate_content(prompt)
    question = response.text.strip()
    db.session.add(InterviewQuestion(job_role=job_role, question=question))
    db.session.commit()
    return question


def evaluate_answer(question, user_answer):
    filler_words = ['uh', 'oh', 'um', 'like', 'you know', 'so', 'actually', 'basically', 'literally', 'I mean', 'well',
                    'sort of', 'kind of']
    filler_word_counts = {word: user_answer.lower().split().count(word) for word in filler_words}

    prompt = (
        f"Evaluate the following answer to the question '{question}': {user_answer}. "
        "Provide a score between 0 and 10 based on the following factors: "
        "Communication, Personality, Professionalism, Culture fit, Dependability, "
        "Past experience, and Problem solving. "
        "Also, consider the use of filler words like 'uh', 'oh', 'um', 'like', 'you know', 'so', 'actually', "
        "'basically', 'literally', 'I mean', 'well', 'sort of', and 'kind of' which are not great for interviews. "
        "Explain the reasoning behind the score. "
        "Additionally, provide a detailed review of the answer and advice for improvement. "
        "Finally, generate the perfect answer to the question."
    )
    response = model.generate_content(prompt)
    response_text = response.text.strip().split('\n')

    try:
        score = int(response_text[0].split()[0])  # Extract the score from the response
    except ValueError:
        score = 0  # Default to 0 if the response is not a valid integer

    review = "\n".join(response_text[1:-1])  # Extract the review and advice from the response
    perfect_answer = response_text[-1]  # Extract the perfect answer

    logger.info(f"Score for question '{question}': {score}")
    logger.info(f"Filler word counts for question '{question}': {filler_word_counts}")
    logger.info(f"Review for question '{question}': {review}")
    logger.info(f"Perfect answer for question '{question}': {perfect_answer}")

    return score, filler_word_counts, review, perfect_answer


def convert_audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Could not understand the audio"
    except sr.RequestError as e:
        return f"Could not request results; {e}"


def text_to_speech(text):
    try:
        response = polly_client.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId=DEFAULT_VOICE_ID
        )
        audio_stream = response['AudioStream']
        save_dir = 'output_audio'
        os.makedirs(save_dir, exist_ok=True)
        audio_filename = f"{secrets.token_urlsafe(8)}.mp3"
        audio_path = os.path.join(save_dir, audio_filename)
        with open(audio_path, 'wb') as file:
            file.write(audio_stream.read())
        logger.info(f"Audio file generated: {audio_filename}")
        return audio_filename
    except Exception as e:
        logger.error(f"Error synthesizing speech: {e}")
        return None


@app.route('/audio/<filename>')
def get_audio(filename):
    file_path = Path('output_audio', filename)  # Correct path to 'output_audio'
    if file_path.exists():
        logger.info(f"Serving audio file: {filename}")
        return send_from_directory(directory='output_audio', path=filename,
                                   mimetype='audio/mpeg')  # Change to 'audio/mpeg'
    else:
        logger.error(f"Audio file not found: {filename}")
        flash("Error loading audio file.", "error")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
