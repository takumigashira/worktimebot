from flask import Flask, request, abort

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

#DB Resopnse
def get_response_message(mes_form):
    if mes_form=="日付":
        with get_DBconnection() as conn:
            with conn.cursor(name="cs") as cur:
                try:
                    sqlStr = "SELECT TO_CHAR(CURRENT_DATE, 'yyyy/mm/dd');"
                    cur.execute(sqlStr)
                    (mes,) = cur.fetchone()
                    return mes
                except:
                    mes = "exception"
                    return mes
    #日付以外はそのまま返す
    return mes_form

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

# MessageEvent
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    #Lineアカウントのdisplay_nameを取得
    profile = line_bot_api.get_profile(event.source.user_id)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=profile.display_name+"さん"))
    # if event.message.text=="登録":
    #     TextSendMessage(text="登録ですね")
    # elif event.message.text=="更新":
    #     TextSendMessage(text="更新ですね")
    # elif event.message.text=="削除":
    #     TextSendMessage(text="削除ですね")
    # else:
    #     TextSendMessage(text="登録、更新、削除のどれかにしてください")


    #line_bot_api.reply_message(event.reply_token,TextSendMessage(text=profile.display_name))
    # #登録、更新、削除に分岐

#オウム返し
#    line_bot_api.reply_message(
#        event.reply_token,
#        TextSendMessage(text=get_response_message(event.message.text)))

    #profileを取得
    #profile = line_bot_api.get_profile(event.source.user_id)

    #status_msg = profile.status_message
    #if status_msg is None:
    #    status_msg = "ステータスメッセージなし"
    
    #messages = TemplateSendMessage(alt_text="Buttons template",
    #                                   template=ButtonsTemplate(
    #                                   thumbnail_image_url=profile.picture_url,
    #                                   title=profile.display_name,
    #                                   text=f"User Id: {profile.user_id[:5]}...\n"
    #                                        f"Status message: {status_msg}",
    #                                   actions=[MessageAction(label="成功", text="次は？")]))

    #line_bot_api.reply_message(event.reply_token, messages=messages)

if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)