from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2

app = Flask(__name__, template_folder='.', static_folder='static')  # 設定模板和靜態檔案目錄

# 設定資料庫連線參數
DB_HOST = "140.117.68.66"
DB_NAME = "project_24"
DB_USER = "project_24"
DB_PASS = "x824kh"

def get_db_connection():
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
    return conn

# [登入頁]
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sales WHERE sAccount = %s AND spassword = %s", (account, password))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user:
            session['logged_in'] = True
            session['user_id'] = user[0]  # 假設 user[0] 是 users 表中的 id 欄位
            return redirect(url_for('home'))  # 登入成功後導向至首頁
        else:
            error = '帳號或密碼錯誤'
            return render_template('login.html', error=error)

    return render_template('login.html')

#[登出]
@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')

#[首頁]
@app.route('/')
def home():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # 若未登入，導向至登入頁面
    return render_template('home.html')

#[查詢票券]
@app.route('/search', methods=['GET', 'POST'])
def search():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # 若未登入，導向至登入頁面
    elif  request.method == 'POST':
        ticketNumber = request.form['ticketNumber']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"select * from voucher where vid='{ticketNumber}'")
        voucher = cur.fetchone()
        cur.close()
        conn.close()
        if voucher:
            return render_template('dataview.html')
        else:
            error = f'查無票券編號：{ticketNumber}' 
            return render_template('search.html', error=error)
    else:
        return render_template('search.html')
        

if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # 設定 session 密鑰
    app.run(debug=True)