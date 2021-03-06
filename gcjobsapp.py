from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from datetime import datetime
import os


app = Flask(__name__)

# Inject the current year into Base.html in the footer
@app.context_processor
def inject_year():
    return dict(year=datetime.now().year)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Text)
    title = db.Column(db.Text)
    closing = db.Column(db.Text)
    department = db.Column(db.Text)
    location = db.Column(db.Text)
    internal = db.Column(db.Integer)
    contents = db.Column(db.Text)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        jobs=Job.query.all()
    else:
        form = request.form.get('search')
        a = form.split(',')
        s = ' & '.join(f'Job.contents.ilike(f"%{x.strip()}%")' for x in a)
        jobs = Job.query.filter(eval(s)).all()
    return render_template('index.html',jobs=jobs)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/help')
def help():
    return render_template('help.html')

if __name__ == "__main__": 
    app.run()
