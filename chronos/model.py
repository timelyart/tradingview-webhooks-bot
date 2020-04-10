import os
import subprocess
from sqlalchemy.sql import ClauseElement
from werkzeug.security import generate_password_hash, check_password_hash
from chronos import db, manager, log
from flask_login import UserMixin


def get_or_create(model, defaults=None, **kwargs):
    instance = db.session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        params = dict((k, v) for k, v in kwargs.items() if not isinstance(v, ClauseElement))
        params.update(defaults or {})
        instance = model(**params)
        return instance


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(128))
    is_anonymous = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return '<User {}>'.format(self.username)


class Exchange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    ccxt_name = db.Column(db.String)
    class_name = db.Column(db.String)

    def __repr__(self):
        return '<Exchange {}>'.format(self.name)


class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String, nullable=True)
    api_secret_hash = db.Column(db.String(128), nullable=True)
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('api_key_exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('api_key_user', lazy=True))

    def set_api_secret(self, api_secret):
        self.api_secret_hash = generate_password_hash(api_secret)

    def check_api_secret(self, api_secret):
        return check_password_hash(self.password_hash, api_secret)

    def __repr__(self):
        return '<APIKey {}.{}>'.format(self.exchange.name, self.api_key)


class ExchangeData(db.Model):
    """
    Aggregates all data that comes from exchanges such as orders and positions
    """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.TIMESTAMP)
    request = db.Column(db.String)  # we might need to hash this since we don't want to see API key/secret information
    data = db.Column(db.UnicodeText)  # we might need LargeBinary here instead
    data_type = db.Column(db.String(20))  # open_orders, open_positions, closed_orders, closed_positions, etc
    data_type_is_open = db.Column(db.Boolean)  # open vs closed, i.e. 'open' orders/positions vs 'closed' orders/positions
    exchange_id = db.Column(db.Integer, db.ForeignKey('exchange.id'), nullable=False)
    exchange = db.relationship('Exchange', backref=db.backref('exchange_data_exchange', lazy=True))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('exchange_data_user', lazy=True))

    def __repr__(self):
        return '<Exchange %r>' % self.exchange.name


def create():
    db.create_all()


def create2():
    file = os.path.abspath(__file__)
    log.info(file)
    try:
        print("Detecting changes and saving them to a migration script... ")
        # result = subprocess.run(['dir'], shell=True)
        result = subprocess.run(['python', file, 'db', 'init'], shell=True)
        if result.returncode == 0:
            print("OK")
        else:
            print("FAILED")
        # print(result.stdout)
    except Exception as e:
        log.exception(e)


def delete():
    db.drop_all()


def manage():
    manager.run()
