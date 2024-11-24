from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://project_24:x824kh@140.117.68.66:5432/project_24'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定義模型
class Sales(db.Model):
    __tablename__ = 'sales'
    sId = db.Column('sid', db.Integer, primary_key=True)  # 映射到資料庫中的 sid 欄位
    sName = db.Column(db.String(50))
    sMail = db.Column(db.String(100), unique=True)
    sPasswordHash = db.Column(db.String(128))

    # 設定密碼
    def set_password(self, password):
        self.sPasswordHash = generate_password_hash(password)

    # 驗證密碼
    def check_password(self, password):
        return check_password_hash(self.sPasswordHash, password)


class Voucher(db.Model):
    __tablename__ = 'voucher'
    vId = db.Column(db.Integer, primary_key=True)
    vName = db.Column(db.String(100))
    amount = db.Column(db.Numeric)
    effectiveDate = db.Column(db.Date)
    expiryDate = db.Column(db.Date)
    quantity = db.Column(db.Integer)
    sId = db.Column(db.Integer, db.ForeignKey('sales.sId'))

# 初始化資料庫
@app.cli.command("initdb")
def initdb():
    """初始化資料庫"""
    db.create_all()
    print("Database created!")

# 建立業務登入 API
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    sales = Sales.query.filter_by(sMail=data['email']).first()
    if sales and sales.check_password(data['password']):
        return jsonify({"message": "Login successful", "sId": sales.sId})
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# 註冊新業務 (示例 API)
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    print(data)
    if Sales.query.filter_by(sMail=data['email']).first():
        return jsonify({"message": "Email already registered"}), 401
    new_user = Sales(sName=data['name'], sMail=data['email'])
    new_user.set_password(data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201


# 測試 API
if __name__ == '__main__':
    app.run(debug=True)


