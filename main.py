#!/usr/bin/python

import os
from flask import Flask, render_template_string, render_template, request, flash
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exists
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter, current_user
from wtforms import Form, BooleanField, TextField, PasswordField, validators, TextAreaField

class WriteForm(Form):
    text = TextAreaField('Story', [validators.Length(min=100,max=10000)] )
    title = TextField('Title', [validators.Length(min=1,max=500)]  )

class EveningForm(Form):
    name = TextField('Name', [validators.Length(min=1,max=255)])
    description = TextAreaField('Description', [validators.Length(min=20,max=1000)] )

# Use a Class-based config to avoid needing a 2nd file
# os.getenv() enables configuration through OS environment variables
class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       '\xf1\xa7n-\x7fc4\xce8\xe0\x04\x87\xa0b:<\xcdee\xa6&\x92\x1e\x00')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'noreply@thousandonestories.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        'Og\~YJ48r2z!dROg\~Y')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"Account registration" <noreply@thousandonestories.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'baltar.asoshared.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '465'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         True))

    # Flask-User settings
    USER_APP_NAME        = "A Thousand and One Stories"                # Used by email templates


def create_app():
    """ Flask application factory """
    
    # Setup Flask app and app.config
    app = Flask(__name__)
    app.config.from_object(__name__+'.ConfigClass')

    # Initialize Flask extensions
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
    mail = Mail(app)                                # Initialize Flask-Mail

    # Define the User data model. Make sure to add flask.ext.user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__='user'
        id = db.Column(db.Integer, primary_key=True)

        # User authentication information
        username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

        # User email information
        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())

        # User information
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        first_name = db.Column(db.String(100), nullable=False, server_default='')
        last_name = db.Column(db.String(100), nullable=False, server_default='')

        stories = db.relationship('Story', backref='user')

        evenings= db.relationship('Evening', backref='user')

    # Define the Story data model.
    class Story(db.Model):
        __tablename__='story'

        id = db.Column(db.Integer, primary_key=True)
        text = db.Column(db.String(10000), nullable=False, unique=False)  # ! can you have a 10000 character string?
        title = db.Column(db.String(500), nullable=False, unique=False)
        
        author_id=db.Column(db.Integer, db.ForeignKey('user.id'))
        #author = db.relationship('User', backref=db.backref('story', lazy='dynamic'))
        author = db.relationship('User')

        evening_id=db.Column(db.Integer, db.ForeignKey('evening.id'))
        #evening = db.relationship('evening')

        def __init__(self, title, text, author):
            self.title=title
            self.text=text
            self.author=author


    class Evening(db.Model):
        __tablename__='evening'

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(255), nullable=False, unique=True)

        stories = db.relationship('Story', backref=db.backref('evening'))

        creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        creator = db.relationship('User')
        
        def __init__(self, name, description, creator):
            self.name = name
            self.description = description
            self.creator = creator


    # Create all database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
    user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

    # The Home page is accessible to anyone
    @app.route('/')
    def home_page():
        stories = Story.query.all()
        return render_template("home.html", story_list=stories)

    # The Members page is only accessible to authenticated users
    @app.route('/members')
    @login_required                                 # Use of @login_required decorator
    def members_page():
        return render_template("members.html")

    @app.route('/mystories')  #TODO: goes on profile page
    @login_required
    def mystories():
        stories = current_user.stories
        return render_template("home.html", story_list=stories)

    @app.route('/write', methods =['GET', 'POST'])
    @login_required
    def write():
        writeform = WriteForm(request.form)
        if request.method == 'POST' and writeform.validate():
            story = Story(writeform.title.data, writeform.text.data, current_user)
            db.session.add(story)
            db.session.commit()
            flash('You have submitted your story. /TODO: now what?')
        return render_template("write.html", form = writeform )

    @app.route('/newevening', methods=['GET','POST'])
    @login_required
    def newevening():
        eveform = EveningForm(request.form)
        if request.method == 'POST' and eveform.validate():
            evening = Evening(eveform.name.data, eveform.description.data, current_user)
            db.session.add(evening)
            db.session.commit()
            flash("You've made an evening.") 
        return render_template("newevening.html", form=eveform)

    @app.route('/evenings', defaults={'path': ''})
    @app.route('/evenings/', defaults={'path': ''})
    @app.route('/evenings/<path:path>')
    def evening(path):
        if path == '':
            evenings = Evening.query.all()
            return render_template("evenings.html", evenings_list= evenings)
        else:

            #stories = Evening.query.filter(evening.name=path)
            match = db.session.query(Evening).filter(Evening.name == path).all()
          
            if match:
                stories = match[0].stories
            
                return render_template("eveningspage.html", story_list = stories, evening_name = path) 

            else:
                if path.endswith("/add"):
                    return render_template_string("addyaddyadd")
                else:
                    return render_template_string("no matching evening")

    return app


# Start development web server
if __name__=='__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
