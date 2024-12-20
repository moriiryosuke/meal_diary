# conda install flask-login
# from flask import Flask,render_template,request,redirect
from test import Nutrients

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

nutl_df = pd.read_csv("../csv/meal_nut.csv",index_col=0)
# nutl_list = meal_df["分類するご飯名"]

nutl_colum = nutl_df.columns.values
# classes = meal_df.iloc[:,0].tolist()
# print(nutl_df)
print(nutl_colum)

print(nutl_df.loc["まぜそば","カロリー"])

for meal in classes:
    meal = meal
    kcal = nutl_df.loc[meal,nutl_colum[0]]
    protein = nutl_df.loc[meal,nutl_colum[1]]
    fat = nutl_df.loc[meal,nutl_colum[2]]
    carbs = nutl_df.loc[meal,nutl_colum[3]]
    salt = nutl_df.loc[meal,nutl_colum[4]]
    vege = nutl_df.loc[meal,nutl_colum[5]]
    gram = vege = nutl_df.loc[meal,nutl_colum[6]]
    with app.app_context():
        post = Nutrients(meal=meal,kcal=kcal,protein=protein,fat=fat,carbs=carbs,salt=salt,vege=vege)
        db.session.add(post)
        db.session.commit()

# for meal in classes:
#     meal = meal
#     kcal = nutl_df.loc[meal,nutl_colum[0]]
#     print(kcal)
#     with app.app_context():
#         post = Nutrients(meal=meal,kcal=kcal)
#         db.session.add(post)
#         db.session.commit()



# with app.app_context():
#     post = Nutrients(meal = "test")
#     #DBに値を送り保存する
#     db.session.add(post)
#     db.session.commit()