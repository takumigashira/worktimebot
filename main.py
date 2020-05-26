from flask import Flask, request, abort,render_template, redirect

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageAction, FollowEvent, MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, PostbackTemplateAction, MessageTemplateAction, URITemplateAction
)
import os
import psycopg2
import datetime

# Flask
app = Flask(__name__)


#環境変数からLINE Access Tokenを設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
#環境変数からLINE Channel Secretを設定
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

#環境変数からDB接続用情報を取得
db_host = os.environ['DB_HOST']
db_port = os.environ['DB_PORT']
db_name = os.environ['DB_NAME']
db_user = os.environ['DB_USER']
db_pass = os.environ['DB_PASS']

#DB Connection
def get_DBconnection():
    dsn = "host=" + db_host + " " + "port=" + db_port + " " + "dbname=" + db_name + " " + "user=" + db_user + " " + "password=" + db_pass 
    return psycopg2.connect(dsn)

#table作成
def create_table():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute('CREATE TABLE IF NOT EXISTS worktime (id serial PRIMARY KEY, date varchar, arrival varchar, leaving varchar, location varchar);')
            except (psycopg2.OperationalError) as e:
                print(e)

#table削除
def delete_table():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            try:
                tablename = "worktime"
                cur.execute('DROP TABLE ' + tablename)
            except (psycopg2.OperationalError) as e:
                print(e)
#稼働登録
def addData():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            try:
                d = request.form["date"]
                s = request.form["start_time"]
                e = request.form["end_time"]
                l = request.form["location"]
                cur.execute('INSERT INTO worktime (date, arrival, leaving, location) VALUES (%s, %s, %s, %s)', (d,s,e,l))
                conn.commit()
            except (psycopg2.OperationalError) as e:
                print(e)

#稼働削除
def deleteData():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            try:
                i = request.form["deleteDateID"]
                cur.execute('DELETE FROM worktime WHERE id=(%s)', (i,))
                conn.commit()
            except (psycopg2.OperationalError) as e:
                print(e)

#稼働更新
def updateData():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            try:
                ui = request.form["update_id"]
                ud = request.form["update_date"]
                us = request.form["update_start_time"]
                ue = request.form["update_end_time"]
                ul = request.form["update_location"]
                cur.execute('UPDATE worktime SET date=(%s), arrival=(%s), leaving=(%s), location=(%s), WHERE id=(%s);', (ud,us,ue,ul,ui))
            except(psycopg2.OperationalError) as e:
                print(e)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    #app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

#DB Table作成
@app.route("/createtable", methods=['GET'])
def createTableTest():
    try:
        create_table()
    except InvalidSignatureError:
        abort(400)
    
    return 'table create SUCCESS'

#DB Table削除
@app.route("/deletetable", methods=["GET"])
def deleteTable():
    try:
        delete_table()
    except InvalidSignatureError:
        abort(400)

    return 'table delete SUCCESS'

#データ一覧表示
@app.route("/display",methods=['GET'])
def displayData():
    with get_DBconnection() as conn:
        with conn.cursor() as cur:
            sqlRes = "SELECT * FROM worktime;"
            tmpStr = []
            cur.execute(sqlRes)
            for row in cur:
                tmpStr.append(row)

            return render_template('display.html', len = len(tmpStr), tmp = tmpStr)

#データ追加
@app.route("/adddata", methods=["POST"])
def insertData():
    try:
       addData()
       return redirect("https://worktimebot.herokuapp.com/add")
    except InvalidSignatureError:
        abort(400)

#データ更新
@app.route("/updatedata", methods=["POST"])
def upData():
    try:
       updateData()
       return redirect("https://worktimebot.herokuapp.com/update")
    except InvalidSignatureError:
        abort(400)

#データ削除
@app.route("/deletedata", methods=["POST"])
def deldata():
    try:
       deleteData()
       return redirect("https://worktimebot.herokuapp.com/delete")
    except InvalidSignatureError:
        abort(400)


#登録用Form表示
@app.route("/add", methods=["GET"])
def addFormDisplay():
    return render_template('add.html', name="takumi")

#更新用Form表示
@app.route("/update", methods=["GET"])
def updateFormDisplay():
    return render_template('update.html', name="takumi")

#削除用Form表示
@app.route("/delete", methods=["GET"])
def deleteFormDisplay():
    return render_template('delete.html', name="takumi")

# MessageEvent
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #Lineアカウントのdisplay_nameを取得
    profile = line_bot_api.get_profile(event.source.user_id)
    if event.message.text=="登録":
        dst_user_id = profile.user_id
        line_bot_api.push_message(dst_user_id, TextSendMessage(text="こちらを開いて日付と時間を登録して下さい。" + "https://worktimebot.herokuapp.com/add"))
    elif event.message.text=="更新":
        dst_user_id = profile.user_id
        line_bot_api.push_message(dst_user_id, TextSendMessage(text="こちらを開いて削除操作をして下さい。" + "https://worktimebot.herokuapp.com/update"))

    elif event.message.text=="削除":
        dst_user_id = profile.user_id
        line_bot_api.push_message(dst_user_id, TextSendMessage(text="こちらを開いて削除操作をして下さい。" + "https://worktimebot.herokuapp.com/delete"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name+"さん。"+"登録、更新、削除のどれかにしてください"))

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)