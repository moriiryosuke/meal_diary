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

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
# import os

#migrate
from flask_migrate import Migrate

#csvファイルから分類するご飯のデータを読み込み
meal_df = pd.read_csv("../csv/meal.csv")

nut_gol_df = pd.read_csv("../csv/nut_gol.csv",index_col=0)
nut_gol_columns = nut_gol_df.columns.values

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

#ログインしていないとき飛ぶ先
login_manager.login_view = '/login'

#ログインメッセージ
#たぶん初期にplese loginみたいなメッセージが入ってる
login_manager.login_message = ''

# UserMixin:Mixinクラスは便利なメソッド（is_authenticated、is_active、get_idなど）を提供
# これを使うことで、Flask-Loginでユーザーの認証状態を簡単に管理
#ログインに関するデータベース
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(25))
    age = db.Column(db.Integer, nullable=False)
    sex = db.Column(db.String, nullable=False)
    movetype = db.Column(db.String, nullable=False)
    kcal = db.Column(db.Integer, nullable=False)
    protein = db.Column(db.Integer, nullable=False)
    fat = db.Column(db.Integer, nullable=False)
    carbs = db.Column(db.Integer, nullable=False)
    vege = db.Column(db.Integer, nullable=False)

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
    comment = db.Column(db.String(20), nullable=True)
    pred = db.Column(db.String(140), nullable=False)
    file_path = db.Column(db.String(100), nullable=False)
    userid = db.Column(db.String(50),db.ForeignKey('user.id'), nullable=False)
    kcal = db.Column(db.Integer, nullable=True)
    protein = db.Column(db.Integer, nullable=True)
    fat = db.Column(db.Integer, nullable=True)
    carbs = db.Column(db.Integer, nullable=True)
    salt = db.Column(db.Integer, nullable=True)
    vege = db.Column(db.Integer, nullable=True)
    gram = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.String, nullable=False)
    meal_time = db.Column(db.String, nullable=True)

#栄養素のデータベース
class Nutrients(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    meal = db.Column(db.String(25), nullable=False)
    kcal = db.Column(db.Integer, nullable=True)
    protein = db.Column(db.Integer, nullable=True)
    fat = db.Column(db.Integer, nullable=True)
    carbs = db.Column(db.Integer, nullable=True)
    salt = db.Column(db.Integer, nullable=True)
    vege = db.Column(db.Integer, nullable=True)
    gram = db.Column(db.Integer, nullable=True)
    

# nutl_df = pd.read_csv("../csv/meal_nut.csv",index_col=0)
# nutl_colum = nutl_df.columns.values

# for meal in classes:
#     meal = meal
#     kcal = nutl_df.loc[meal,nutl_colum[0]]
#     protein = nutl_df.loc[meal,nutl_colum[1]]
#     fat = nutl_df.loc[meal,nutl_colum[2]]
#     carbs = nutl_df.loc[meal,nutl_colum[3]]
#     salt = nutl_df.loc[meal,nutl_colum[4]]
#     vege = nutl_df.loc[meal,nutl_colum[5]]
#     post = Nutrients(meal=meal,kcal=kcal,protein=protein,fat=fat,carbs=carbs,salt=salt,vege=vege)
#     db.session.add(post)
#     db.session.commit()

today_nutl = {"kcal":0,"protein":0,"fat":0,"carbs":0,"vege":0}

#投稿表示画面
@app.route('/')
@login_required
def index():
    today_nutl["kcal"] = 0
    today_nutl["protein"] = 0
    today_nutl["fat"] = 0
    today_nutl["carbs"] = 0
    today_nutl["vege"] = 0
    #リスト形式で全Postから取得
    #リストの中身がpostクラスのオブジェクトみたいな感じ
    # posts = Post.query.all()
    #現在のユーザー取得
    login_id = current_user.id
    #投稿を取得
    posts = Post.query.filter(Post.userid == login_id)
    #目標栄養素（ユーザーを取得）
    users = User.query.filter(User.id == login_id)
    # print(f"今日の摂取カロリーは{today_nutl["kcal"]}")
    meal_list=[0]*15
        
    #一番上
    meal_list[0] = Post.query.filter_by(userid=login_id).order_by(Post.id.desc()).first()
    #2つ目
    meal_list[1] = Post.query.filter_by(userid=login_id).order_by(Post.id.desc()).offset(1).first()
    # if meal_list[0] and not meal_list[1]:
    #     today_nutl["kcal"] = meal_list[0]       
    num = 0
    flug = 0
    #2個ある場合
    if meal_list[0] and meal_list[1]:
        while flug == 0:
            if meal_list[num].created_at[:10] != meal_list[num+1].created_at[:10]:
                flug = 1
                num -= 1
            else:
                meal_list[num+2] = Post.query.filter_by(userid=login_id).order_by(Post.id.desc()).offset(num+2).first()
            if not meal_list[num+2]:
                flug = 1
            num += 1
    
    if meal_list[0]:
        for j in range(num+1):
            today_nutl["kcal"] += meal_list[j].kcal
            today_nutl["protein"] += meal_list[j].protein
            today_nutl["fat"] += meal_list[j].fat
            today_nutl["carbs"] += meal_list[j].carbs
            today_nutl["vege"] += meal_list[j].vege
            print(j)
        print("カロリー合計")
        print(today_nutl["kcal"])

    return render_template('index.html',posts = posts,users = users,nutl=today_nutl)

#新規投稿画面
@app.route("/new",methods = ["GET","POST"])
@login_required
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
            pred_answer = classes[predicted]

            # return render_template("index.html", answer = pred_answer, imagefile=filepath)

# ここからdb
        #POSTメソッド時の処理
        # ユーザー名と紐付け
        userid = current_user.id
        # コメント
        comment1 = request.form.get("comment")
        gram = request.form.get("gram")
        # if not gram:
        #     gram = 100
        # else:
        #     gram = int(gram)
        #いつのご飯か
        meal_time = request.form.get("meal_time")
        #予測結果
        pred1 = pred_answer
        # file_path = "file_path"
        file_path = filepath
        #栄養素
        nutrientsnt = Nutrients.query.filter_by(meal=pred1).first()

        if not gram:
            gram = nutrientsnt.gram
            gram = int(gram)
        else:
            gram = int(gram)

        now = datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M")

        # kcal = int.from_bytes(nutrientsnt.kcal,'little')

        post = Post(comment=comment1, pred=pred1, file_path=file_path, gram=gram, userid=userid,
                    kcal=round(nutrientsnt.kcal*gram/100,2),protein=round(nutrientsnt.protein*gram/100,2),
                    fat=round(nutrientsnt.fat*gram/100,2),carbs=round(nutrientsnt.carbs*gram/100,2),
                    salt=round(nutrientsnt.salt*gram/100,2),vege=round(nutrientsnt.vege*gram/100,2),
                    created_at=formatted_time, meal_time=meal_time)
        #DBに値を送り保存する
        db.session.add(post)
        db.session.commit()

        # user = User.query.get(userid)
        # meal1 = Post.query.filter_by(userid=userid).order_by(Post.id.desc()).first()
        # meal2 = Post.query.filter_by(userid=userid).order_by(Post.id.desc()).offset(1).first()
        # if meal1:
        #     flug,add_kcal = calc(user,meal1,meal2)
        # if flug == 0:
        #     today_nutl["kcal"] += add_kcal
        # else:
        #     today_nutl["kcal"] = add_kcal
        # meal_list=[0]*15
         
        # #一番上
        # meal_list[0] = Post.query.filter_by(userid=userid).order_by(Post.id.desc()).first()
        # #2つ目
        # meal_list[1] = Post.query.filter_by(userid=userid).order_by(Post.id.desc()).offset(1).first()
        # # if meal_list[0] and not meal_list[1]:
        # #     today_nutl["kcal"] = meal_list[0]       
        # num = 0
        # flug = 0
        # #2個ある場合
        # if meal_list[0] and meal_list[1]:
        #     while flug == 0:
        #         if meal_list[num].created_at[:10] != meal_list[num+1].created_at[:10]:
        #             flug = 1
        #         meal_list[num+2] = Post.query.filter_by(userid=userid).order_by(Post.id.desc()).offset(num+2).first()
        #         if not meal_list[num+2]:
        #             flug = 1
        #         num += 1
        
        # if meal_list[0]:
        #     for j in range(num):
        #         today_nutl["kcal"] += meal_list[j].kcal
        #     print("カロリー合計")
        #     print(today_nutl["kcal"])

        # ~ここまでdb
        return redirect("/")
    else:
        #GETメソッド時
        return render_template("testnew.html")

#編集画面
@app.route("/<int:id>/edit", methods = ["GET","POST"])
@login_required
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
@login_required
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
        #HTMLからデータ受け取り
        username = request.form.get("username")
        password = request.form.get("password")
        age = request.form.get("age")
        sex = request.form.get("sex")
        movetype = request.form.get("movetype")
        #もらったままだと文字列！！
        age_int = int(age)
        #userのインスタンスを作成
        #年齢判定
        if age_int <=29:
            AGE = "18-29"
        elif 30 <= age_int <=49:
            AGE = "30-49"
        elif 50 <= age_int <=64:
            AGE = "50-64"
        elif 65 <= age_int <=74:
            AGE = "65-74"
        else:
            AGE = "75"
        #男女判定
        if sex == "男":
            SEX = "0"
        else:
            SEX = "1"
        #分類
        CLASS = f"{AGE}-{movetype}-{SEX}" 
        kcal = round(nut_gol_df.loc[CLASS,nut_gol_columns[0]],2)
        protein = round(nut_gol_df.loc[CLASS,nut_gol_columns[1]],2)
        fat = round(nut_gol_df.loc[CLASS,nut_gol_columns[2]],2)
        carbs = round(nut_gol_df.loc[CLASS,nut_gol_columns[3]],2)
        vege = round(nut_gol_df.loc[CLASS,nut_gol_columns[4]],2)

        print(kcal,protein,fat,carbs,vege)

        user = User(username=username,age=age,sex=sex,movetype=movetype,kcal=kcal,protein=protein,
                    fat=fat,carbs=carbs,vege=vege,
                    password=generate_password_hash(password, method="pbkdf2:sha256"))
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
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
        # 例外処理
        if username and password:
            if user:
                if check_password_hash(user.password, password):
                    login_user(user)
                    # 本画面へ
                    return redirect("/") 
                else:
                    flash("ユーザー名とパスワードが一致しません")
                    return redirect(request.url)
            else:
                flash("入力したユーザー名は存在しません")
                return redirect(request.url) 
        else:
            flash("未入力の項目があります")
            return redirect(request.url)      
    else:
        return render_template("login.html")

#ログアウト
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("ログアウトしました")
    return redirect("/login")

if __name__ == '__main__':
    app.run(debug=True)

