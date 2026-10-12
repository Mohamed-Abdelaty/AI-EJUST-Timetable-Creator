import sqlite3, os, csv

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB = os.path.join(DATA_DIR, "database.db")


def read_csv_dict_safe(path):
    rows = []
    if not os.path.exists(path):
        print(f"File not found: {os.path.basename(path)} (Skipping)")
        return rows
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            row = { (k.strip() if k else ""): (v.strip() if v else "") for k,v in r.items() }
            if any(v for v in row.values()):
                rows.append(row)
    return rows


print(" Creating database and tables")

# remove old db
if os.path.exists(DB):
    os.remove(DB)
    print(" Old database deleted")

conn = sqlite3.connect(DB)
cur = conn.cursor()

# ------------------------------------------------------
#  Create Tables
# ------------------------------------------------------
cur.executescript("""
DROP TABLE IF EXISTS Instructors;
DROP TABLE IF EXISTS Courses;
DROP TABLE IF EXISTS Rooms;
DROP TABLE IF EXISTS TimeSlots;
DROP TABLE IF EXISTS Sections;
DROP TABLE IF EXISTS Schedule;

CREATE TABLE Instructors (
    InstructorID TEXT PRIMARY KEY,
    Name TEXT,
    PreferredSlots TEXT,
    QualifiedCourses TEXT
);

CREATE TABLE Courses (
    CourseID TEXT PRIMARY KEY,
    CourseName TEXT,
    Credits INTEGER,
    Type TEXT,
    Year TEXT,
    Department TEXT
);

CREATE TABLE Rooms (
    RoomID TEXT PRIMARY KEY,
    Type TEXT,
    Capacity INTEGER
);

CREATE TABLE TimeSlots (
    Day TEXT,
    StartTime TEXT,
    EndTime TEXT
);

CREATE TABLE Sections (
    SectionID TEXT PRIMARY KEY,
    Semester INTEGER,
    StudentCount INTEGER,
    Year TEXT,
    GroupName TEXT
);

CREATE TABLE Schedule (
    Day TEXT,
    StartTime TEXT,
    EndTime TEXT,
    CourseID TEXT,
    CourseName TEXT,
    Instructor TEXT,
    Room TEXT,
    GroupName TEXT,
    SectionID TEXT,
    Year TEXT
);
""")

# Load CSV Data
instructors_rows = read_csv_dict_safe(os.path.join(DATA_DIR, "Instructors.csv"))
courses_rows = read_csv_dict_safe(os.path.join(DATA_DIR, "Courses.csv"))
rooms_rows = read_csv_dict_safe(os.path.join(DATA_DIR, "Rooms.csv"))
timeslot_rows = read_csv_dict_safe(os.path.join(DATA_DIR, "TimeSlots.csv"))
sections_rows = read_csv_dict_safe(os.path.join(DATA_DIR, "Sections.csv"))


# Insert Functions
def insert_instructors(rows):
    data=[]; seen=set()
    for r in rows:
        pid=r.get("InstructorID","").strip()
        if not pid or pid in seen: continue
        seen.add(pid)
        data.append((pid, r.get("Name","").strip(), r.get("PreferredSlots","").strip(), r.get("QualifiedCourses","").strip()))
    if data:
        cur.executemany("INSERT INTO Instructors VALUES (?,?,?,?)", data)
    print(f"Inserted {len(data)} instructors")


def insert_courses(rows):
    data=[]; seen=set()
    for r in rows:
        cid=r.get("CourseID","").strip()
        if not cid or cid in seen: continue
        seen.add(cid)
        try: cr=int(r.get("Credits","0").strip())
        except: cr=0
        year = r.get("Year","").strip()
        dept = r.get("Department","").strip() or "CSIT" 
        data.append((
            cid,
            r.get("CourseName","").strip(),
            cr,
            r.get("Type","").strip(),
            year,
            dept
        ))
    if data:
        cur.executemany("INSERT INTO Courses VALUES (?,?,?,?,?,?)", data)
    print(f"Inserted {len(data)} courses.")


def insert_rooms(rows):
    data=[]; seen=set()
    for r in rows:
        rid=r.get("RoomID","").strip()
        if not rid or rid in seen: continue
        seen.add(rid)
        try: cap=int(r.get("Capacity","0").strip())
        except: cap=0
        data.append((rid, r.get("Type","").strip(), cap))
    if data:
        cur.executemany("INSERT INTO Rooms VALUES (?,?,?)", data)
    print(f"Inserted {len(data)} rooms.")


def insert_timeslots(rows):
    data=[]
    for r in rows:
        d=r.get("Day","").strip(); s=r.get("StartTime","").strip(); e=r.get("EndTime","").strip()
        if d and s: data.append((d,s,e))
    if data:
        cur.executemany("INSERT INTO TimeSlots VALUES (?,?,?)", data)
    print(f"Inserted {len(data)} timeslots.")


def insert_sections(rows):
    data=[]; seen=set()
    for r in rows:
        sid=r.get("SectionID","").strip()
        if not sid or sid in seen: continue
        seen.add(sid)
        try: sem=int(r.get("Semester","0").strip() or "0")
        except: sem=0
        try: cnt=int(r.get("StudentCount","0").strip() or "0")
        except: cnt=0
        year = r.get("Year","").strip()
        grp = r.get("GroupName","").strip()

        if year in ["3rd Year", "4th Year"] and grp.startswith("Group"):
            for dept, num in {"CSC": 2, "CNC": 3, "AID": 3, "BIF": 1}.items():
                for i in range(1, num + 1):
                    data.append((f"{sid}_{dept}{i}", sem, cnt, year, f"{dept} Sec {i}"))
        else:
            data.append((sid, sem, cnt, year, grp))
    if data:
        cur.executemany("INSERT INTO Sections VALUES (?,?,?,?,?)", data)
    print(f"Inserted {len(data)} sections.")


# Insert All Tables
insert_instructors(instructors_rows)
insert_courses(courses_rows)
insert_rooms(rooms_rows)
insert_timeslots(timeslot_rows)
insert_sections(sections_rows)

conn.commit()
conn.close()
print(f"Database created successfully at: {DB}")
