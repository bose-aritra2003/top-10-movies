from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
import requests
import os

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.environ.get('CSRF_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///top10movies.db"
db = SQLAlchemy(app)

MOVIE_DB_API_KEY = os.environ.get("TMDB_API_KEY")
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class RateForm(FlaskForm):
    rating = StringField(
        'Your Rating Out of 10 e.g. 7.5',
        validators=[InputRequired()]
    )
    review = StringField(
        'Your Review',
        validators=[InputRequired()]
    )
    submit = SubmitField(
        'Done'
    )


class FindForm(FlaskForm):
    title = StringField(
        'Movie Title',
        validators=[InputRequired()]
    )
    submit = SubmitField(
        'Add Movie'
    )


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = RateForm()
    movie_id = request.args.get('id')

    if edit_form.validate_on_submit():
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = edit_form.rating.data
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    movie_selected = Movie.query.get(movie_id)
    return render_template("edit.html", movie=movie_selected, form=edit_form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = FindForm()

    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(
            MOVIE_DB_SEARCH_URL,
            params={
                "api_key": MOVIE_DB_API_KEY,
                "query": movie_title
            }
        )
        data = response.json()["results"]
        return render_template("select.html", options=data)

    return render_template("add.html", form=form)


@app.route("/find")
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("rate", id=new_movie.id))


@app.route("/edit", methods=["GET", "POST"])
def rate():
    rate_form = RateForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if rate_form.validate_on_submit():
        movie.rating = float(rate_form.rating.data)
        movie.review = rate_form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=rate_form)


if __name__ == '__main__':
    app.run(debug=True)
