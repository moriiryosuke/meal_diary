# データベースを変更したときに一度動かす
from test import app
from test import db
# from test import Post
with app.app_context():
    #データベースのテ－ブル削除
    db.drop_all()
    db.create_all()
    # db.drop_all(bind=Post.metadata)

#マイグレーションでおかしくなったとき
# test.db、migrationsフォルダを削除してdb.py動かして、下の3つやる
# flask db init    # マイグレーションのリポジトリ初期化(git initみたいなもん)

# set FLASK_APP=test.py
# flask db migrate # マイグレーション用のスクリプトを生成(migrations/versions/配下のxxx_.py)
# flask db upgrade # データベースへ書き込み
