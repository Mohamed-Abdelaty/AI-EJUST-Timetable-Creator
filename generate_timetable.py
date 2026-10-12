import sqlite3, random, time, sys
from collections import defaultdict

# Fix Windows console encoding for Unicode characters
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DB = "data/database.db"
random.seed(time.time())

GROUPS = ["Group 1", "Group 2", "Group 3"]
DEPARTMENTS = ["CSC", "CNC", "AID", "BIF"]
MAX_DOMAIN = 500
TIME_LIMIT = 300.0

SLOT_ORDER = ['9:00 AM', '10:45 AM', '12:30 PM', '2:15 PM']

# Load Data
def load_data():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT CourseID, CourseName, Credits, Type, Year, Department FROM Courses")
    courses = c.fetchall()
    c.execute("SELECT InstructorID, Name, QualifiedCourses FROM Instructors")
    instructors = c.fetchall()
    c.execute("SELECT RoomID, Type, Capacity FROM Rooms")
    rooms = c.fetchall()
    c.execute("SELECT Day, StartTime, EndTime FROM TimeSlots ORDER BY Day, StartTime")
    timeslots = c.fetchall()
    c.execute("SELECT SectionID, StudentCount FROM Sections")
    sections = c.fetchall()
    conn.close()

    instr = []
    for iid, name, qc in instructors:
        qset = set(x.strip() for x in (qc or "").split(",") if x.strip())
        instr.append((iid, name, qset))
    return courses, instr, rooms, timeslots, sections


# ------------------------------------------------------
# Build Sections Map
# ------------------------------------------------------
def build_sections_map(sections):
    m = defaultdict(list)
    for sid, cnt in sections:
     
        parts = sid.split("_")
        if len(parts) == 1: 
            if len(sid) >= 4:
                year_num = sid[1]
                group_num = sid[3]
            else:
                year_num = sid[1] if len(sid) > 1 else "1"
                group_num = sid[3] if len(sid) > 3 else "1"
            year_label = f"{year_num}st Year" if year_num == "1" else \
                         f"{year_num}nd Year" if year_num == "2" else \
                         f"{year_num}rd Year" if year_num == "3" else \
                         f"{year_num}th Year"
            group_label = f"Group {group_num}"
        else:  
            ych = parts[0][1] if len(parts[0]) > 1 else "3"
            year_label = f"{ych}rd Year" if ych == "3" else f"{ych}th Year"
            group_label = parts[1]
        m[(year_label, group_label)].append((sid, cnt))
    return m


# ------------------------------------------------------
# Build CSP Variables
# ------------------------------------------------------
def build_variables(courses, sections_map):
    vars_list = []
    for c in courses:
        cid, cname, credits, ctype, year, dept = c

        if year in ["1st Year", "2nd Year"]:
            for grp in GROUPS:
                if ctype.lower().startswith("lab"):
                    for sid, cnt in sections_map.get((year, grp), []):
                        vars_list.append((c, year, grp, sid))
                else:
                    if sections_map.get((year, grp)):
                        vars_list.append((c, year, grp, None))
        else:
            depts = [d.strip() for d in (dept or "").split(",") if d.strip()]
            for d in depts:
                if ctype.lower().startswith("lab"):
                    for sid, cnt in sections_map.get((year, d), []):
                        vars_list.append((c, year, d, sid))
                else:
                    if sections_map.get((year, d)):
                        vars_list.append((c, year, d, None))
    return vars_list


# ------------------------------------------------------
# Domain Builder
# ------------------------------------------------------
def build_domain_for_var(var, instructors, rooms, timeslots):
    course, year, group, sid = var
    cid, cname, credits, ctype, _, _ = course
    qualified = [ins for ins in instructors if cid in ins[2]]
    if not qualified:
        qualified = instructors[:]
    valid_rooms = [r for r in rooms if r[1].lower() == ctype.lower()]
    if not valid_rooms:
        valid_rooms = rooms[:]

    dom = []
    for iid, iname, _ in qualified:
        for rid, rtype, cap in valid_rooms:
            for (day, start, end) in timeslots:
                dom.append((iid, iname, rid, day, start, end))
    if len(dom) > MAX_DOMAIN:
        random.shuffle(dom)
        dom = dom[:MAX_DOMAIN]
    return dom


# ------------------------------------------------------
# Hard Constraints
# ------------------------------------------------------
def violates(assignments, option, var):
    iid, iname, rid, day, start, end = option
    course, year, group, sid = var

    def to_minutes(t):
        t = t.strip().upper().replace(".", ":")
        if ":" not in t:
            return 0
        parts = t.replace("AM", "").replace("PM", "").strip().split(":")
        h, m = int(parts[0]), int(parts[1])
        if "PM" in t and h != 12:
            h += 12
        if "AM" in t and h == 12:
            h = 0
        return h * 60 + m

    start_m, end_m = to_minutes(start), to_minutes(end)

    for v, opt in assignments.items():
        _, oy, og, osid = v
        oi, oname, oroom, oday, ost, oend = opt
        if oday != day:
            continue

        ost_m, oend_m = to_minutes(ost), to_minutes(oend)
        overlap = not (end_m <= ost_m or start_m >= oend_m)

        # Instructor conflict
        if oi == iid and overlap:
            return True

        # Room conflict
        if oroom == rid and overlap:
            return True

        # Same group/department conflict
        if (oy, og) == (year, group):
            if sid is None or osid is None or sid == osid:
                if overlap:
                    return True
    return False




# ------------------------------------------------------
# Soft scoring: prefer middle slots & minimize gaps
# ------------------------------------------------------
def soft_score(var, opt, assignments):
    """
    Higher score == more preferred.
    - prefer middle slots (10:45,12:30)
    - avoid earliest (9:00) and latest (2:15) if possible
    - reward choices that reduce gaps for same (year,group) on same day
    - penalize too many classes for same group on same day (to spread)
    """
    iid, iname, rid, day, start, end = opt
    course, year, group, sid = var

    score = 0.0

    if start == "10:45 AM" or start == "12:30 PM":
        score += 2.0
    elif start == "9:00 AM" or start == "2:15 PM":
        score -= 1.0

    same_group_day = []
    same_group_all_days = []
    same_instructor_day = []
    for v_assigned, o_assigned in assignments.items():
        _, y2, g2, sid2 = v_assigned
        ii, nn, rr, od, st, en = o_assigned
        if (y2, g2) == (year, group):
            same_group_all_days.append((od, st))
            if od == day:
                same_group_day.append(st)
        if ii == iid and od == day:
            same_instructor_day.append(st)

    if len(same_group_day) > 2: 
        score -= 1.5

    try:
        idx = SLOT_ORDER.index(start)
    except ValueError:
        idx = None

    if same_group_day and idx is not None:
        dists = []
        for s in same_group_day:
            try:
                j = SLOT_ORDER.index(s)
                dists.append(abs(j - idx))
            except ValueError:
                continue
        if dists:
            mind = min(dists)
            if mind == 1:
                score += 1.5
            elif mind >= 2:
                score -= 1.0 * (mind - 1)
        else:
            score += 0.2

    # if len(same_instructor_day) >= 2:
    #     score -= 0.8

    score += random.random() * 0.01
    return score


# ------------------------------------------------------
# Forward Checking (unchanged logic)
# ------------------------------------------------------
def forward_check(domains, var, opt):
    pruned = {}
    iid, iname, rid, day, start, end = opt
    course, year, group, sid = var
    for other, dom in domains.items():
        if other == var: continue
        new_dom, removed = [], []
        for o in dom:
            oi, oname, oroom, oday, ost, oend = o
            if oday == day and ost == start:
                if oi == iid or oroom == rid:
                    removed.append(o); continue
                _, oy, og, osid = other
                if (oy, og) == (year, group):
                    if sid is None or osid is None or sid == osid:
                        removed.append(o); continue
            new_dom.append(o)
        if removed:
            pruned[other] = removed
            domains[other] = new_dom
    return pruned

def restore_domains(domains, pruned):
    for v, items in pruned.items():
        domains[v].extend(items)


# ------------------------------------------------------
# Variable ordering & domain ordering with soft scoring
# ------------------------------------------------------
def select_var(unassigned, domains):
    best = None; best_len = 999999
    for v in unassigned:
        l = len(domains.get(v, []))
        if l < best_len:
            best = v; best_len = l
    return best

def order_domain_values(var, domains, assignments):
    opts = domains[var][:]
    scored = []
    for o in opts:
        s = soft_score(var, o, assignments)
        scored.append((s, o))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [o for _, o in scored]


# ------------------------------------------------------
# Backtracking
# ------------------------------------------------------
def backtrack(unassigned, domains, assignments, start_time):
    if time.time() - start_time > TIME_LIMIT:
        return False, "timeout"
    if not unassigned:
        return True, "complete"
    var = select_var(unassigned, domains)
    if not var or not domains.get(var):
        return False, "empty_domain"

    for opt in order_domain_values(var, domains, assignments):
        if violates(assignments, opt, var):
            continue
        assignments[var] = opt
        pruned = forward_check(domains, var, opt)
        unassigned.remove(var)
        ok, reason = backtrack(unassigned, domains, assignments, start_time)
        if ok:
            return True, reason
        unassigned.append(var)
        restore_domains(domains, pruned)
        assignments.pop(var, None)
    return False, "fail"



# ------------------------------------------------------
# Solve all-year helper & main generate_and_save
# ------------------------------------------------------
def solve_for_year(year, courses, instructors, rooms, timeslots, sections_map):
    variables = [v for v in build_variables(courses, sections_map) if v[1] == year]
    print(f"--> {year}: {len(variables)} variables")
    if not variables:
        print(f" No variables for {year}")
        return []

    domains = {v: build_domain_for_var(v, instructors, rooms, timeslots) for v in variables}
    unassigned = variables[:]
    assignments = {}
    t0 = time.time()
    ok, reason = backtrack(unassigned, domains, assignments, t0)
    print(f"{year} finished in {time.time()-t0:.2f}s => ok={ok}, reason={reason}")

    rows = []
    for var, opt in assignments.items():
        course, year, group, sid = var
        cid, cname = course[0], course[1]
        iid, iname, rid, day, start, end = opt
        
        if sid is None:
            sids = [t[0] for t in sections_map.get((year, group), [])]
            for secid in sids:
                rows.append((day, start, end, cid, cname, iname, rid, group, secid, year))
        else:
            rows.append((day, start, end, cid, cname, iname, rid, group, sid, year))
    return rows


def generate_and_save():
    courses, instructors, rooms, timeslots, sections = load_data()
    sections_map = build_sections_map(sections)
    all_rows = []

    for year in ["1st Year", "2nd Year", "3rd Year", "4th Year"]:
        print(f"\nGenerating timetable for {year} ...")
        rows = solve_for_year(year, courses, instructors, rooms, timeslots, sections_map)
        all_rows.extend(rows)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("DELETE FROM Schedule")
    if all_rows:
        cur.executemany("INSERT INTO Schedule VALUES (?,?,?,?,?,?,?,?,?,?)", all_rows)
    conn.commit()
    conn.close()

    print(f"\n Done. Total scheduled = {len(all_rows)}")


if __name__ == "__main__":
    generate_and_save()
