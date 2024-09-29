import config 
import gspread
import random
import datetime
import pandas as pd
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)


#Googleスプレッドシートの情報を得る.

# 認証してGoogleスプレッドシートにアクセス
gc = gspread.service_account(
    filename="linebot.json"
)
# スプレッドシートを開く (スプレッドシートのURLの最後にあるIDを使用)

sh = gc.open_by_key(config.SPREADSHEET_URL)

#これでsh.sheet1.get_all_values()でシート1の全ての値を取り出せるようになった。

#LINEbotを操作する.
app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)    


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

# 反応の関数。
def generate_responce():
    responce_list = [
        "ですね！\n今日がいい日になりますように。",
        "で記入しました！\n健康第一ですよ〜！",
        "ですね！\n今日は演劇日和かも。",
        "ですね！\nたまにはホッと一息。🍵",
        "ですね！\nいってらっしゃい〜！",
        "ですね！\n今日はいいことがある予感🔮",
        "で記入しました！\nありがとうございます💡",
        "ですね！\n気合い入れていきましょ〜！⭐️",
        "デスネ。\nキニュウイタシマシタ🤖",
        "ですね！\nちゃんと記入できましたよ〜🖊️",
        "ですにゃん🐈",
        "ですね！\n素敵な一日になりますように！！",
    ]
    return random.choice(responce_list)


#空のユーザー辞書を作成.
member_ws = sh.worksheet("members")

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.reply_token == "00000000000000000000000000000000":
        return
    
    user_input = event.message.text

    #プロフィールの情報を取得。
    profile = line_bot_api.get_profile(event.source.user_id)
    user_id        = event.source.user_id # ユーザID (zzz)
    user_disp_name = profile.display_name # アカウント名   

    user_list = member_ws.get_all_values()
    user_df = pd.DataFrame(user_list,columns=['user_id', 'line_name','user_name'])

    #初期値の設定。
    num = 0

    for user,name in zip(user_df["user_id"],user_df["user_name"]):
        if user_id == user:
           user_name = name
           num = 1

    if num == 0:
        user_name = str(user_input)[3:]
        new_df = pd.DataFrame([{'user_id':str(user_id), 'line_name':str(user_disp_name),'user_name':user_name}])
        user_df = pd.concat([user_df,new_df])
        member_ws.insert_row([str(user_id),str(user_disp_name),user_name], 1)
    else:
        num = 0

    #JSTの時間を取得。
    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )
        
    try:
        temperature = float(user_input)

        #スプレッドシートに書き込む
        ws = sh.worksheet("data")
        # 指定行に引数のリストの内容を1行追加
        ws.insert_row([str(now),str(user_id),str(user_name),str(user_disp_name),str(user_input)], 2)

        #LINEbotで返信

        if temperature >= 37.5:
            message = str(user_input) + "ですね。\nお大事になさってください。"
        else:
            message = user_input + generate_responce()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )

    except:
        if "登録" in user_input:
            message = user_name + "さん\n名前の登録ありがとうございます。"
        else:
            message = "正しい値を入力してください。"
        
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message)
        )

if __name__ == "__main__":
    app.run(host="localhost", port=8000)