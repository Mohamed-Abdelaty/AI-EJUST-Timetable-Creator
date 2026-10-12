# app.py
from flask import Flask, render_template, redirect, url_for
import sqlite3, os, subprocess, sys

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "database.db")

@app.route("/")
def home():
    return redirect("/timetable")

@app.route("/generate")
def generate():
    # شغّل سكريبت التوليد علطول
    try:
        script = os.path.join(BASE, "generate_timetable.py")
        subprocess.run([sys.executable, script], check=True, cwd=BASE,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    except Exception as e:
        return f"<h3 style='color:red;text-align:center'>Error while generating: {e}</h3>"
    return redirect(url_for("timetable"))

@app.route("/timetable")
def timetable():
    if not os.path.exists(DB):
        return "<h3 style='color:red;text-align:center'>Database not found. Run create_database.py first.</h3>"
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT Day,StartTime,EndTime,CourseID,CourseName,Instructor,Room,GroupName,SectionID,Year FROM Schedule")
    data = cur.fetchall()
    conn.close()
    if not data:
        return "<h3 style='color:red;text-align:center'>No timetable yet. <a href='/generate'>Generate Now</a></h3>"
    return render_template("timetable.html", data=data)

@app.route("/instructors")
def instructors():
    if not os.path.exists(DB):
        return "<h3 style='color:red;text-align:center'>Database not found. Run create_database.py first.</h3>"
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT Day,StartTime,EndTime,CourseID,CourseName,Instructor,Room,GroupName,SectionID,Year FROM Schedule ORDER BY Instructor,Day,StartTime")
    all_data = cur.fetchall()
    conn.close()
    if not all_data:
        return "<h3 style='color:red;text-align:center'>No timetable yet. <a href='/generate'>Generate Now</a></h3>"
    
    # Filter out instructor conflicts - keep only first occurrence for each (instructor, day, time)
    instructor_slots = {}
    filtered_data = []
    for row in all_data:
        day, start, end, cid, cname, instructor, room, group, secid, year = row
        key = (instructor, day, start)
        if key not in instructor_slots:
            instructor_slots[key] = True
            filtered_data.append(row)
    
    return render_template("instructor_timetable.html", data=filtered_data)

if __name__ == "__main__":
    app.run(debug=True)

