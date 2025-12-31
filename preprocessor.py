import re
import pandas as pd

def preprocess(data):

    # WhatsApp datetime pattern (Unicode-safe)
    pattern = r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}[\u202f\s]?(?:AM|PM))\s-\s'

    messages = re.split(pattern, data)[1:]
    dates = messages[::2]
    messages = messages[1::2]

    df = pd.DataFrame({
        'user_message': messages,
        'message_date': dates
    })

    # clean unicode + dash
    df['message_date'] = (
        df['message_date']
        .str.replace('\u202f', ' ', regex=False)
        .str.replace(' -', '', regex=False)
    )

    # parse datetime safely
    df['date'] = pd.to_datetime(df['message_date'], format='mixed', errors='coerce')
    df.drop(columns=['message_date'], inplace=True)

    # separate user & message
    users = []
    msgs = []

    for message in df['user_message']:
        entry = re.split(r'^([^:]+):\s', message)
        if len(entry) > 1:
            users.append(entry[1])
            msgs.append(entry[2])
        else:
            users.append('group_notification')
            msgs.append(entry[0])

    df['user'] = users
    df['message'] = msgs
    df.drop(columns=['user_message'], inplace=True)

    # datetime features
    df['only_date'] = df['date'].dt.date
    df['year'] = df['date'].dt.year
    df['month_num'] = df['date'].dt.month
    df['month'] = df['date'].dt.month_name()
    df['day'] = df['date'].dt.day
    df['day_name'] = df['date'].dt.day_name()
    df['hour'] = df['date'].dt.hour
    df['minute'] = df['date'].dt.minute

    # period column (hour buckets)
    df['period'] = df['hour'].apply(
        lambda x: "23-00" if x == 23 else f"{x:02d}-{x+1:02d}"
    )

    return df
