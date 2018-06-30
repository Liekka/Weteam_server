# coding:utf-8
from flask import Flask, request
from models import *
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../Database/Weteam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# User部分


@app.route('/add_user', methods=['POST'])
def add_user():
    """使用于Post方法，用于向数据库中增加用户"""
    # 首先取出需要的参数
    student_id = request.values.get('student_id')
    username = request.values.get('username')
    attended_course_ids = request.values.get('attended_course_ids')
    profile_photo = request.values.get('profile_photo')

    # 需要判断是否是学生
    if request.values.get('is_teacher') == '0':
        is_teacher = 0
    elif request.values.get('is_teacher') == '1':
        is_teacher = 1
    else:
        error = "is_teacher is neither 0 or 1", 400
        return error
    # 增加新的用户
    u = User(student_id, username, is_teacher, profile_photo, attended_course_ids)
    error = u.add_user()
    return error


@app.route('/get_user', methods=['GET'])
def get_user():
    """根据学工号返回用户的信息"""
    # 从url中取出所需参数
    student_id = request.values.get('student_id')
    u = User.query.filter(User.student_id == student_id).first()
    # 判断是否存在该用户，并返回response
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
    # 从url中取出所需参数
    student_id = request.values.get('student_id')
    attended_course_ids = request.values.get('attended_course_ids')
    u = User.query.filter(User.student_id == student_id).first()
    # 判断是否存在该用户，并返回response
    if u is None:
        return "Cannot find such a student", 400
    else:
        u.attended_course_ids = attended_course_ids
        db.session.add(u)
        db.session.commit()
        return "%s" % json.dumps(u.__json__()), 200

# Team部分


@app.route('/add_team', methods=['POST'])
def add_team():
    """向数据库中增加队伍"""
    # 从url中取出所需参数
    course_id = int(request.values.get('course_id'))
    leader_id = request.values.get('leader_id')
    team_info = request.values.get('team_info')
    max_team = request.values.get('max_team')
    available_team = request.values.get('available_team')
    team_members_id = request.values.get('team_members_id')
    # 只有存在对应的course_id才能创建对应的队伍
    if Course.query.filter(course_id == Course.course_id).first() is None:
        return 'Don\'t have such a course'

    team = Team(course_id, leader_id, team_info, max_team, available_team, team_members_id)
    # 确定这门课中，该队长没有创建过其他课程
    if Team.query.filter((team.course_id == Team.course_id) &
                         (team.leader_id == Team.leader_id)).first() is None:
        db.session.add(team)
        db.session.commit()
        return "%s" % json.dumps(team.__json__()), 200
    else:
        return "Already have a team with this leader", 400


@app.route('/get_team', methods=['GET'])
def get_team():
    """获取队伍信息"""
    # 从url中取出所需参数
    team_id = request.values.get('team_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    # 确定存在这门课程
    if team is None:
        return "Cannot find such a team", 400
    else:
        return "%s" % json.dumps(team.__json__()), 200


@app.route('/delete_team', methods=['POST'])
def delete_team():
    """删除队伍,解散队伍的同时，必须同时更改Course中所有对应学生的student_id和team_id"""
    # 从url中取出所需参数
    team_id = request.values.get('team_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    # 如果不存在这门课程，则返回报错
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
    """增删队伍中的成员或修改队长人选"""
    # 从url中取出所需参数
    team_id = request.values.get('team_id')
    leader_id = request.values.get('leader_id')
    team_members_id = request.values.get('team_members_id')
    team = Team.query.filter(team_id == Team.team_id).first()
    # 如果不存在这门课程，则返回报错
    if team is None:
        return "Cannot find such a team", 400
    else:
        # if need to change team leader
        if leader_id != 'None':
            team.leader_id = leader_id
        # 修改队伍成员列表
        team.team_members_id = team_members_id
        temp = team.get_members_id()
        # 如果队伍中的人都被删掉了，报错
        if temp is None:
            return "At least 1 member is required", 400
        team.available_team = team.max_team - len(temp)
        db.session.add(team)
        db.session.commit()
        return "%s" % json.dumps(team.__json__()), 200


# Course部分

@app.route('/add_course', methods=['POST'])
def add_course():
    """教师新建课程"""
    # 从url中取出所需参数
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
    # 确定该老师在同一课程时间段没有其他课程
    if Course.query.filter((course.teacher_id == Course.teacher_id)
                           & (name == Course.name) &
                           (course_time == Course.course_time)).first() is None:
        db.session.add(course)
        db.session.commit()
        return '%s' % json.dumps(course.__json__()), 200
    else:
        return 'Already have this class', 400


@app.route('/modify_course_info', methods=['POST'])
def modify_course_info():
    """修改课程信息功能"""
    # 从url中取出所需参数
    course_id = request.values.get('course_id')
    course_info = request.values.get('course_info')
    course = Course.query.filter(course_id == Course.course_id).first()
    # 确定是否存在该课程
    if course is None:
        return 'Don\'t have such a course', 400
    else:
        course.course_info = course_info
        db.session.add(course)
        db.session.commit()
        return '%s' % json.dumps(course.__json__()), 200


@app.route('/get_course', methods=['GET'])
def get_course():
    """根据课程id取得课程信息，或是进行模糊搜索"""
    # 从url中取出所需参数
    course_id = request.values.get('course_id')
    # 可以不通过课程id，而是通过课程名来取得课程信息
    if course_id is None:
        name = request.values.get('name')
        if name is None :
            return 'Don\'t have enough information', 400
        else:
            # 进行模糊搜索，匹配课程名并返回所有匹配的课程
            course = Course.query.filter((name == Course.name)).all()
            if course is not None:
                for i in range(len(course)):
                    teacher = User.query.filter(User.student_id == course[i].teacher_id).first()
                    if teacher is None:
                        return 'Don\'t have teacher : ' + str(course.teacher_id)
                    course[i] = course[i].__json__()
                    course[i]['teacher_name'] = teacher.username
                return '%s' % json.dumps(course), 200
    else:
        course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Cannot find this course', 400
    else:
        return '%s' % json.dumps(course.__json__()), 200


@app.route('/delete_course', methods=['POST'])
def delete_course():
    """根据课程id删除课程功能"""
    # 从url中取出所需参数
    course_id = request.values.get('course_id')
    course = Course.query.filter(course_id == Course.course_id).first()
    if course is None:
        return 'Cannot find this course', 400
    else:
        #删除所有队伍
        if course.team_ids != 'None':
            team_ids = course.get_team_ids()
            for team_id in team_ids:
                team = Team.query.filter(team_id == Team.team_id).first()
                if team is not None:
                    db.session.delete(team)
                else:
                    return 'Cannot find team: %d' % team_id, 400

        # 对于所有参加了这门课的学生，在其attended_course_ids中修改
        if course.student_ids != 'None':
            student_ids_dict = eval(course.student_ids)
            for user_id in student_ids_dict:
                user = User.query.filter(user_id == User.student_id).first()
                if user is None:
                    return 'Cannot find user : %d' % user_id, 400
                a = user.attended_course_ids
                a = a.split('@')
                a.remove(course_id)
                # 如果学生只参加了这门课程，那么他的参加课程列表字段就要被赋值为None
                if a is None:
                    user.attended_course_ids = 'None'
                else:
                    user.attended_course_ids = '@'.join(a)
                db.session.add(user)

        db.session.delete(course)
        db.session.commit()
        return 'success', 200


@app.route('/course_modify_student', methods=['POST'])
def course_modify_student():
    """对于课程增删学生"""
    # 从url中取出所需参数
    course_id = request.values.get('course_id')
    student_ids = request.values.get('student_ids')
    course = Course.query.filter(course_id == Course.course_id).first()
    # 确定存在该课程
    if course is None:
        return 'Cannot find such a course', 400
    else:
        course.student_ids = student_ids
        db.session.add(course)
        db.session.commit()
        return '%s' % json.dumps(course.__json__()), 200


@app.route('/modify_team_ids', methods=['POST'])
def modify_team_ids():
    """更改课程中的队伍列表"""
    # 从url中取出所需参数
    course_id = request.values.get('course_id')
    team_ids = request.values.get('team_ids')
    course = Course.query.filter(course_id == Course.course_id).first()
    # 确定存在该课程
    if course is None:
        return 'Cannot find such a course', 400
    else:
        course.team_ids = team_ids
        db.session.add(course)
        db.session.commit()
        return '%s' % json.dumps(course.__json__()), 200


# third session key
@app.route('/get_third_session_key', methods=['POST', 'GET'])
def get_third_session_key():
    code = request.values.get('code')
    # encryptedData = request.values.get('encryptedData')
    # iv = request.values.get('iv')
    third_session_key = ThirdSessionKey().get_third_session_key(js_code=code)
    if third_session_key:
        return third_session_key, 200
    else:
        return 'some error', 400


@app.route('/get_decrypted_data', methods=['POST', 'GET'])
def get_decrypted_data():
    third_session_key = request.values.get('third_session_key')
    encryptedData = request.values.get('encryptedData')
    iv = request.values.get('iv')
    decrypted = ThirdSessionKey().decrypt_data(third_session_key=third_session_key, encryptedData=encryptedData, iv=iv)
    if decrypted:
        return json.dumps(decrypted), 200
    else:
        return 'some error', 400


@app.route('/login', methods=['POST', 'GET'])
def login():
    third_session_key = request.values.get('third_session_key')
    return json.dumps(ThirdSessionKey(third_session_key=third_session_key).login(third_session_key=third_session_key)), 200


if __name__ == '__main__':
    db.app = app
    db.init_app(app)
    db.create_all()
    app.run(host='0.0.0.0', debug=True, port=8080)
