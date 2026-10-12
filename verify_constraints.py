# import sqlite3
# import os

# DB = "data/database.db"

# def check():
#     if not os.path.exists(DB):
#         print("Database not found.")
#         return

#     conn = sqlite3.connect(DB)
#     c = conn.cursor()
#     c.execute("SELECT Day, StartTime, EndTime, CourseID, CourseName, Instructor, Room, GroupName, SectionID, Year FROM Schedule")
#     rows = c.fetchall()
#     conn.close()

#     if not rows:
#         print(" No schedule data found.")
#         return

#     # Check for Instructor Conflicts
#     # Map: (Instructor, Day, StartTime) -> (Year, CourseID)
#     instr_map = {}
#     room_map = {}
    
#     instr_conflicts = 0
#     room_conflicts = 0
    
#     for r in rows:
#         day, start = r[0], r[1]
#         instr = r[5]
#         room = r[6]
#         course = r[3]
#         year = r[9]
        
#         if not instr or instr == "None": continue
#         if not room or room == "None": continue

#         # We store list of assignments
#         key = (instr, day, start)
#         if key not in instr_map: instr_map[key] = []
#         instr_map[key].append(r)

#         rkey = (room, day, start)
#         if rkey not in room_map: room_map[rkey] = []
#         room_map[rkey].append(r)

#     # Analyze overlaps
#     print("--- Verifying Instructor Conflicts ---")
#     for k, assignments in instr_map.items():
#         if len(assignments) > 1:
#             # Check if all assignments are in the same room (merged class)
#             rooms = set(a[6] for a in assignments)
#             if len(rooms) > 1:
#                 print(f" Instructor {k[0]} double booked at {k[1]} {k[2]} in rooms: {rooms}")
#                 instr_conflicts += 1
#             else:
#                  # Check if Time is same (it is by key)
#                  # This is likely a merged class (same instructor, same room, same time, diff sections). 
#                  # This is ALLOWED usually.
#                  pass

#     print("--- Verifying Room Conflicts ---")
#     for k, assignments in room_map.items():
#         # k is (Room, Day, Start)
#         if len(assignments) > 1:
#             # Multiple classes in same room at same time.
#             # Only allowed if same Instructor (merged class).
#             instrs = set(a[5] for a in assignments)
#             if len(instrs) > 1:
#                 print(f" Room {k[0]} double booked at {k[1]} {k[2]} by instructors: {instrs}")
#                 room_conflicts += 1

#     if instr_conflicts == 0 and room_conflicts == 0:
#         print("No hard conflicts found!")
#     else:
#         print(f" Found {instr_conflicts} Instructor conflicts and {room_conflicts} Room conflicts.")

# if __name__ == "__main__":
#     check()
