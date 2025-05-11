import subprocess
import os
from flask import Flask, request, render_template, send_file, redirect, url_for
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import re

def no_show():
    pass
plt.show=no_show
app = Flask(__name__)

pattern = r'[A-Z][a-z]{2} [A-Z][a-z]{2} \d{2} \d{2}:\d{2}:\d{2} \d{4}'

csvfile = "structuredlog.csv" #output of bash.sh
script_sh = "scripts/bash.sh"
full_timestamps_sh = "scripts/full_timestamps.sh"
filter_sh = "scripts/filter.sh"
level_filter_sh="scripts/filter_level.sh"

@app.route('/')
def index():
    return render_template('upload.html') #Renders upload.html, where the user uploads a log file

@app.route('/hurray', methods=['POST']) #Handles file upload and level filtering. displays the display.html
def upload():
    global csvfile,save_path
    
    if 'log' in request.files:
        f = request.files['log']
        save_path = os.path.join('uploadedlogfiles', f.filename)
        f.save(save_path)
        try:   #file validate (apache or not)
            with open(save_path, 'r') as file1:
                lines = file1.readlines()
        except:
                return render_template('upload.html', error='The uploaded file is not an Apache log file.')
        if not lines:
               return render_template('upload.html', error='The uploaded file is not an Apache log file.')

        count = 0   #checking first three lines of apache file...generally apache has [..........] so I did validating the file using that 
        for line in lines[:3]:
            if '[' in line and ']' in line:
                if not re.search(pattern, line):
                    return render_template('upload.html', error='The uploaded file is not an Apache log file.')
                if not '[error]' in line or not '[notice]' in line:
                    count += 1
        if count < 3:
            return render_template('upload.html', error='The uploaded file is not an Apache log file.')
        
        subprocess.run(['bash', script_sh, save_path], check=True)
        subprocess.run(['bash', full_timestamps_sh, csvfile, 'full_timestamps.txt'], check=True)
        csvfile = "structuredlog.csv"
        return render_template("display.html", name=f.filename)
    elif 'level' in request.form:
        level = request.form.get('level')
        if level == 'all': #when level all is chosen the default file is structuredlog.csv
            csvfile="structuredlog.csv"
        else:
            subprocess.run(['bash', level_filter_sh,save_path, level], check=True)
            level_filtered =f"{level}_structuredlog.csv"
            if os.path.exists( level_filtered):
                csvfile =  level_filtered
        return render_template('display.html',selected_level=level)
    
    return render_template('display.html')

@app.route('/display')
def viewcsv():
    return render_template('display.html') #renders the dislay.html again 

@app.route('/latestcsv')#Lets users download the CSV file. latestcsv - server-Supplies the actual CSV file content as text.
def latestcsv():
    return send_file(csvfile, mimetype='text/csv')#returns the CSV file (like structuredlog.csv or filtered file) as a downloadable file.


def get_timestamps(): 
    timestamps = []
    if os.path.exists('full_timestamps.txt'):
        with open('full_timestamps.txt', 'r') as f:
            timestamps = [line.strip() for line in f]
            
    return timestamps

def read_filtered_data(start_line, end_line): 
    filtered_data = []
    with open(csvfile, 'r') as f:
        next(f) 
        for i, line in enumerate(f, 1): #returns both line numbers and lines....start_line and end_line are the values in linenos.txt file..
            if start_line <= end_line and i >= start_line and i <= end_line:
                filtered_data.append(line.strip().split(','))
            if start_line >= end_line and i <= start_line and i >= end_line:
                filtered_data.append(line.strip().split(','))             
    return filtered_data


###################################default plots when no timestamps or when we go direct from tabular form of csv to visualizations page###############
def lineplot(filtered_data=None): #Events logged with time (Line Plot) 
    eventcount = {}
    
    if filtered_data:
        for row in filtered_data:
            time1 = row[1].strip()
            time = time1[:24]
            
            if time in eventcount:
                eventcount[time] += 1
            else:
                eventcount[time] = 1
    else:
        with open(csvfile,'r') as file:
            next(file)
            for line in file:
                time1 = line.split(",")[1].strip()
                time = time1[:24]
                
                if time in eventcount:
                    eventcount[time] += 1
                else:
                    eventcount[time] = 1
            
    timexaxis = list(sorted(eventcount.keys()))
    numberyaxis = [eventcount[t] for t in timexaxis]  
    return timexaxis, numberyaxis     
        
def piechart(filtered_data=None): #Level State Distribution (Pie Chart)
    levelcount = {}
    
    if filtered_data:
        for row in filtered_data:
            level = row[2].strip()
            
            if level in levelcount:
                levelcount[level] += 1
            else:
                levelcount[level] = 1
    else:
        with open(csvfile,'r') as file:
            next(file)
            for line in file:
                level = line.split(',')[2].strip()
                
                if level in levelcount:
                    levelcount[level] += 1
                else:
                    levelcount[level] = 1
        
    labels = list(levelcount.keys()) 
    sizes = list(levelcount.values())
    
    return labels, sizes

def bargraph(filtered_data=None): #Event Code Distribution (Bar Plot)
    eventIdcounts = {'E1': 0, 'E2': 0, 'E3': 0, 'E4': 0, 'E5': 0, 'E6': 0}
    
    if filtered_data:
        for row in filtered_data:
            eventId = row[4].strip()
            if eventId in eventIdcounts:
                eventIdcounts[eventId] += 1
    else:
        with open(csvfile,'r') as file:
            next(file)
            for line in file:
                eventId = line.split(',')[4].strip()
                if eventId in eventIdcounts:
                    eventIdcounts[eventId] += 1
            
    return list(eventIdcounts.keys()), list(eventIdcounts.values())

@app.route('/graphs', methods=['GET','POST'])
def graphs():
    graph_url = None
    if request.method == 'POST': 
        from_time = request.form.get('fromtime')
        to_time = request.form.get('totime')
        print(f"From time: {from_time}, To time: {to_time}")
        # Save inputs to two_timestamps.txt
        with open('two_times.txt', 'w') as f:
            f.write(f"{from_time}\n{to_time}")

        # Run filter.sh to get line numbers
        try:
            subprocess.run(['bash', 'scripts/filter.sh', 'full_timestamps.txt', 'two_times.txt'], check=True)
            
            # Read line numbers from output file
            with open('line_nos.txt', 'r') as f:
                line_numbers = f.read().strip()
            # Parse line numbers
        
            middle = len(line_numbers) // 2
            start_line = int(line_numbers[:middle])
            end_line = int(line_numbers[middle:])
            
            # Read filtered data from CSV file
            filtered_data = []
            with open(csvfile, 'r') as f:
                next(f)  # Skip header
                for i, line in enumerate(f, 1):
                    if start_line <= end_line and i >= start_line and i <= end_line:
                        parts = line.strip().split(',')
                        filtered_data.append(parts)
                    if start_line >= end_line and i <= start_line and i >= end_line:
                        parts = line.strip().split(',')
                        filtered_data.append(parts)    
            
            # Generate filtered plots
            line_xaxis, line_yaxis = lineplot_filtered(filtered_data)
            pie_labels, pie_values = piechart_filtered(filtered_data)
            bar_labels, bar_values = bargraph_filtered(filtered_data)
            
            graph_url = 'filtered'
        except Exception as e:
            print(f"Error during filtering: {e}")
            #to non-filtered data
            return render_template('graphs.html', error="Filtering failed. Check timestamps format.")
    else:
        # Generate full data plots
        line_xaxis, line_yaxis = lineplot()
        pie_labels, pie_values = piechart()
        bar_labels, bar_values = bargraph()
    
    # # Now create the plots (either filtered or not)
    # plt.figure(figsize=(15, 5))

    # # 1st subplot: Line plot (Events over time)
    # plt.subplot(1, 3, 1)
    # plt.plot(line_xaxis, line_yaxis, color='b')
    # plt.title('Number of Events vs Time')
    # plt.xlabel('Time')
    # plt.ylabel('Number of Events')
    # plt.xticks(rotation=45)
    

    # # 2nd subplot: Pie chart (Level state distribution)
    # plt.subplot(1, 3, 2)
    # plt.pie(pie_values, labels=pie_labels, autopct='%1.1f%%')
    # plt.title('Level State Distribution')

    # # 3rd subplot: Bar chart (Event code distribution)
    # plt.subplot(1, 3, 3)
    # plt.bar(bar_labels, bar_values, color='green')
    # plt.title('Event Code Distribution')
    # plt.xlabel('Event Code')
    # plt.ylabel('Frequency')

    # plt.tight_layout()
    # Line plot (Events over time)
    plt.figure(figsize=(6,6))
    plt.plot(line_xaxis, line_yaxis, color='b')
    plt.title('Number of Events vs Time')
    plt.xlabel('Time')
    plt.ylabel('Number of Events')
    plt.xticks(rotation=0)
    #plt.tick_params(axis='both', labelsize=20)
    if request.method == 'POST':
        plt.savefig('static/filtered_lineplot.png')
    else:
        plt.savefig('static/lineplot.png')
    plt.close()

# Pie chart (Level state distribution)
    plt.figure(figsize=(5, 5))
    plt.pie(pie_values, labels=pie_labels,colors=['green', 'yellow'] ,autopct='%1.1f%%')
    plt.title('Level State Distribution')
    if request.method == 'POST':
        plt.savefig('static/filtered_piechart.png')
    else:
        plt.savefig('static/piechart.png')
    plt.close()

# Bar chart (Event code distribution)
    plt.figure(figsize=(6, 6))
    plt.bar(bar_labels, bar_values, color='green')
    plt.title('Event Code Distribution')
    plt.xlabel('Event Code')
    plt.ylabel('Frequency')
    if request.method == 'POST':
        plt.savefig('static/filtered_bargraph.png')
    else:
        plt.savefig('static/bargraph.png')
    plt.close()

    # if request.method == 'POST':
    #     # For filtered data
    #     plt.savefig('static/filtered_graphs.png')
    #     graph_url = 'static/filtered_graphs.png'
    #     plt.close()
    #     plt.savefig('static/filtered_graphs.png')
    #     graph_url = 'static/filtered_graphs.png'
    #     plt.savefig('static/filtered_graphs.png')
    #     graph_url = 'static/filtered_graphs.png'
        
    # else:
    #     # For full data
    #     plt.savefig('static/graphs.png')
    #     graph_url = None
    #     plt.savefig('static/graphs.png')
    #     graph_url = None
    #     plt.savefig('static/graphs.png')
    #     graph_url = None
    
    # plt.close()
    
    return render_template('graphs.html', graph_url=graph_url)

# Add these filtered data functions
def lineplot_filtered(filtered_data):
    eventcount = {}
    for row in filtered_data:
        time1 = row[1].strip()
        time = time1[:24]# Adjust this based on your timestamp format
        
        if time in eventcount:
            eventcount[time] += 1
        else:
            eventcount[time] = 1
        
    timexaxis = list(sorted(eventcount.keys()))
    numberyaxis = [eventcount[t] for t in timexaxis]  
    return timexaxis, numberyaxis

def piechart_filtered(filtered_data):
    levelcount = {}
    for row in filtered_data:
        level = row[2].strip()
        
        if level in levelcount:
            levelcount[level] += 1
        else:
            levelcount[level] = 1
    
    labels = list(levelcount.keys()) 
    sizes = list(levelcount.values())
    
    return labels, sizes

def bargraph_filtered(filtered_data):
    eventIdcounts = {'E1': 0, 'E2': 0, 'E3': 0, 'E4': 0, 'E5': 0, 'E6': 0}
    for row in filtered_data:
        eventId = row[4].strip()
        if eventId in eventIdcounts:
            eventIdcounts[eventId] += 1
        
    return list(eventIdcounts.keys()), list(eventIdcounts.values())

@app.route('/run', methods=['POST']) #server for text box python editor, used to process code submitted in a textbox.
def run():
    plot_url="" #path to generated plot image
    c = ""  #c stores the submitted code so it can be shown again in the text box.
    if request.method == 'POST':
        code = request.form['code']
         
        if ('import' in code or 'from' in code):
            allowed_imports = ['import numpy', 'from numpy',
                               'import matplotlib', 'from matplotlib']
            lines = code.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('import') or line.startswith('from'):
                    if not any(allowed in line for allowed in allowed_imports):
                        return render_template('graphs.html', error='Only matplotlib and numpy imports are allowed.', c=c)

        exec(code)
        #saving the plot
        c = code
        plot_url = 'static/custom_plot.png' 
        plt.savefig(os.path.join('static', 'custom_plot.png'))
        plt.close() #ensures the plot is cleared before the next one is created.
        return render_template('graphs.html',plot_url = plot_url, c = c) #Sends the image path and code back to the HTML template for display.
    else :
        return render_template('graphs.html',plot_url = plot_url, c = c) 
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
