import datetime as dt
from flask import Flask
import boto3
import numpy as np
from collections import OrderedDict
import os
from random import randint
from flask import Flask, flash, redirect
import base64
from flask_mysqldb import MySQL



chartavg=[]
chartavg1=[]
chartavg2=[]
chartavg3=[]
chartavg4=[]
averages = {}

maxrate = [70]
minrate = [10]
flag =[0]

UPLOAD_FOLDER = 'static/uploads/'
app = Flask(__name__)
mysql = MySQL(app)


app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'flask'

app.config['MYSQL_HOST'] = 'database-1.cv6jb2nf90le.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_PASSWORD'] = 'adminflask'
app.config['MYSQL_DB'] = 'flask'


def avg2(statistic):
    with app.app_context():
        count = 0 
        cursor = mysql.connection.cursor()
        cursor.execute(f'SELECT {statistic} FROM statistic ORDER BY ID DESC LIMIT 12')
        data = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()
        for i in range(len(data)):
            count += data[i][0]
        avgx = float(('{:.0f}'.format(count/12)) )
        return avgx