import json
from datetime import datetime
from enum import Enum

class UserType(Enum):
    ADMIN = "Admin"
    TEACHER = "Teacher"
    STUDENT = "Student"
    STAFF = "Staff"

class GradeLevel(Enum):
    FRESHMAN = "9th Grade"
    SOPHOMORE = "10th Grade"
    JUNIOR = "11th Grade"
    SENIOR = "12th Grade"

class Subject(Enum):
    MATH = "Mathematics"
    SCIENCE = "Science"
    ENGLISH = "English"
    HISTORY = "History"
    ART = "Art"
    PHYSICAL_EDUCATION = "Physical Education"

class User:
    def __init__(self, user_id, name, email, password, user_type):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password = password  # In production, use hashed passwords
        self.user_type = UserType(user_type)
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'password': self.password,
            'user_type': self.user_type.value,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(
            data['user_id'],
            data['name'],
            data['email'],
            data['password'],
            data['user_type']
        )
        user.created_at = datetime.fromisoformat(data['created_at'])
        return user

class Student(User):
    def __init__(self, user_id, name, email, password, grade_level):
        super().__init__(user_id, name, email, password, UserType.STUDENT.value)
        self.grade_level = GradeLevel(grade_level)
        self.enrolled_courses = []
        self.attendance = {}
        self.grades = {}
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'grade_level': self.grade_level.value,
            'enrolled_courses': self.enrolled_courses,
            'attendance': {k: v.isoformat() for k, v in self.attendance.items()},
            'grades': self.grades
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        student = cls(
            data['user_id'],
            data['name'],
            data['email'],
            data['password'],
            data['grade_level']
        )
        student.enrolled_courses = data['enrolled_courses']
        student.attendance = {k: datetime.fromisoformat(v) for k, v in data['attendance'].items()}
        student.grades = data['grades']
        return student

class Teacher(User):
    def __init__(self, user_id, name, email, password, subjects):
        super().__init__(user_id, name, email, password, UserType.TEACHER.value)
        self.subjects = [Subject(subject) for subject in subjects]
        self.assigned_courses = []
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'subjects': [subject.value for subject in self.subjects],
            'assigned_courses': self.assigned_courses
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        teacher = cls(
            data['user_id'],
            data['name'],
            data['email'],
            data['password'],
            data['subjects']
        )
        teacher.assigned_courses = data['assigned_courses']
        return teacher

class Course:
    def __init__(self, course_id, name, subject, teacher_id, schedule, classroom, capacity=30):
        self.course_id = course_id
        self.name = name
        self.subject = Subject(subject)
        self.teacher_id = teacher_id
        self.schedule = schedule  # e.g., "Mon/Wed 10:00-11:30"
        self.classroom = classroom
        self.capacity = capacity
        self.enrolled_students = []
        self.syllabus = ""
    
    def to_dict(self):
        return {
            'course_id': self.course_id,
            'name': self.name,
            'subject': self.subject.value,
            'teacher_id': self.teacher_id,
            'schedule': self.schedule,
            'classroom': self.classroom,
            'capacity': self.capacity,
            'enrolled_students': self.enrolled_students,
            'syllabus': self.syllabus
        }
    
    @classmethod
    def from_dict(cls, data):
        course = cls(
            data['course_id'],
            data['name'],
            data['subject'],
            data['teacher_id'],
            data['schedule'],
            data['classroom'],
            data['capacity']
        )
        course.enrolled_students = data['enrolled_students']
        course.syllabus = data['syllabus']
        return course
    
    def enroll_student(self, student_id):
        if len(self.enrolled_students) < self.capacity:
            if student_id not in self.enrolled_students:
                self.enrolled_students.append(student_id)
                return True
        return False
    
    def remove_student(self, student_id):
        if student_id in self.enrolled_students:
            self.enrolled_students.remove(student_id)
            return True
        return False

class School:
    def __init__(self, name):
        self.name = name
        self.users = {}  # user_id: User
        self.courses = {}  # course_id: Course
        self.current_user = None
        self.load_data()
    
    def save_data(self):
        data = {
            'name': self.name,
            'users': {user_id: user.to_dict() for user_id, user in self.users.items()},
            'courses': {course_id: course.to_dict() for course_id, course in self.courses.items()}
        }
        with open('school_data.json', 'w') as f:
            json.dump(data, f)
    
    def load_data(self):
        try:
            with open('school_data.json', 'r') as f:
                data = json.load(f)
                self.name = data['name']
                self.users = {}
                for user_id, user_data in data['users'].items():
                    if user_data['user_type'] == UserType.STUDENT.value:
                        self.users[user_id] = Student.from_dict(user_data)
                    elif user_data['user_type'] == UserType.TEACHER.value:
                        self.users[user_id] = Teacher.from_dict(user_data)
                    else:
                        self.users[user_id] = User.from_dict(user_data)
                self.courses = {course_id: Course.from_dict(course_data) 
                              for course_id, course_data in data['courses'].items()}
        except FileNotFoundError:
            # Create default admin if no data exists
            admin = User("admin001", "Admin", "admin@school.com", "admin123", UserType.ADMIN.value)
            self.users[admin.user_id] = admin
            self.save_data()
    
    def generate_id(self, prefix):
        return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def create_user(self, name, email, password, user_type, **kwargs):
        if user_type == UserType.STUDENT.value:
            user_id = self.generate_id("STU")
            grade_level = kwargs.get('grade_level', GradeLevel.FRESHMAN.value)
            self.users[user_id] = Student(user_id, name, email, password, grade_level)
        elif user_type == UserType.TEACHER.value:
            user_id = self.generate_id("TCH")
            subjects = kwargs.get('subjects', [])
            self.users[user_id] = Teacher(user_id, name, email, password, subjects)
        else:
            user_id = self.generate_id("USR")
            self.users[user_id] = User(user_id, name, email, password, user_type)
        
        self.save_data()
        return user_id
    
    def login(self, email, password):
        for user in self.users.values():
            if user.email == email and user.password == password:
                self.current_user = user
                return True, f"Welcome {user.name}!"
        return False, "Invalid credentials"
    
    def logout(self):
        self.current_user = None
        return True, "Logged out successfully"
    
    def create_course(self, name, subject, teacher_id, schedule, classroom, capacity=30):
        if not self.current_user or self.current_user.user_type != UserType.ADMIN:
            return None, "Admin access required"
        
        if teacher_id not in self.users or self.users[teacher_id].user_type != UserType.TEACHER:
            return None, "Invalid teacher ID"
        
        course_id = self.generate_id("CRS")
        self.courses[course_id] = Course(
            course_id, name, subject, teacher_id, schedule, classroom, capacity
        )
        
        # Add course to teacher's assigned courses
        teacher = self.users[teacher_id]
        teacher.assigned_courses.append(course_id)
        
        self.save_data()
        return course_id, "Course created successfully"
    
    def enroll_student(self, course_id, student_id):
        if not self.current_user or self.current_user.user_type != UserType.ADMIN:
            return False, "Admin access required"
        
        if course_id not in self.courses:
            return False, "Course not found"
        
        if student_id not in self.users or self.users[student_id].user_type != UserType.STUDENT:
            return False, "Invalid student ID"
        
        course = self.courses[course_id]
        student = self.users[student_id]
        
        if course.enroll_student(student_id):
            student.enrolled_courses.append(course_id)
            self.save_data()
            return True, "Student enrolled successfully"
        return False, "Enrollment failed (course may be full)"
    
    def record_attendance(self, student_id, date=None, present=True):
        if not self.current_user or self.current_user.user_type not in [UserType.TEACHER, UserType.ADMIN]:
            return False, "Teacher or admin access required"
        
        if student_id not in self.users or self.users[student_id].user_type != UserType.STUDENT:
            return False, "Invalid student ID"
        
        student = self.users[student_id]
        date = date or datetime.now()
        student.attendance[date.date().isoformat()] = present
        self.save_data()
        return True, "Attendance recorded"
    
    def record_grade(self, student_id, course_id, grade):
        if not self.current_user or self.current_user.user_type not in [UserType.TEACHER, UserType.ADMIN]:
            return False, "Teacher or admin access required"
        
        if student_id not in self.users or self.users[student_id].user_type != UserType.STUDENT:
            return False, "Invalid student ID"
        
        if course_id not in self.courses:
            return False, "Course not found"
        
        student = self.users[student_id]
        if course_id not in student.enrolled_courses:
            return False, "Student not enrolled in this course"
        
        student.grades[course_id] = grade
        self.save_data()
        return True, "Grade recorded"

def main():
    school = School("Python High School")
    
    while True:
        print("\n=== School Management System ===")
        print(f"School: {school.name}")
        
        if school.current_user:
            print(f"\nLogged in as: {school.current_user.name} ({school.current_user.user_type.value})")
            
            if school.current_user.user_type == UserType.ADMIN:
                print("1. Create User")
                print("2. Create Course")
                print("3. Enroll Student")
                print("4. View All Users")
                print("5. View All Courses")
                print("6. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    print("\nCreate New User")
                    name = input("Name: ")
                    email = input("Email: ")
                    password = input("Password: ")
                    print("User Types:")
                    for user_type in UserType:
                        print(user_type.value)
                    user_type = input("User Type: ")
                    
                    if user_type == UserType.STUDENT.value:
                        print("Grade Levels:")
                        for grade in GradeLevel:
                            print(grade.value)
                        grade_level = input("Grade Level: ")
                        user_id = school.create_user(name, email, password, user_type, grade_level=grade_level)
                    elif user_type == UserType.TEACHER.value:
                        print("Subjects (comma separated):")
                        for subject in Subject:
                            print(subject.value)
                        subjects = [s.strip() for s in input("Subjects: ").split(",")]
                        user_id = school.create_user(name, email, password, user_type, subjects=subjects)
                    else:
                        user_id = school.create_user(name, email, password, user_type)
                    
                    print(f"User created with ID: {user_id}")
                
                elif choice == '2':
                    print("\nCreate New Course")
                    name = input("Course Name: ")
                    print("Subjects:")
                    for subject in Subject:
                        print(subject.value)
                    subject = input("Subject: ")
                    teacher_id = input("Teacher ID: ")
                    schedule = input("Schedule (e.g., Mon/Wed 10:00-11:30): ")
                    classroom = input("Classroom: ")
                    capacity = input("Capacity (default 30): ") or 30
                    
                    try:
                        course_id, message = school.create_course(
                            name, subject, teacher_id, schedule, classroom, int(capacity))
                        print(f"{message} Course ID: {course_id}")
                    except ValueError:
                        print("Invalid capacity value")
                
                elif choice == '3':
                    print("\nEnroll Student in Course")
                    student_id = input("Student ID: ")
                    course_id = input("Course ID: ")
                    success, message = school.enroll_student(course_id, student_id)
                    print(message)
                
                elif choice == '4':
                    print("\nAll Users:")
                    for user_id, user in school.users.items():
                        print(f"\nID: {user_id}")
                        print(f"Name: {user.name}")
                        print(f"Type: {user.user_type.value}")
                        if user.user_type == UserType.STUDENT:
                            print(f"Grade: {user.grade_level.value}")
                        elif user.user_type == UserType.TEACHER:
                            print(f"Subjects: {[s.value for s in user.subjects]}")
                
                elif choice == '5':
                    print("\nAll Courses:")
                    for course_id, course in school.courses.items():
                        print(f"\nID: {course_id}")
                        print(f"Name: {course.name}")
                        print(f"Subject: {course.subject.value}")
                        print(f"Teacher: {school.users[course.teacher_id].name}")
                        print(f"Schedule: {course.schedule}")
                        print(f"Classroom: {course.classroom}")
                        print(f"Enrolled: {len(course.enrolled_students)}/{course.capacity}")
                
                elif choice == '6':
                    school.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif school.current_user.user_type == UserType.TEACHER:
                print("1. View My Courses")
                print("2. Record Attendance")
                print("3. Record Grades")
                print("4. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    teacher = school.current_user
                    print("\nYour Courses:")
                    for course_id in teacher.assigned_courses:
                        if course_id in school.courses:
                            course = school.courses[course_id]
                            print(f"\nID: {course_id}")
                            print(f"Name: {course.name}")
                            print(f"Subject: {course.subject.value}")
                            print(f"Schedule: {course.schedule}")
                            print(f"Classroom: {course.classroom}")
                            print(f"Students Enrolled: {len(course.enrolled_students)}")
                
                elif choice == '2':
                    print("\nRecord Attendance")
                    student_id = input("Student ID: ")
                    date = input("Date (YYYY-MM-DD, leave blank for today): ")
                    present = input("Present? (Y/N): ").lower() == 'y'
                    
                    try:
                        date_obj = datetime.strptime(date, "%Y-%m-%d") if date else None
                        success, message = school.record_attendance(student_id, date_obj, present)
                        print(message)
                    except ValueError:
                        print("Invalid date format")
                
                elif choice == '3':
                    print("\nRecord Grade")
                    student_id = input("Student ID: ")
                    course_id = input("Course ID: ")
                    grade = input("Grade: ")
                    
                    success, message = school.record_grade(student_id, course_id, grade)
                    print(message)
                
                elif choice == '4':
                    school.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
            
            elif school.current_user.user_type == UserType.STUDENT:
                print("1. View My Courses")
                print("2. View My Grades")
                print("3. View My Attendance")
                print("4. Logout")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    student = school.current_user
                    print("\nYour Courses:")
                    for course_id in student.enrolled_courses:
                        if course_id in school.courses:
                            course = school.courses[course_id]
                            print(f"\nID: {course_id}")
                            print(f"Name: {course.name}")
                            print(f"Subject: {course.subject.value}")
                            print(f"Teacher: {school.users[course.teacher_id].name}")
                            print(f"Schedule: {course.schedule}")
                            print(f"Classroom: {course.classroom}")
                
                elif choice == '2':
                    student = school.current_user
                    print("\nYour Grades:")
                    for course_id, grade in student.grades.items():
                        if course_id in school.courses:
                            course = school.courses[course_id]
                            print(f"{course.name}: {grade}")
                
                elif choice == '3':
                    student = school.current_user
                    print("\nYour Attendance:")
                    for date, present in student.attendance.items():
                        status = "Present" if present else "Absent"
                        print(f"{date}: {status}")
                
                elif choice == '4':
                    school.logout()
                    print("Logged out successfully")
                
                else:
                    print("Invalid choice")
        
        else:
            print("\n1. Login")
            print("2. Exit")
            
            choice = input("Enter your choice: ")
            
            if choice == '1':
                email = input("Email: ")
                password = input("Password: ")
                success, message = school.login(email, password)
                print(message)
            
            elif choice == '2':
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice")

if __name__ == "__main__":
    main()