#!/usr/bin/env python

import argparse
import datetime
import logging
import json

from flask import Flask, make_response, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.admin import Admin
from flask.ext.admin.contrib.sqla import ModelView
from werkzeug.debug import DebuggedApplication

import app_config
from render_utils import make_context, smarty_filter, urlencode_filter
import static

app = Flask(__name__)
app.debug = app_config.DEBUG

file_handler = logging.FileHandler('%s/public_app.log' % app_config.SERVER_LOG_PATH)
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

app.register_blueprint(static.static, url_prefix='/%s' % app_config.PROJECT_SLUG)

app.add_template_filter(smarty_filter, name='smarty')
app.add_template_filter(urlencode_filter, name='urlencode')

app.config['SECRET_KEY'] = '530980429'

secrets = app_config.get_secrets()

def build_connection_string():
    """
    Build a string to pass to the Flask app for connecting to DB
    """
    DATABASE = {
        'name': app_config.PROJECT_SLUG,
        'user': secrets.get('POSTGRES_USER') or app_config.PROJECT_SLUG,
        'password': secrets.get('POSTGRES_PASSWORD') or None,
        'host': secrets.get('POSTGRES_HOST') or 'localhost',
        'port': secrets.get('POSTGRES_PORT') or 5432
    }

    s = 'postgresql://'
    if DATABASE['user']:
        s += DATABASE['user']
    if DATABASE['password']:
        s += ':%s' % DATABASE['password']
    s += '@%(host)s:%(port)i/%(name)s' % DATABASE

    return s

app.config['SQLALCHEMY_DATABASE_URI'] = build_connection_string()

db = SQLAlchemy(app)

class Query(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    clan_yaml = db.Column(db.String)

    def __unicode__(self):
       return self.name

project_query_table = db.Table('project_query', db.Model.metadata,
    db.Column('query_id', db.Integer, db.ForeignKey('query.id')),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'))
)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ga_property_id = db.Column(db.String)
    domain = db.Column(db.String)
    url_prefix = db.Column(db.String)
    launch_date = db.Column(db.String)
    queries = db.relationship(Query, secondary=project_query_table)

    def __unicode__(self):
        return u'%s Carebot Project' % self.name

class ProjectAdmin(ModelView):
    column_filters = ['ga_property_id', 'domain']

    column_sortable_list = ('name', 'ga_property_id', 'domain', 'url_prefix', 'launch_date')

    form_args = dict(
        ga_property_id = dict(default = '53470309'),
        domain = dict(default = 'apps.npr.org')
    )

class QueryAdmin(ModelView):
    column_list = ['name']

admin = Admin(app, name='Carebot')
admin.add_view(ProjectAdmin(Project, db.session))
admin.add_view(QueryAdmin(Query, db.session))

# Enable Werkzeug debug pages
if app_config.DEBUG:
    wsgi_app = DebuggedApplication(app, evalex=False)
else:
    wsgi_app = app

# Catch attempts to run the app directly
if __name__ == '__main__':
    print 'This command has been removed! Please run "fab public_app" instead!'
