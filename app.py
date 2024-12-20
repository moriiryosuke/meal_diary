from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime



app = Flask(__name__)
# どのデータベースに接続するか指定
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test.db"
# FlaskアプリケーションとSQLAlchemyのインスタンスを結びつける
db = SQLAlchemy(app)

#dｂ.modelを継承したクラス、SQLAlchemyのORMを利用できる
#db.modelを継承することで、SQLAlchemyにデータベースモデルとして認識させる
class Post(db.Model):
    #カラムを指定してるだけ、文字数や型など
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    body = db.Column(db.String(140), nullable=False)
    test = db.Column(db.String(100), nullable=False)

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
        #POSTメソッド時の処理
        title1 = request.form.get("title")
        body1 = request.form.get("body")
        # test = "test"
        test = request.form.get("body")
        # post = Post(title=title1, body=body1)
        post = Post(title=title1, body=body1, test=test)
        #DBに値を送り保存する
        db.session.add(post)
        db.session.commit()
        return redirect("/")
    else:
        #GETメソッド時
        return render_template("new.html")

#編集画面
@app.route("/<int:id>/edit", methods = ["GET","POST"])
def update(id):
    post = Post.query.get(id)
    if request.method =="GET":
        return render_template("edit.html",post=post)
    else:
        post.title = request.form.get("title")
        post.body = request.form.get("body")
        db.session.commit()
        return redirect("/")

@app.route("/<int:id>/delete", methods = ["GET"])
def delete(id):
    #このpostは配列ではなく、postクラスのオブジェクト
    post = Post.query.get(id)
    #投稿を削除
    db.session.delete(post)
    #削除を反映
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

