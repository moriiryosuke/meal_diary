# conda install flask-login

# from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask import Flask, request, redirect, render_template, flash
from werkzeug.utils import secure_filename
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import pandas as pd

from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import generate_password_hash, check_password_hash
# import os

#migrate
from flask_migrate import Migrate

#csvファイルから分類するご飯のデータを読み込み
meal_df = pd.read_csv("../csv/meal.csv")
meal_list = meal_df["分類するご飯名"]
classes = meal_df.iloc[:,0].tolist()

image_size = 150

UPLOAD_FOLDER = "static/image"
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

#もらったファイルが上で定義した拡張子を持っているか判定する関数
def allowed_file(filename):
    return "." in filename and filename.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS

model = load_model("../model/75_num013_model.h5")

app = Flask(__name__)
# どのデータベースに接続するか指定
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# シークレットキーの設定urandom(24)は24バイトのランダムな列
# セッション情報の保存と改ざん防止（クッキーも）
app.config["SECRET_KEY"] = os.urandom(24)
# FlaskアプリケーションとSQLAlchemyのインスタンスを結びつける
db = SQLAlchemy(app)
#マイグレーションセットアップ
migrate = Migrate(app, db)
#便利なの定義
login_manager = LoginManager()
#ログイン周りの初期化
login_manager.init_app(app)

# UserMixin:Mixinクラスは便利なメソッド（is_authenticated、is_active、get_idなど）を提供
# これを使うことで、Flask-Loginでユーザーの認証状態を簡単に管理
#ログインに関するデータベース
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))

# Flask-LoginがユーザーIDを使って、データベースからユーザー情報をロードする方法を指定
# 各リクエストで呼ばれてユーザー確認される
#user_idは（ユーザーとサーバー間での一連のやり取りを一時的に保持）してあるセッションから持ってくる
@login_manager.user_loader
def load_user(user_id):
    #user_idのカラムすべてを返す
    return User.query.get(int(user_id))

#db.modelを継承したクラス、SQLAlchemyのORMを利用できる
#db.modelを継承することで、SQLAlchemyにデータベースモデルとして認識させる
#投稿に関するデータベース
class Post(db.Model):
    #カラムを指定してるだけ、文字数や型など
    id = db.Column(db.Integer, primary_key=True)
    comment = db.Column(db.String(20), nullable=False)
    pred = db.Column(db.String(140), nullable=False)
    file_path = db.Column(db.String(100), nullable=False)
    test = db.Column(db.String(100), nullable=True)

#ホーム画面
@app.route('/')
def index():
    #リスト形式で全Postから取得
    #リストの中身がpostクラスのオブジェクトみたいな感じ
    posts = Post.query.all()
    print(posts)
    return render_template('index.html',posts = posts)

#新規投稿画面
@app.route("/new",methods = ["GET","POST"])
def create():
    if request.method == "POST":
        #request.filesは辞書型でファイルが格納される
        #fileが送られると、"file"というkeyができる
        #"file"というkeyが#request.filesにあるかの確認
        if "file" not in request.files:
            flash("ファイルがありません")
            return redirect(request.url)
        #ファイル名が無し、つまりファイルが送られていない場合
        file = request.files["file"]
        if file.filename == "":
            flash("ファイルがありません")
            return redirect(request.url)
        
        #ファイルがあるかつ指定した拡張子
        if file and allowed_file(file.filename):
            #secure_filename('../../../../home/username/.bashrc')
            #>>> 'home_username_.bashrc'（変なとこ飛ばんようにしてる）
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            print(filepath)

            #画像の読み込みと変換
            img = image.load_img(filepath,target_size=(image_size,image_size))
            img = image.img_to_array(img)
            #ピクセル値255を0から1に変換
            img = img / 255.0
            #次元追加！[[]]
            data = np.array([img])
            print(model.predict(data))
            result = model.predict(data)[0]
            print(result)
            predicted = result.argmax()
            print(predicted)
            pred_answer = "これは" + classes[predicted] + "です"

            # return render_template("index.html", answer = pred_answer, imagefile=filepath)

# ここからdb
        #POSTメソッド時の処理
        comment1 = request.form.get("comment")

        test = request.form.get("test")

        pred1 = pred_answer
        # file_path = "file_path"
        file_path = filepath
        # post = Post(comment=comment1, pred=pred1)
        post = Post(comment=comment1, pred=pred1, file_path=file_path, test=test)
        #DBに値を送り保存する
        db.session.add(post)
        db.session.commit()
        # ~ここまでdb
        return redirect("/")
    else:
        #GETメソッド時
        return render_template("testnew.html")

#編集画面
@app.route("/<int:id>/edit", methods = ["GET","POST"])
def update(id):
    post = Post.query.get(id)
    if request.method =="GET":
        return render_template("edit.html",post=post)
    else:
        post.comment = request.form.get("comment")
        post.pred = request.form.get("pred")

        post.test = request.form.get("test")

        db.session.commit()
        return redirect("/")

#削除
@app.route("/<int:id>/delete", methods = ["GET"])
def delete(id):
    #このpostは配列ではなく、postクラスのオブジェクト
    post = Post.query.get(id)
    #投稿を削除
    db.session.delete(post)
    #削除を反映
    db.session.commit()
    return redirect('/')

#サインアップ（新規登録）
@app.route("/signup" , methods = ["GET","POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        #userのインスタンスを作成
        user = User(username=username,password=generate_password_hash(password, method="pbkdf2:sha256"))
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
    #ログインまだ作ってない
    else:
        return render_template("signup.html")

#ログイン
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # 一致するユーザー取得
        user = User.query.filter_by(username=username).first()
        if check_password_hash(user.password, password):
            login_user(user)
            # 本画面へ
            return redirect("/")        
    else:
        return render_template("login.html")


if __name__ == '__main__':
    app.run(debug=True)

