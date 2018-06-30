# -*- coding: utf-8 -*
from flask_sqlalchemy import SQLAlchemy
import json
import base64
from Crypto.Cipher import AES
import os
import requests
import binascii

db = SQLAlchemy()


class User(db.Model):
    """用户表"""
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    is_teacher = db.Column(db.Boolean, nullable=False)
    # 存 dict 形如 id1@id2
    attended_course_ids = db.Column(db.Text, nullable=False)
    username = db.Column(db.String(20), nullable=False)
    profile_photo = db.Column(db.Text)

    def __init__(self, student_id, name, is_teacher, profile_photo, attended_course_ids):
        self.student_id = student_id
        self.username = name
        self.is_teacher = is_teacher
        self.profile_photo = profile_photo
        self.attended_course_ids = attended_course_ids

    def add_user(self):
        """如果成功，那么就返回success，如果失败，返回失败原因"""
        if User.query.filter(self.student_id == User.student_id).first() is None:
            db.session.add(self)
            db.session.commit()
            return '%s' % json.dumps(self.__json__()), 200
        else:
            return 'Already have this student_id', 400

    def get_course_ids(self):
        """以list的形式返回team_members_id"""
        return self.attended_course_ids.split('@')

    def __json__(self):
        info = {
            "user_id": self.user_id,
            "student_id": self.student_id,
            "username": self.username,
            "is_teacher": self.is_teacher,
            "profile_photo": str(self.profile_photo),
            "attended_course_ids": str(self.attended_course_ids)
        }
        return info


class Team(db.Model):
    """队伍表"""
    __tablename__ = 'teams'
    team_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_id = db.Column(db.Integer)
    # 学号
    leader_id = db.Column(db.Integer, nullable=False)
    team_info = db.Column(db.String(100), nullable=False)
    # list
    team_members_id = db.Column(db.Text, nullable=False)
    max_team = db.Column(db.Integer, nullable=False)
    available_team = db.Column(db.Integer, nullable=False)

    def __init__(self, course_id, leader_id, team_info, max_team,
                 available_team, team_members_id):
        self.course_id = course_id
        self.leader_id = leader_id
        self.team_info = team_info
        self.max_team = max_team
        self.available_team = available_team
        self.team_members_id = team_members_id

    def __json__(self):
        """以JSON的形式返回当前用户的数据"""
        info = {
            "team_id": self.team_id,
            "course_id": self.course_id,
            "leader_id": self.leader_id,
            "team_info": self.team_info,
            "team_members_id": self.team_members_id,
            "max_team": self.max_team,
            "available_team": self.available_team
        }
        return info

    def get_members_id(self):
        """以list的形式返回team_members_id"""
        return str(self.team_members_id).split('@')

    def delete_team(self, course):
        """删除指定的队伍"""
        # 得到student_ids
        student_ids_dict = eval(course.student_ids)
        team_member = self.get_members_id()
        # 将组内每个成员的组队信息更改
        for member in team_member:
            student_ids_dict[member] = 0
        # 将course的team_ids进行更改
        new_team_ids = course.get_team_ids()
        new_team_ids.remove(str(self.team_id))
        if new_team_ids is None:
            new_team_ids = 'None'
        else:
            new_team_ids = '@'.join(new_team_ids)
        course.team_ids = new_team_ids
        course.student_ids = json.dumps(student_ids_dict)
        # 更新数据库
        db.session.delete(self)
        db.session.add(course)
        db.session.commit()


class Course(db.Model):
    """课程表"""
    __tablename__ = 'course'
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_id = db.Column(db.Integer)
    team_ids = db.Column(db.Text, nullable=False)
    student_ids = db.Column(db.Text, nullable=False)
    course_info = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course_time = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(100), nullable=False)
    end_time = db.Column(db.String(100), nullable=False)
    max_team = db.Column(db.Integer, nullable=False)
    min_team = db.Column(db.Integer, nullable=False)

    def __init__(self, teacher_id, course_info, name, course_time, start_time,
                 end_time, max_team, min_team, student_ids, team_ids):
        self.teacher_id = teacher_id
        self.course_info = course_info
        self.name = name
        self.course_time = course_time
        self.start_time = start_time
        self.end_time = end_time
        self.max_team = max_team
        self.min_team = min_team
        self.team_ids = team_ids
        self.student_ids = student_ids

    def __json__(self):
        """以json的格式返回课程信息"""
        info = {
            "course_id": self.course_id,
            "teacher_id": self.teacher_id,
            "team_ids": self.team_ids,
            "course_info": self.course_info,
            "name": self.name,
            "course_time": self.course_time,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "max_team": self.max_team,
            "min_team": self.min_team,
            "student_ids" : self.student_ids
        }
        return info

    def get_team_ids(self):
        """以list的形式返回team_ids"""
        return str(self.team_ids).split('@')


class ThirdSessionKey(db.Model):
    """third session key"""
    __tablename__ = 'thirdsessionkeys'
    third_session_key_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    third_session_key = db.Column(db.String(50), nullable=False)
    session_key = db.Column(db.String(50), nullable=False)
    openid = db.Column(db.String(50), nullable=False)

    def __init__(self, third_session_key=None, session_key=None, openid=None):
        self.appid = 'wx3b06cde5635b391d'
        self.secret = '559c9a13441e8e2a8e970860a37170f8'
        #self.appid = 'wx4f4bc4dec97d474b'
        #self.session_key = 'tiihtNczf5v6AKRyjwEUhQ=='
        self.third_session_key = third_session_key
        self.session_key = session_key
        self.openid = openid

    # decrypt encrypted_data and add third_session_key to it
    def get_third_session_key(self, js_code):
        session_key_and_openid = self.jscode2session(js_code)
        self.session_key = session_key_and_openid.get('session_key')
        self.openid = session_key_and_openid.get('openid')
        
        if self.session_key is None:
            return 'Error: session_key is None', 400

        # 生成长度为32位的hex字符串，用于第三方session的key
        self.third_session_key = binascii.hexlify(os.urandom(16)).decode()
        # store third_session_key, session_key, openid
        thirdsessionkey = ThirdSessionKey(self.third_session_key, self.session_key, self.openid)
        temp = ThirdSessionKey.query.filter(thirdsessionkey.openid == ThirdSessionKey.openid).first()
        if temp is None:
            db.session.add(thirdsessionkey)
            db.session.commit()
        else:
            temp.third_session_key = thirdsessionkey.third_session_key
            temp.session_key = thirdsessionkey.session_key
            db.session.commit()

        return self.third_session_key
        
    def login(self, third_session_key):
        temp = ThirdSessionKey.query.filter(third_session_key == ThirdSessionKey.third_session_key).first()
        if temp is None:
            return False
        else:
            return True

    def decrypt_data(self, third_session_key, encryptedData, iv):
        temp = ThirdSessionKey.query.filter(third_session_key == ThirdSessionKey.third_session_key).first()
        if temp is None:
            return False
        else:
            self.session_key = temp.session_key
        # base64 decode
        session_key = base64.b64decode(self.session_key)
        encrypted_data = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(session_key, AES.MODE_CBC, iv)

        decrypted_data = self._unpad(cipher.decrypt(encrypted_data))
        decrypted = json.loads(decrypted_data.decode('utf-8', 'ignore'))

        if decrypted['watermark']['appid'] != self.appid:
            raise Exception('Invalid Buffer')
        
        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s)-1:])]

    # get json(dict): {openid, session_key}
    def jscode2session(self, js_code):
        url = ('https://api.weixin.qq.com/sns/jscode2session?appid={}&secret={}&js_code={}&grant_type=authorization_code'
               ).format(self.appid, self.secret, js_code)
        r = requests.get(url)
        return r.json()
