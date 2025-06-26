SQLite
保持する必要のあるデータ
イベントID 主キー
    role ID
    チャンネルID


Discord で必要な処理
scheduled Event_create or delete
https://discordpy.readthedocs.io/ja/latest/api.html?highlight=event#discord.on_scheduled_event_create

    on_scheduled_event_create(event)
    on_scheduled_event_delete(event)

    返ってくる値
    https://discordpy.readthedocs.io/ja/latest/api.html?highlight=event#discord.ScheduledEvent
    
    作成されたときに取得する情報
    ・start_time
    ・id

on_scheduled_event_user_add or remove
https://discordpy.readthedocs.io/ja/latest/api.html?highlight=on_scheduled_event_user_add#discord.on_scheduled_event_user_add
    on_scheduled_event_user_add(event, user)
    on_scheduled_event_user_remove(event, user)

    

create_role or delete
https://discordpy.readthedocs.io/ja/latest/api.html?highlight=role#discord.Guild.create_role
    create_role

チャンネルを作成する
https://discordpy.readthedocs.io/ja/stable/api.html?highlight=create%20channel#discord.Guild.create_text_channel

role を作成する
https://discordpy.readthedocs.io/ja/stable/api.html?highlight=create%20role#discord.Guild.create_role


処理

スケジュールが作成されたとき
    ロールを作成 ( イベントの日付にする yyyymmdd )
    イベントカテゴリの中にチャンネルを作成
        チャンネルに対し、前処理で作成したロールはチャットの送信、メッセージを見るなどの基本操作を許可する

スケジュールが終了したとき
    データベースに イベント終了フラグを立てる

スケジュールが更新されたとき
    変わった項目の確認
    スケジュールが変わっていたとき
        チャンネル名の日付を更新
        ロールの名前を更新

bot に必要な権限
・Intents.guild_scheduled_events 
・manage_events
・manage_roles

1108369998864

https://discord.com/oauth2/authorize?client_id=1373633404154941450