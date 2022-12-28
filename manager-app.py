from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import boto3
import numpy as np
from app import *
from collections import OrderedDict
import os
from random import randint
from flask import Flask, flash, redirect
import base64
from flask_mysqldb import MySQL
from sched import scheduler
from apscheduler.schedulers.background import BackgroundScheduler
import json

import datetime

scheduler = BackgroundScheduler()
scheduler.start()
instance = ''
hit , miss , req , numOfItems , sizeCache , time = {} , {} , {} , {} , {} , {}



ec2 = boto3.client("ec2")
def get_running_instances():
    
    ec2_client = boto3.client("ec2")
    reservations = ec2_client.describe_instances(Filters=[
        {
            "Name": "instance-state-name",
            "Values": ["pending", "running",],
        }
    ]).get("Reservations")
    array = []
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            
            array.append(instance_id)
    for i in array:
        if i == 'i-0f37879110feedbdf' : # ec2 linux 
            array.pop(array.index(i))
            array.append('i-0f37879110feedbdf') # ec2 linux
    for i in array:
        if i == 'i-0239fc44187d18614': # ec2 app manager
            array.pop(array.index(i))

    return array

def get_number_of_running_instances():
    ec2_client = boto3.client("ec2")
    reservations = ec2_client.describe_instances(Filters=[
        {
            "Name": "instance-state-name",
            "Values": ["pending" , "running",],
        }
    ]).get("Reservations")
    array = []
    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            array.append(instance_id)
    for i in array:
        if i == 'i-0239fc44187d18614': # ec2 app manager
            array.pop(array.index(i))
    
    return len(array)
@app.route('/' )
def home():
    
    # statistics()
    count = get_number_of_running_instances()
    m1 = maxrate[-1]
    m2 = minrate[-1]
    print(get_running_instances())
    print (count)
    print(maxrate[-1])
    print(minrate[-1])
    # return render_template('manager-app.html' , count = count)
    return render_template('manager-app.html', maxRate = m1 , minRate = m2 ,count = count ,
                                chartavg = json.dumps(chartavg) , 
                                chartavg1 = json.dumps(chartavg1) ,
                                chartavg2 = json.dumps(chartavg2) ,
                                chartavg3 = json.dumps(chartavg3) ,
                                chartavg4 = json.dumps(chartavg4) 
                             
                        )
@app.route('/' , methods=['POST' ,'GET'])
def memcache_pool_Manual():
    count = get_number_of_running_instances()
    m1 = maxrate[-1]
    m2 = minrate[-1]
    
    try:
        if request.method == 'POST':
            policty =  request.form['pool_resizing']
            if policty == "Manual":   
                flag.append(0) # flag = 0 for manual
                if request.form["policty"] == 'Grow': # grow the
                    
                    global  instance
                    if count >= 8 : # max number of instances
                        flash("You can't grow more than 8 instances")
                        # return redirect(url_for('home') , count = count , maxRate = m1 , minRate = m2)
                        return render_template('manager-app.html', maxRate = m1 , minRate = m2 , count = count)
                    else:
                        instance = ec2.run_instances(
                        ImageId="ami-00059cd1761a3914f",
                        MinCount=1,
                        MaxCount=1,
                        InstanceType="t2.micro",
                        KeyName="test"
                    )
                        count = get_number_of_running_instances()
                        print(get_running_instances())
                        print (count)
                
                if request.form["policty"] == 'Shrink': # shrink the pool
                    instance_id = get_running_instances()  
                    
                    if instance_id[0] != "i-0f37879110feedbdf" : # ec2 linux
                        ec2.stop_instances(InstanceIds=[instance_id[0]])
                    else:
                        flash("You can't shrink the pool to less than 1 instance")

            elif policty == "Auto": 
                flag.append(1)
                maxRate =  request.form["max"]
                minRate =  request.form["min"]
                maxrate.append(int(maxRate))
                minrate.append(int(minRate))

                return render_template('manager-app.html', maxRate = maxRate , minRate = minRate , count = count)
    except:
        
        flash("Error")
        return redirect(url_for('home') )
    
    return redirect(url_for('home'))

@app.route('/config' , methods=['POST' ,'GET'])
def config():

    if request.method == 'POST':
        capacity = request.form['capacity']
        try:
            if request.form['replacement'] == 'LRU':
                curser = mysql.connection.cursor()
                curser.execute('INSERT INTO config (capacity, policty) VALUES (%s , %s)' , [capacity,2])
                mysql.connection.commit()
                curser.close()
                flash("LRU")
                return redirect(url_for('home'))
            elif request.form['replacement'] == 'RR':
                curser = mysql.connection.cursor()
                curser.execute('INSERT INTO config (capacity, policty) VALUES (%s , %s)' , [capacity,1])
                mysql.connection.commit()
                curser.close()
                flash("RR")
                return redirect(url_for('home'))
        except:
            flash("Error")
            return redirect(url_for('home'))
    return redirect(url_for('home'))


@app.route('/clear' , methods=['POST'])
def clear():
    if request.method == 'POST':
        if request.form['removedata'] == 'clr':
            print('clear')
            instance_id = get_running_instances()
            for i in instance_id:
                if i == 'i-0f37879110feedbdf' : # ec2 linux
                    pass
                else:
                    ec2.terminate_instances(InstanceIds=[i])
            print(get_running_instances())
            print(get_number_of_running_instances())
            
        elif request.form['removedata'] == 'del':
            print('delete')
            curser = mysql.connection.cursor()
        try:
            delete_all_objects_from_s3_folder()
            #for delete img in folder
            curser.execute("DELETE FROM todo")
            mysql.connection.commit()
            curser.close()
            flash( 'Image successfully deleted')
            return redirect(url_for('home'))
        except:
            flash('Image not found')
            return redirect(url_for('home'))
            

    return redirect(url_for('home'))

def delete_all_objects_from_s3_folder():

    bucket_name = "mnews3"

    s3_client = boto3.client("s3")

    # First we list all files in folder
    response = s3_client.list_objects_v2(Bucket=bucket_name,)

    files_in_folder = response["Contents"]
    files_to_delete = []
    # We will create Key array to pass to delete_objects function
    for f in files_in_folder:
        files_to_delete.append({"Key": f["Key"]})

    # This will delete all files in a folder
    response = s3_client.delete_objects(
        Bucket=bucket_name, Delete={"Objects": files_to_delete}
    )
    print(response)


def statistics():
    with app.app_context():
        count = get_number_of_running_instances()
        cloudwatch = boto3.client('cloudwatch')

    # Set the namespace for the metrics
    namespace = 'MyNamespace'

    # Set the names of the metrics
    metric_names = ['missMetric', 'hitMetric', 'reqMetric', 'itemsMetric' , 'sizeMetric']

    # Set the start and end time for the data points
    start_time = datetime.datetime.utcnow() - datetime.timedelta(seconds=60)
    end_time = datetime.datetime.utcnow()

    # Set the time period for the data points (in seconds)
    period = 60
    

    # Loop through the metric names
    for metric_name in metric_names:
        # Get the statistical data for the metric
        statistics = cloudwatch.get_metric_statistics(
            Namespace=namespace,
            MetricName=metric_name,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=['Average']
        )

        # Get the average value from the statistical data
        average = statistics['Datapoints'][0]['Average']
        # Add the average value to the dictionary
        averages[metric_name] = average
 
    if len(chartavg) == 30:
        chartavg.clear()
        chartavg1.clear()
        chartavg2.clear()
        chartavg3.clear()
        chartavg4.clear()
    chartavg.append(averages['missMetric'])
    chartavg1.append(averages['hitMetric'])
    chartavg2.append(averages['reqMetric'])
    chartavg3.append(averages['itemsMetric'])
    chartavg4.append(averages['sizeMetric'])

    if flag[-1] ==1:
        if  maxrate[-1] <= averages['missMetric'] : #chartavg[-1]
            print('grow')  
        
        global  instance
        if  maxrate[-1] <= averages['missMetric'] :  #chartavg[-1]
            if count < 8 :
                # instance = ec2.run_instances(
                #     ImageId="ami-00059cd1761a3914f",
                #     MinCount=1,
                #     MaxCount=1,
                #     InstanceType="t2.micro",
                #     KeyName="test"
                # )
                print("grow")
        else:
            if count > 1:
                instance_id = get_running_instances()
                if instance_id[0] != "i-0f37879110feedbdf" : # ec2 linux
                    # ec2.stop_instances(InstanceIds=[instance_id[0]])
                    print("shrink")
            else:
                print("no shrink")
    else:
        print(averages['missMetric'])
        print(avg2('miss_rate'))
        print('manual')

def avg():
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM statistic ORDER BY id DESC LIMIT 1')
        data = cursor.fetchall()
        mysql.connection.commit()
        cursor.close()

        for i in range(len(data)):
            miss[i] = data[i][1]
            hit[i] = data[i][2]
            req[i] = data[i][3]
            numOfItems[i] = data[i][5]
            sizeCache[i] = data[i][6]
        print('statistics')
        print(req[0])
        print('/*******************************/')
        cloudwatch = boto3.client('cloudwatch')

        namespace = 'MyNamespace'
        # metric_name = 'MyMetric'
        value = miss[0]
        value2 = hit[0]
        value3 = req[0]
        value4 = numOfItems[0]
        value5 = sizeCache[0]

        metric_data = [
                        {
                            'MetricName': 'missMetric',
                            'Value': value
                        },
                        {
                            'MetricName': 'hitMetric',
                            'Value': value2
                        },
                        {
                            'MetricName': 'reqMetric',
                            'Value':  value3
                        },
                        {
                            'MetricName': 'itemsMetric',
                            'Value': value4
                        },
                        {
                            'MetricName': 'sizeMetric',
                            'Value': value5
                        }
                    ]   
        cloudwatch.put_metric_data(

            Namespace=namespace,
            MetricData=metric_data

        )
   

scheduler.add_job(func=avg, trigger="interval", seconds= 5) # seconds
scheduler.add_job(func=statistics, trigger="interval", seconds= 61) # minutes

if __name__ ==  "__main__":
    app.run(debug = False ,
            host = "0.0.0.0" ,
            port = 5000
            ) 



          
