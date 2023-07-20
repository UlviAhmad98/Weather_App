from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
import sys, requests, datetime, os
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
app.config['SECRET_KEY'] = 'So-Seckrekt'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(85), unique=True, nullable=False)

    def __repr__(self):
        return self.name


db.create_all()


def api_access(city_name):
    api_key = os.environ.get('weather_api_key')
    request_params = {'q': city_name, 'units': 'metric', 'appid': api_key}
    response = requests.get('http://api.openweathermap.org/data/2.5/weather', params=request_params)
    return response


def time_cards(time):
    if 5 <= time < 12:
        return "evening-morning"
    elif 12 <= time < 20:
        return "day"
    else:
        return "night"


@app.route('/', methods=['GET'])
def index():
    cities = City.query.all()
    weather_dict = dict()
    for city in cities:
        city_name = city.name.upper()
        weather_data = api_access(city_name).json()
        temperature = round(weather_data['main']['temp'])
        time = (datetime.datetime.utcnow() + datetime.timedelta(seconds=weather_data['timezone'])).hour
        day_time = time_cards(time)
        weather_state = weather_data['weather'][0]['main']
        weather_dict.update({city.id: {'city': city.name.capitalize(),
                                       'temperature': temperature,
                                       'weather_state': weather_state,
                                       'day_time': day_time}})
    return render_template('index.html', weather=weather_dict)


@app.route('/add', methods=['POST'])
def add_city():
    if request.method == 'POST':
        city_name = request.form['city_name']
        if api_access(city_name).status_code != 200:
            flash("The city doesn't exist!", category='error')
            return redirect(url_for('index'))
        elif City.query.filter_by(name=city_name).first() is not None:
            flash("The city has already been added to the list!", category='info')
            return redirect(url_for('index'))
        city = City(name=city_name)
        db.session.add(city)
        db.session.commit()
        return redirect(url_for('index'))


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    if request.method == 'POST':
        city_del = City.query.filter_by(id=city_id).first()
        db.session.delete(city_del)
        db.session.commit()
        return redirect('/')


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
