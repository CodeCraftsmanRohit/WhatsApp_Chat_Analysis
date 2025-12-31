import re
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def preprocess(data):
    """
    Preprocess WhatsApp chat data
    """
    try:
        # Handle different WhatsApp formats
        # Common pattern for most WhatsApp exports
        pattern = r'(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}\s?[APapMm]*)\s*-\s*(.*)'

        lines = data.strip().split('\n')
        messages = []
        dates = []

        for line in lines:
            if not line.strip():
                continue

            match = re.match(pattern, line)
            if match:
                dates.append(match.group(1))
                messages.append(match.group(2))
            else:
                # If line doesn't match pattern, append to last message
                if messages:
                    messages[-1] += ' ' + line.strip()

        if not messages:
            # Try alternative pattern
            pattern2 = r'\[(\d{1,2}/\d{1,2}/\d{2,4},\s\d{1,2}:\d{2}:\d{2})\]\s*(.*)'
            for line in lines:
                match = re.match(pattern2, line)
                if match:
                    dates.append(match.group(1))
                    messages.append(match.group(2))
                elif messages:
                    messages[-1] += ' ' + line.strip()

        if not messages:
            raise ValueError("No valid messages found in the file")

        # Create DataFrame
        df = pd.DataFrame({
            'raw_message': messages,
            'date_string': dates
        })

        # Clean date strings - FIXED: Use raw string for regex
        df['date_string'] = df['date_string'].str.replace(r'[\[\]]', '', regex=True)
        df['date_string'] = df['date_string'].str.replace('\u202f', ' ', regex=False)

        # Parse dates
        df['date'] = pd.to_datetime(df['date_string'], format='mixed', errors='coerce')

        # Drop rows where date couldn't be parsed
        df = df.dropna(subset=['date'])

        # Extract user and message
        def extract_user_message(text):
            if not isinstance(text, str):
                return 'group_notification', ''

            # Common patterns
            if ': ' in text:
                parts = text.split(': ', 1)
                if len(parts) == 2:
                    user = parts[0].strip()
                    # Clean user name
                    user = re.sub(r'[\u202c\u200e]', '', user)
                    message = parts[1].strip()
                    return user, message

            return 'group_notification', text.strip()

        # Apply extraction
        extracted = df['raw_message'].apply(extract_user_message)
        df['user'] = extracted.apply(lambda x: x[0])
        df['message'] = extracted.apply(lambda x: x[1])

        # Remove rows with empty messages
        df = df[df['message'].str.strip() != '']

        # Create datetime features
        df['only_date'] = df['date'].dt.date
        df['year'] = df['date'].dt.year
        df['month_num'] = df['date'].dt.month
        df['month'] = df['date'].dt.month_name()
        df['day'] = df['date'].dt.day
        df['day_name'] = df['date'].dt.day_name()
        df['hour'] = df['date'].dt.hour
        df['minute'] = df['date'].dt.minute

        # Create time periods
        def get_period(hour):
            periods = [
                (0, 2, "00-02"), (2, 4, "02-04"), (4, 6, "04-06"),
                (6, 8, "06-08"), (8, 10, "08-10"), (10, 12, "10-12"),
                (12, 14, "12-14"), (14, 16, "14-16"), (16, 18, "16-18"),
                (18, 20, "18-20"), (20, 22, "20-22"), (22, 24, "22-24")
            ]
            for start, end, label in periods:
                if start <= hour < end:
                    return label
            return "22-24"

        df['period'] = df['hour'].apply(get_period)

        # Drop unnecessary columns
        df = df.drop(['raw_message', 'date_string'], axis=1)

        # Reset index
        df = df.reset_index(drop=True)

        return df

    except Exception as e:
        print(f"Error in preprocessing: {e}")
        import traceback
        traceback.print_exc()
        return None