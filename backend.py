# importing Flask and other modules
from flask import Flask, request, render_template, redirect, url_for, send_file
import flask
import pandas as pd
import ILPAlgorithm
import GreedyAlgorithm
 
# Flask constructor
app = Flask(__name__, template_folder='Templates')  
file_name = '' 
# A decorator used to tell the application
# which URL is associated with the function
@app.route('/', methods =["GET"])
def index():
    return render_template("index.html")

@app.route('/ilp', methods =["POST"])
def run_alg():
    files = flask.request.files.getlist('file')
    print(files[0])
    prefs = pd.read_csv(files[0])

    sems = pd.read_csv(files[1])
    file_name = files[0].filename

    

    w_1 = request.form.get("first") or 100
    w_2 = request.form.get("scnd") or 30
    w_3 = request.form.get("third") or 20
    w_4 = request.form.get("lt_third") or 0

    topk = request.form.get("threshold") or 3

    semester = request.form.get("sem")

    priorities = []
    if request.form.get("change-priority") == 'yes':

        priorities.append(request.form.get("AB-priority") or 1)
        priorities.append(request.form.get("BSE-priority") or 1)
        priorities.append(request.form.get("Base-priority") or 1)

    successful, output_file_name, report_file_name, _, _ = ILPAlgorithm.main(prefs, sems, w_1, w_2, w_3, w_4, topk, semester, file_name, priorities)
    
    if not successful:
        return render_template('./infeasible.html')
  
    return render_template("./results.html", output = output_file_name, report = report_file_name)

@app.route('/greedy', methods =["POST"])
def test_greedy_alg():
    files = flask.request.files.getlist('file')
    print(files[0])
    prefs = pd.read_csv(files[0])
    sems = pd.read_csv(files[1])
    file_name = files[0].filename
    semester = request.form.get("sem")
    _, _, output_file_name, report_file_name = GreedyAlgorithm.algorithm([prefs, sems], semester, file_name)
    return render_template("./results.html", output = output_file_name, report = report_file_name)

@app.route('/downlaod_output')
def download_file1():
    output_filename = flask.request.args.get("output")
    output_path = output_filename

    return send_file(output_path, as_attachment=True)

@app.route('/downlaod_report')
def download_file2():
    report_filename = flask.request.args.get("report")

    report_path = report_filename
    return send_file(report_path, as_attachment=True)
 
if __name__ == "__main__":
    app.run()