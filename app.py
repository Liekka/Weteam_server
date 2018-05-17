# coding:utf-8
from flask import Flask, request
from models import *
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./Weteam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# User部分


@app.route('/add_user', methods=['POST'])
def add_user():
    """使用于Post方法，用于向数据库中增加用户"""
    student_id = request.values.get('student_id')
    username = request.values.get('username')
    if request.values.get('is_teacher') == '0':
        is_teacher = 0;
    elif request.values.get('is_teacher') == '1':
        is_teacher = 1;
    else:
        error = "is_teacher is neither 0 or 1", 400
        return error
    attended_course_ids = request.values.get('attended_course_ids')
    profile_photo = request.values.get('profile_photo')
    u = User(student_id, username, is_teacher, profile_photo, attended_course_ids)
    error = u.add_user()
    return error


@app.route('/get_user', methods=['GET'])
def get_user():
    student_id = request.values.get('student_id')
    u = User.query.filter(User.student_id == student_id).first()
    if u is None:
        return "Cannot find such a student", 400
    else:
        return "%s" % json.dumps(u.__json__()), 200


@app.route('/delete_user', methods=['DELETE'])
def delete_user():
    pass


@app.route('/modify_attended_course', methods=['POST'])
def modify_attended_course():
    """更改用户加入或创建的课程信息"""
    student_id = request.values.get('student_id')
    attended_course_ids = request.values.get('attended_course_ids')
    u = User.query.filter(User.student_id == student_id).first()
    if u is None:
        return "Cannot find such a student", 400
    else:
        u.attended_course_ids = attended_course_ids
        db.session.add(u)
        db.session.commit()
        return "success", 200

# Team部分


@app.route('/add_team', methods=['POST'])
def add_team():
    """向数据库中增加队伍"""
    course_id = int(request.values.get('course_id'))
    leader_sid = request.values.get('leader_sid')
    team_info = request.values.get('team_info')
    max_team = request.values.get('max_team')
    available_team = request.values.get('available_team')
    team_members_id = request.values.get('team_members_id')
    # 只有存在对应的course_id才能创建对应的队伍
    if Course.query.filter(course_id == Course.course_id).first() is None:
        return 'Don\'t have such a course'

    team = Team(course_id, leader_sid, team_info, max_team, available_team, team_members_id)
    if Team.query.filter((team.course_id == Team.course_id) &
                         (team.leader_sid == Team.leader_sid)).first() is None:
        db.session.add(team)
        db.session.commit()
        return "success", 200
    else:
        return "Already have a team with this leader", 400


@app.route('/get_team', methods=['GET'])
def get_team():
    """获取队伍信息"""
    team_id = request.values.get('team_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    if team is None:
        return "Cannot find such a team", 400
    else:
        return "%s" % json.dumps(team.__json__()), 200


@app.route('/delete_team', methods=['DELETE'])
def delete_team():
    """删除队伍,解散队伍的同时，必须同时更改Course中所有对应学生的student_id和team_id"""
    team_id = request.values.get('team_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    if team is None:
        return "Cannot find such a team", 400
    else:
        # 找到这个team所对应的course
        course = Course.query.filter(team.course_id == Course.course_id).first()
        if course is None:
            return 'Cannot find a corresponding course', 400
        team.delete_team(course)
        return "success", 200


@app.route('/modify_team', methods=['POST'])
def modify_team():
    team_id = request.values.get('team_id')
    team_members_id = request.values.get('team_members_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    if team is None:
        return "Cannot find such a team", 400
    else:
        team.team_members_id = team_members_id
        db.session.add(team)
        db.session.commit()
        return "success", 200


# Course部分

@app.route('/add_course', methods=['POST'])
def add_course():
    teacher_id = request.values.get('teacher_id')
    team_ids = request.values.get('team_ids')
    student_ids = request.values.get('student_ids')
    course_info = request.values.get('course_info')
    name = request.values.get('name')
    course_time = request.values.get('course_time')
    start_time = request.values.get('start_time')
    end_time = request.values.get('end_time')
    max_team = request.values.get('max_team')
    min_team = request.values.get('min_team')
    course = Course(teacher_id, course_info, name, course_time, start_time,
                    end_time, max_team, min_team, student_ids, team_ids)
    if Course.query.filter((course.teacher_id == Course.teacher_id)
                           & (name == Course.name) &
                           (course_time == Course.course_time)).first() is None:
        db.session.add(course)
        db.session.commit()
        return 'success', 200
    else:
        return 'Already have this class', 400


@app.route('/modify_course_info', methods=['POST'])
def modify_course_info():
    course_id = request.values.get('course_id')
    course_info = request.values.get('course_info')
    course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Don\'t have such a course', 400
    else:
        course.course_info = course_info
        db.session.add(course)
        db.session.commit()
        return '%s' % json.dumps(course.__json__()), 200


@app.route('/get_course', methods=['GET'])
def get_course():
    course_id = request.values.get('course_id')
    if course_id is None:
        name = request.values.get('name')
        course_time = request.values.get('course_time')
        if name is None or course_time is None:
            return 'Don\'t  have enough information', 400
        else:
            course = Course.query.filter((name == Course.name) & (course_time == Course.course_time)).first()
    else:
        course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Cannot find this course', 400
    else:
        return '%s' % json.dumps(course.__json__()), 200


@app.route('/delete_course', methods=['POST'])
def delete_course():
    course_id = request.values.get('course_id')
    course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Cannot find this course', 400
    else:
        #删除所有队伍
        team_ids = course.get_team_ids()
        for team_id in team_ids:
            team = Team.query.filter(team_id == Team.team_id).first()
            db.session.delete(team)
        student_ids_dict = json.load(course.student_ids)
        # 对于所有参加了这门课的学生，在其attended_course_ids中修改
        for user_id in student_ids_dict:
            user = User.query.filter(user_id == User.user_id).first()
            attended_course_ids = user.get_course_ids()
            attended_course_ids = attended_course_ids.remove(course_id)
            user.attended_course_ids = ''.join(attended_course_ids)
            db.session.add(user)
        db.session.delete(course)
        db.session.commit()
        return 'success', 200


@app.route('/course_modify_student', methods=['POST'])
def course_modify_student():
    """对于课程增删学生"""
    course_id = request.values.get('course_id')
    student_ids = request.values.get('student_ids')
    course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Cannot find such a course', 400
    else:
        course.student_ids = student_ids
        db.session.add(course)
        db.session.commit()
        return 'success', 200


if __name__ == '__main__':
    db.app = app
    db.init_app(app)
    db.create_all()
    app.run(host='0.0.0.0', debug=True, port=8080)
