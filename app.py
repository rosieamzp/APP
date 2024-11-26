from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, template_folder='.', static_folder='static')  # 設定模板和靜態檔案目錄

# 設定資料庫連線參數
DB_HOST = "140.117.68.66"
DB_NAME = "project_24"
DB_USER = "project_24"
DB_PASS = "x824kh"

#設定mail server參數
smtp_server = 'smtp.gmail.com'
smtp_port = 587  # TLS 端口
sender_email = 'weiru119@gmail.com'
sender_password = 'xtqc qrje ydfj rans'

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
            session['user_name'] = user[1]  # 假設 user[0] 是 users 表中的 id 欄位
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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"select status, count(status) from voucherissuance group by status ")
    voucher = cur.fetchall()
    print(voucher)
    cur.close()
    conn.close()
    return render_template('home.html',voucher =voucher)

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

        cur.execute(f"select saccount,sname from sales where sid = '{voucher[6]}'")
        salse = cur.fetchone()

        cur.close()
        conn.close()
        if voucher:
            return render_template('dataview.html',voucher=voucher,salse=salse)
        else:
            error = f'查無票券編號：{ticketNumber}' 
            return render_template('search.html', error=error)
    else:
        return render_template('search.html')
        
#[新增票券]
@app.route('/addvoucher', methods=['GET', 'POST'])
def addvoucher():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # 若未登入，導向至登入頁面
    elif  request.method == 'POST':
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"INSERT INTO voucher(vid, vname, amount, effectivedate, expirydate, quantity, sid, cname, channel)	VALUES ('{request.form['voucherSerial']}', '{request.form['voucherName']}', {request.form['amount']}, '{request.form['startDate']}', '{request.form['endDate']}', {request.form['quantity']}, {session.get('user_id')}, '{request.form['company']}', '{request.form['channels']}');")
        conn.commit()
        sql ="INSERT INTO public.voucherissuance(vid, viseq, status, channel) VALUES (%s, %s, %s, %s);"
        values = []
        quantity = int(request.form['quantity'])+1  # 將 quantity 轉換為整數
        for i in range(1,quantity):
            value = (
                request.form['voucherSerial'],  # vid
                f"{request.form['voucherSerial']}{i:04d}",  # viseq，從 1 開始遞增
                '未使用',  # status
                request.form['channels'],  # channel
            )
            values.append(value)
        cur.executemany(sql, values)
        conn.commit()
        cur.execute("SELECT cname FROM company")
        options  = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('addvoucher.html', exOver="t",options =options)
    else:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT cname FROM company")
        options  = cur.fetchall()
        cur.close()
        conn.close()
        return render_template('addvoucher.html',options =options )

#[查詢票券明細]
@app.route('/issueVouchers', methods=['GET', 'POST'])
def issueVouchers():
    if not session.get('logged_in'):
        return redirect(url_for('login'))  # 若未登入，導向至登入頁面
    elif  request.method == 'POST':
        mails = request.form.getlist('mails')
        voucherIds = request.form.getlist('voucherId[]')
        values = []
        sql = "update voucherissuance set status = '已發送',email=%s where viseq =%s"

        for index, element in enumerate(mails):
            if(element != 'none'):
                print(f"Element at index {index} is {element},{voucherIds[index]} ")
                message = MIMEMultipart()
                message['From'] = sender_email
                message['To'] = element
                message['Subject'] = f'發送票券：{voucherIds[index]}'

                # 加入純文字內容
                message.attach(MIMEText('發送票券',  voucherIds[index]))
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, element, message.as_string())
                values.append((element,voucherIds[index]))
        conn = get_db_connection()
        cur = conn.cursor()
        cur.executemany(sql, values)
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('issueVouchers', vid=request.args['vid'], count=len(values)))
    else:
        ticketNumber = request.args['vid']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f"select viseq from voucherissuance where status='未使用' and vid='{ticketNumber}'")
        voucher = cur.fetchall()

        cur.execute(f"select ename,email from employee where cname in (SELECT cname FROM voucher where vid = '{ticketNumber}')")
        mails = cur.fetchall()
        
        cur.close()
        conn.close()
        return render_template('IssueVouchers.html',voucher=voucher,mails=mails)



if __name__ == '__main__':
    app.secret_key = 'your_secret_key'  # 設定 session 密鑰
    app.run(debug=True)