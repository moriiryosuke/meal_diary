#ファイル自体の削除
import os
from app import app

db_file_path = './instance/test.db'  # SQLiteデータベースファイルのパス

# データベースファイルが存在する場合、削除する
if os.path.exists(db_file_path):
    os.remove(db_file_path)
    print(f'{db_file_path} を削除しました。')
else:
    print(f'{db_file_path} は存在しません。')
