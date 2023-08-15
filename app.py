import subprocess
import datetime

import config

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields

app = Flask(__name__)
app.config.from_object(config)
db = SQLAlchemy(app)
api = Api(app, version='1.0', title='Video Clipping API', description='API for video clipping', doc='/swagger')


# 剪辑信息
class Clip(db.Model):
    __tablename__ = "clip"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    video_url = db.Column(db.String(300), nullable=False)
    clipped_url = db.Column(db.String(300), nullable=False)
    start_time = db.Column(db.String(100), nullable=False)
    end_time = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)


# 用户信息
class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(300), nullable=False)
    password = db.Column(db.String(300), nullable=False)
    # 普通用户1 会员2
    role = db.Column(db.Integer, nullable=False)


@api.route('/clip', endpoint='clip')
class ClipResource(Resource):
    # 添加文档注释
    @api.doc(description='Clip a video')
    # 定义输入模型
    @api.expect(api.model('Clip', {
        'video_url': fields.String(required=True),
        'start_time': fields.String(required=True),
        'end_time': fields.String(required=True),
        'user_id': fields.String(required=True)
    }))
    def post(self):
        try:
            # 获取请求信息
            video_url = request.json.get('video_url')
            start_time = request.json.get('start_time')
            end_time = request.json.get('end_time')
            user_id = request.json.get('user_id')
            now_time = datetime.datetime.now().microsecond
            user = User.query.get(user_id)

            # 普通用户user.role=0，会员用户user.role=1
            if user.role != 1:
                return jsonify({'error': '该用户权限不足，无法进行剪辑操作，请开通会员'})

            # 剪辑后视频存放位置
            output_filename = f'{now_time}.mp4'
            output_filepath = f'd:/temp/{output_filename}'

            # 生成ffmpeg命令
            ffmpeg_cmd = [
                'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
                '-i', video_url,
                '-ss', start_time,
                '-to', end_time,
                '-vcodec', 'copy',
                '-acodec', 'copy',
                output_filepath
            ]

            # 调用ffmpeg
            subprocess.run(ffmpeg_cmd, capture_output=True, text=True, check=True)

            # 生成下载链接（此处为本地链接）
            clipped_url = f'file://127.0.0.1/d$/temp/{output_filename}'

            clip = Clip(video_url=video_url, clipped_url=clipped_url, start_time=start_time, end_time=end_time,
                        user_id=user_id)
            db.session.add(clip)
            db.session.commit()

            return jsonify({'clipped_url': clipped_url})
        except subprocess.CalledProcessError as e:
            return jsonify({'error': e.stderr})
        except Exception as e:
            return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run()
