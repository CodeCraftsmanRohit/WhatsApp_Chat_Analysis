import streamlit as st
import preprocessor
import helper
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="WhatsApp Chat Analyzer",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #25D366;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #25D366;
        margin-bottom: 10px;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stButton button {
        width: 100%;
        background-color: #25D366;
        color: white;
        font-weight: bold;
    }
    .stButton button:hover {
        background-color: #128C7E;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None

st.sidebar.title("📱 WhatsApp Chat Analyzer")
st.sidebar.markdown("---")

# File uploader with instructions
st.sidebar.markdown("### 📤 Upload WhatsApp Chat")
uploaded_file = st.sidebar.file_uploader(
    "Choose a .txt file",
    type=['txt'],
    help="Export your WhatsApp chat without media and upload the .txt file"
)

if uploaded_file is not None:
    try:
        # Read and decode file
        bytes_data = uploaded_file.getvalue()

        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'latin-1']
        data = None

        for encoding in encodings:
            try:
                data = bytes_data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if data is None:
            st.error("Unable to decode the file. Please ensure it's a valid WhatsApp chat export.")
            st.stop()

        # Preprocess data
        with st.spinner("Processing chat data..."):
            df = preprocessor.preprocess(data)
            if df is not None and not df.empty:
                st.session_state.df = df
                st.sidebar.success("✅ Data loaded successfully!")
            else:
                st.error("No valid messages found in the chat file.")
                st.stop()

    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        st.stop()

# User selection
if st.session_state.df is not None:
    df = st.session_state.df

    # Fetch unique users
    user_list = df['user'].unique().tolist()

    # Remove system messages
    system_messages = ['group_notification', 'Notification', 'notification', 'System']
    user_list = [user for user in user_list if user not in system_messages]

    if len(user_list) == 0:
        st.error("No valid users found in the chat.")
        st.stop()

    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox(
        "👤 Select User for Analysis",
        user_list,
        help="Select 'Overall' for group analysis or a specific user"
    )

    st.sidebar.markdown("---")

    # Analysis button
    if st.sidebar.button("🚀 Analyze Chat"):

        # Main header
        st.markdown(f"<h1 class='main-header'>📊 Chat Analysis: {selected_user}</h1>", unsafe_allow_html=True)

        # Top Statistics
        st.markdown("## 📈 Top Statistics")
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("📨 Total Messages", f"{num_messages:,}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("💬 Total Words", f"{words:,}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🖼️ Media Shared", f"{num_media_messages:,}")
            st.markdown('</div>', unsafe_allow_html=True)

        with col4:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("🔗 Links Shared", f"{num_links:,}")
            st.markdown('</div>', unsafe_allow_html=True)

        # Timeline Analysis
        st.markdown("---")
        st.markdown("## 📅 Timeline Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Monthly Timeline")
            timeline = helper.monthly_timeline(selected_user, df)
            if not timeline.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(timeline['time'], timeline['message'], color='#25D366', linewidth=2.5, marker='o')
                ax.fill_between(timeline['time'], timeline['message'], alpha=0.3, color='#25D366')
                ax.set_xlabel('Month-Year', fontsize=12)
                ax.set_ylabel('Number of Messages', fontsize=12)
                ax.set_title('Monthly Activity Trend', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close()

        with col2:
            st.markdown("### Daily Timeline")
            daily_timeline = helper.daily_timeline(selected_user, df)
            if not daily_timeline.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(daily_timeline['only_date'], daily_timeline['message'],
                       color='#128C7E', linewidth=2)
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Number of Messages', fontsize=12)
                ax.set_title('Daily Activity Trend', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45, ha='right')
                plt.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close()

        # Activity Analysis
        st.markdown("---")
        st.markdown("## 🕒 Activity Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Most Active Day")
            busy_day = helper.week_activity_map(selected_user, df)
            if not busy_day.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = plt.cm.Set3(range(len(busy_day)))
                ax.bar(busy_day.index, busy_day.values, color=colors)
                ax.set_xlabel('Day of Week', fontsize=12)
                ax.set_ylabel('Number of Messages', fontsize=12)
                ax.set_title('Activity by Day', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45)
                st.pyplot(fig)
                plt.close()

        with col2:
            st.markdown("### Most Active Month")
            busy_month = helper.month_activity_map(selected_user, df)
            if not busy_month.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = plt.cm.Paired(range(len(busy_month)))
                ax.bar(busy_month.index, busy_month.values, color=colors)
                ax.set_xlabel('Month', fontsize=12)
                ax.set_ylabel('Number of Messages', fontsize=12)
                ax.set_title('Activity by Month', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45)
                st.pyplot(fig)
                plt.close()

        # Heatmap
        st.markdown("### Weekly Activity Heatmap")
        heatmap = helper.activity_heatmap(selected_user, df)
        if not heatmap.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            sns.heatmap(heatmap, cmap='YlGnBu', linewidths=0.5, linecolor='gray',
                       cbar_kws={'label': 'Number of Messages'})
            ax.set_xlabel('Time Period (Hour)', fontsize=12)
            ax.set_ylabel('Day of Week', fontsize=12)
            ax.set_title('Activity Heatmap (Day vs Time)', fontsize=14, fontweight='bold')
            st.pyplot(fig)
            plt.close()

        # User Analysis (Only for Overall)
        if selected_user == "Overall":
            st.markdown("---")
            st.markdown("## 👥 User Analysis")

            x, new_df = helper.most_busy_users(df)

            col1, col2 = st.columns([3, 2])

            with col1:
                st.markdown("### Most Active Users")
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = plt.cm.viridis(range(len(x)))
                bars = ax.bar(x.index, x.values, color=colors)
                ax.set_xlabel('Users', fontsize=12)
                ax.set_ylabel('Number of Messages', fontsize=12)
                ax.set_title('Top Contributors', fontsize=14, fontweight='bold')
                plt.xticks(rotation=45, ha='right')

                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                           f'{int(height):,}', ha='center', va='bottom', fontsize=10)

                st.pyplot(fig)
                plt.close()

            with col2:
                st.markdown("### User Contribution")
                st.dataframe(new_df, width='stretch')

        # Word Analysis
        st.markdown("---")
        st.markdown("## 📝 Word Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Word Cloud")
            try:
                wc = helper.create_wordcloud(selected_user, df)
                if wc:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    ax.imshow(wc, interpolation='bilinear')
                    ax.axis("off")
                    ax.set_title('Frequent Words', fontsize=14, fontweight='bold')
                    st.pyplot(fig)
                    plt.close()
            except Exception as e:
                st.warning("Word cloud could not be generated.")

        with col2:
            st.markdown("### Most Common Words")
            common_df = helper.most_common_words(selected_user, df)
            if not common_df.empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                colors = plt.cm.coolwarm(range(len(common_df)))
                bars = ax.barh(common_df[0], common_df[1], color=colors)
                ax.set_xlabel('Frequency', fontsize=12)
                ax.set_ylabel('Words', fontsize=12)
                ax.set_title('Top 20 Most Used Words', fontsize=14, fontweight='bold')
                ax.invert_yaxis()

                # Add value labels
                for i, (value, bar) in enumerate(zip(common_df[1], bars)):
                    ax.text(value + 0.1, bar.get_y() + bar.get_height()/2,
                           f' {value}', va='center', fontsize=10)

                st.pyplot(fig)
                plt.close()

        # Emoji Analysis
        st.markdown("---")
        st.markdown("## 😊 Emoji Analysis")

        emoji_df = helper.emoji_helper(selected_user, df)

        if not emoji_df.empty:
            col1, col2 = st.columns([2, 3])

            with col1:
                st.markdown("### Top Emojis")
                st.dataframe(emoji_df.head(10), width='stretch')

            with col2:
                st.markdown("### Emoji Distribution")
                fig, ax = plt.subplots(figsize=(8, 8))
                # Fixed: Use column names instead of indices
                if 'Count' in emoji_df.columns and 'Emoji' in emoji_df.columns:
                    ax.pie(emoji_df['Count'].head(10), labels=emoji_df['Emoji'].head(10),
                          autopct='%1.1f%%', startangle=90,
                          colors=plt.cm.tab20c(range(len(emoji_df.head(10)))))
                else:
                    # Fallback to index-based access
                    ax.pie(emoji_df.iloc[:, 1].head(10), labels=emoji_df.iloc[:, 0].head(10),
                          autopct='%1.1f%%', startangle=90,
                          colors=plt.cm.tab20c(range(len(emoji_df.head(10)))))
                ax.set_title('Top 10 Emoji Usage', fontsize=14, fontweight='bold')
                ax.axis('equal')
                st.pyplot(fig)
                plt.close()
        else:
            st.write("No emojis found in the chat.")

        # Download Section
        st.markdown("---")
        st.markdown("## 📥 Export Analysis")

        col1, col2, col3 = st.columns(3)

        with col1:
            stats_df = pd.DataFrame({
                'Metric': ['Total Messages', 'Total Words', 'Media Shared', 'Links Shared'],
                'Value': [num_messages, words, num_media_messages, num_links]
            })
            st.download_button(
                label="📊 Download Statistics CSV",
                data=stats_df.to_csv(index=False),
                file_name=f"chat_stats_{selected_user}.csv",
                mime="text/csv"
            )

        with col2:
            timeline_data = helper.monthly_timeline(selected_user, df)
            st.download_button(
                label="📅 Download Timeline CSV",
                data=timeline_data.to_csv(index=False),
                file_name=f"timeline_{selected_user}.csv",
                mime="text/csv"
            )

        with col3:
            if not emoji_df.empty:
                st.download_button(
                    label="😊 Download Emoji Data",
                    data=emoji_df.to_csv(index=False),
                    file_name=f"emoji_analysis_{selected_user}.csv",
                    mime="text/csv"
                )

        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <p>Made with ❤️ using Streamlit | WhatsApp Chat Analyzer v2.0</p>
        <p>Note: This tool analyzes chat data locally. No data is stored on any server.</p>
        </div>
        """, unsafe_allow_html=True)

else:
    # Welcome screen
    st.markdown("<h1 class='main-header'>📱 WhatsApp Chat Analyzer</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.image("https://cdn-icons-png.flaticon.com/512/220/220236.png", width=200)

    st.markdown("""
    ## Welcome! 👋

    This interactive dashboard helps you analyze your WhatsApp chat history with:

    ### 📊 **Features:**
    - **Message Statistics**: Total messages, words, media, and links
    - **Timeline Analysis**: Monthly and daily activity trends
    - **Activity Maps**: Busiest days, months, and heatmaps
    - **Word Analysis**: Word clouds and most common words
    - **Emoji Analysis**: Most used emojis and their frequency
    - **User Analysis**: Most active users in group chats

    ### 📝 **How to Use:**
    1. **Export your WhatsApp chat**:
       - Open any WhatsApp chat
       - Tap on three dots → More → Export chat
       - Choose "Without Media"
       - You'll receive a `.txt` file

    2. **Upload the file** in the sidebar

    3. **Select a user** or choose "Overall" for group analysis

    4. **Click "Analyze Chat"** to see insights!

    ---

    **⚠️ Privacy Note**: All processing happens locally in your browser.
    Your chat data is never uploaded to any server.
    """)