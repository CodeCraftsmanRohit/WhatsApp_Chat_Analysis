from urlextract import URLExtract
from wordcloud import WordCloud
import pandas as pd
from collections import Counter
import emoji
import re
import numpy as np
from datetime import datetime

extract = URLExtract()

def fetch_stats(selected_user, df):
    """
    Fetch basic statistics for selected user
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Number of messages
        num_messages = df.shape[0]

        # Number of words
        words = []
        for message in df['message'].dropna():
            words.extend(message.split())

        # Media messages
        media_patterns = ['Media omitted', 'image omitted', 'video omitted',
                         'audio omitted', 'document omitted', '<Media omitted>']
        media_conditions = df['message'].str.contains('|'.join(media_patterns),
                                                     case=False, na=False)
        num_media_messages = media_conditions.sum()

        # Links
        links = []
        for message in df['message'].dropna():
            urls = extract.find_urls(message)
            if urls:
                links.extend(urls)

        return num_messages, len(words), num_media_messages, len(links)

    except Exception as e:
        print(f"Error in fetch_stats: {e}")
        return 0, 0, 0, 0

def most_busy_users(df):
    """
    Identify most active users in the chat
    """
    try:
        # Exclude system messages
        system_messages = ['group_notification', 'Notification', 'notification', 'System']
        filtered_df = df[~df['user'].isin(system_messages)]

        # Get top 10 users
        user_counts = filtered_df['user'].value_counts().head(10)

        # Calculate percentages - FIXED: Use list comprehension for rounding
        percentages = [(count / len(filtered_df)) * 100 for count in user_counts.values]
        rounded_percentages = [round(p, 2) for p in percentages]

        # Create dataframe
        percent_df = pd.DataFrame({
            'User': user_counts.index,
            'Messages': user_counts.values,
            'Percentage': rounded_percentages
        }).reset_index(drop=True)

        return user_counts, percent_df

    except Exception as e:
        print(f"Error in most_busy_users: {e}")
        return pd.Series(), pd.DataFrame()

def create_wordcloud(selected_user, df):
    """
    Create word cloud from messages
    """
    try:
        # Load stop words
        stop_words = set()
        try:
            with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
                stop_words = set(f.read().split())
        except FileNotFoundError:
            # Use basic English stop words
            stop_words = set(['the', 'and', 'to', 'of', 'i', 'a', 'you', 'is', 'that', 'it',
                             'in', 'my', 'for', 'me', 'on', 'this', 'with', 'but', 'have',
                             'are', 'was', 'be', 'so', 'just', 'like', 'not', 'at'])

        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Filter out system messages and media
        temp = df[
            (~df['user'].isin(['group_notification', 'Notification'])) &
            (~df['message'].str.contains('Media omitted|image omitted|video omitted',
                                        case=False, na=False))
        ].copy()

        if temp.empty:
            return None

        # Clean messages
        def clean_message(msg):
            if not isinstance(msg, str):
                return ""
            # Remove URLs
            msg = re.sub(r'http\S+', '', msg)
            # Remove emojis
            msg = ''.join(char for char in msg if char not in emoji.EMOJI_DATA)
            # Remove special characters
            msg = re.sub(r'[^\w\s]', '', msg)
            # Remove stop words
            words = [word for word in msg.lower().split() if word not in stop_words and len(word) > 2]
            return ' '.join(words)

        temp['cleaned_message'] = temp['message'].apply(clean_message)

        # Combine all messages
        text = ' '.join(temp['cleaned_message'].dropna())

        if not text.strip():
            return None

        # Generate word cloud
        wc = WordCloud(
            width=800,
            height=400,
            background_color='white',
            min_font_size=10,
            max_words=200,
            colormap='viridis'
        )

        return wc.generate(text)

    except Exception as e:
        print(f"Error in create_wordcloud: {e}")
        return None

def most_common_words(selected_user, df, top_n=20):
    """
    Find most common words in messages
    """
    try:
        # Load stop words
        stop_words = set()
        try:
            with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
                stop_words = set(f.read().split())
        except FileNotFoundError:
            stop_words = set(['the', 'and', 'to', 'of', 'i', 'a', 'you', 'is', 'that', 'it',
                             'in', 'my', 'for', 'me', 'on', 'this', 'with', 'but', 'have',
                             'are', 'was', 'be', 'so', 'just', 'like', 'not', 'at', 'hi',
                             'hello', 'hey', 'ok', 'okay', 'yes', 'no', 'hmm', 'lol'])

        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Filter messages
        temp = df[
            (~df['user'].isin(['group_notification', 'Notification'])) &
            (~df['message'].str.contains('Media omitted|image omitted|video omitted',
                                        case=False, na=False))
        ]

        words = []

        for message in temp['message'].dropna():
            # Clean message
            message = re.sub(r'http\S+', '', message)
            message = ''.join(char for char in message if char not in emoji.EMOJI_DATA)
            message = re.sub(r'[^\w\s]', '', message)

            # Split into words and filter
            for word in message.lower().split():
                if word not in stop_words and len(word) > 2:
                    words.append(word)

        # Count and return top N words
        word_counts = Counter(words)
        common_words = pd.DataFrame(word_counts.most_common(top_n))

        return common_words

    except Exception as e:
        print(f"Error in most_common_words: {e}")
        return pd.DataFrame()

def emoji_helper(selected_user, df):
    """
    Analyze emoji usage
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        emojis = []

        for message in df['message'].dropna():
            # Extract all emojis from message
            emojis.extend([c for c in message if c in emoji.EMOJI_DATA])

        if not emojis:
            return pd.DataFrame(columns=['Emoji', 'Count', 'Description'])

        # Count emojis
        emoji_counter = Counter(emojis)

        # Create DataFrame with emoji info
        emoji_list = []
        for emoji_char, count in emoji_counter.most_common():
            try:
                desc = emoji.demojize(emoji_char).replace(':', '').replace('_', ' ').title()
            except:
                desc = "Unknown Emoji"

            emoji_list.append({
                'Emoji': emoji_char,
                'Count': count,
                'Description': desc
            })

        return pd.DataFrame(emoji_list)

    except Exception as e:
        print(f"Error in emoji_helper: {e}")
        return pd.DataFrame()

def monthly_timeline(selected_user, df):
    """
    Create monthly timeline of messages
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Group by month and year
        df['year_month'] = df['date'].dt.to_period('M')
        timeline = df.groupby('year_month').size().reset_index(name='message')

        # Convert to string for display
        timeline['time'] = timeline['year_month'].dt.strftime('%b %Y')

        return timeline[['time', 'message']]

    except Exception as e:
        print(f"Error in monthly_timeline: {e}")
        return pd.DataFrame()

def daily_timeline(selected_user, df):
    """
    Create daily timeline of messages
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Group by date
        df['only_date'] = df['date'].dt.date
        daily_timeline = df.groupby('only_date').size().reset_index(name='message')

        return daily_timeline

    except Exception as e:
        print(f"Error in daily_timeline: {e}")
        return pd.DataFrame()

def week_activity_map(selected_user, df):
    """
    Map activity by day of week
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Get day names in order
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['day_name'] = pd.Categorical(df['date'].dt.day_name(), categories=days_order, ordered=True)

        return df['day_name'].value_counts().sort_index()

    except Exception as e:
        print(f"Error in week_activity_map: {e}")
        return pd.Series()

def month_activity_map(selected_user, df):
    """
    Map activity by month
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Get month names in order
        months_order = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December']
        df['month'] = pd.Categorical(df['date'].dt.month_name(), categories=months_order, ordered=True)

        return df['month'].value_counts().sort_index()

    except Exception as e:
        print(f"Error in month_activity_map: {e}")
        return pd.Series()

def activity_heatmap(selected_user, df):
    """
    Create activity heatmap (day vs time)
    """
    try:
        if selected_user != 'Overall':
            df = df[df['user'] == selected_user]

        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date'])

        # Create day and period columns
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['day_name'] = pd.Categorical(df['date'].dt.day_name(), categories=days_order, ordered=True)

        # Create time periods
        df['hour'] = df['date'].dt.hour
        df['period'] = df['hour'].apply(
            lambda x: f"{x:02d}:00"
        )

        # Create pivot table
        heatmap_data = df.pivot_table(
            index='day_name',
            columns='period',
            values='message',
            aggfunc='count',
            fill_value=0
        )

        return heatmap_data

    except Exception as e:
        print(f"Error in activity_heatmap: {e}")
        return pd.DataFrame()