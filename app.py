import streamlit as st
import pandas as pd
import google.generativeai as genai
from typing import Optional, Dict, Any

# IMPORT HELPER FUNCTIONS
from helpers.fetch_articles import *
from helpers.article_review import *

st.set_page_config(page_title='News Aggregator', page_icon='📖', layout='wide', initial_sidebar_state='expanded')

# Init news api key
newsapi = st.secrets['newsapi']['API_KEY']

# Initialize session state
if "selected_article_title" not in st.session_state:
    st.session_state["selected_article_title"] = None
if "selected_article_url" not in st.session_state:
    st.session_state["selected_article_url"] = None
if "article_summary" not in st.session_state:
    st.session_state["article_summary"] = None
if "quiz_data_list" not in st.session_state:
    st.session_state["quiz_data_list"] = None

genai.configure(api_key=st.secrets['gemini']['GOOGLE_API_KEY'])

def generate_summary():
    url = st.session_state["selected_article_url"]
    article_text = parse_article(url)
    if article_text:
        first_model = genai.GenerativeModel('gemini-1.0-pro')
        first_chat = first_model.start_chat(history=[])
        try:
            summary = summarise_article(article_text, first_chat)
            st.session_state["article_summary"] = summary
            
        except Exception as e:
            st.warning("Apologies, unable to generate summary ☹️")
            st.stop()

def generate_questions():
    if "article_summary" in st.session_state:
        summary = st.session_state["article_summary"]
        with st.spinner("Crafting your quiz..."):
            second_model = genai.GenerativeModel('gemini-1.0-pro')
            second_chat = second_model.start_chat(history=[])
            quiz_data_list = generate_quiz_questions(summary, second_chat)
            st.session_state["quiz_data_list"] = quiz_data_list


            
def to_dataframe(data: Optional[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    if data is None:
        return None
    articles = data.get('articles', [])
    return pd.DataFrame(articles)

def is_article_accessible(url: str) -> bool:
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.warning(f"Error checking article accessibility: {e}")
        return False

def display_news(df):
    st.markdown('<p style="font-size:24px; font-weight:bold;">News Articles Search Results</p>', unsafe_allow_html=True)
    if df is None:
        st.info("No News")
    else:
        for i in range(len(df)):
            story = df.iloc[i]
            source = story.get("source", {}).get("name", "Unknown Source")
            article_title = story.get("title", "No Title")
            imageURL = story.get("urlToImage", "")
            publishedTime = format_date(story.get("publishedAt", ""))
            description = story.get("description", "")
            article_url = story.get("url", "")
            
            if article_title and article_url and article_title != '[Removed]' and article_url != '[Removed]':
                if is_article_accessible(article_url):
                    with st.container():
                        col1, _, col2, col3 = st.columns([1, 0.5, 4, 1])
                        with col1:
                            if imageURL:
                                st.image(imageURL, width=150)
                        with col2:
                            st.markdown(f'[{article_title}]({article_url}) ({source})')
                            st.text(publishedTime)
                            if description:
                                with st.expander("Read more"):
                                    st.write(description)
                        with col3:
                            def create_article_callback(title=article_title, url=article_url):
                                def article_callback():
                                    st.session_state["selected_article_title"] = title
                                    st.session_state["selected_article_url"] = url
                                    st.session_state["article_summary"] = None
                                    st.session_state["quiz_data_list"] = None
                                    display_study_page()
                                return article_callback

                            # Ensure each button has a unique key
                            button_key = f"study_btn_{i}"
                            st.button(label=f"Study →", on_click=create_article_callback(article_title, article_url), key=button_key, use_container_width=True, type="primary")
                        
                        st.markdown("---")

def display_study_page():
    st.markdown('<p style="font-size:30px; font-weight:bold;">Study Article in Greater Detail</p>', unsafe_allow_html=True)
    title = st.session_state["selected_article_title"]
    st.markdown(f'*{title}*')
    
    st.button("Generate Summary", type='primary', on_click=generate_summary, key='summary_button')
    if st.session_state.article_summary:
        st.markdown("#### **Summary:**")
        st.write(st.session_state.article_summary)

        st.button("Generate Questions", type='primary', on_click=generate_questions, key='questions_button')
        if st.session_state.quiz_data_list:
            if 'user_answers' not in st.session_state:
                st.session_state.user_answers = [None for _ in st.session_state.quiz_data_list]
            if 'correct_answers' not in st.session_state:
                st.session_state.correct_answers = [q["options"][q["correct_answer_index"]] for q in st.session_state.quiz_data_list]
            if 'randomized_options' not in st.session_state:
                st.session_state.randomized_options = [q["options"] for q in st.session_state.quiz_data_list]
            
            with st.form(key='my_quiz'):
                    st.subheader("🧠 Quiz Time: Test Your Knowledge!")
                    for i, q in enumerate(st.session_state.quiz_data_list):
                        options = st.session_state.randomized_options[i]
                        default_index = st.session_state.user_answers[i] if st.session_state.user_answers[i] is not None else 0
                        response = st.radio(q["question"], options, index=default_index, key=f"radio_{i}")
                        user_choice_index = options.index(response)
                        st.session_state.user_answers[i] = user_choice_index

                    results_submitted = st.form_submit_button(label='Unveil My Score!', type='primary')

                    if results_submitted:
                        score = sum([ua == st.session_state.randomized_options[i].index(ca) for i, (ua, ca) in enumerate(zip(st.session_state.user_answers, st.session_state.correct_answers))])
                        st.success(f"Your score: {score}/{len(st.session_state.quiz_data_list)}")

                        if score == len(st.session_state.quiz_data_list):
                            st.success("Congratulations! You got all correct!")
                            st.balloons()
                        else:
                            incorrect_count = len(st.session_state.quiz_data_list) - score
                            st.warning(f"Almost there! You got {incorrect_count} questions wrong. Let's review them:")

                        for i, (ua, ca, q, ro) in enumerate(zip(st.session_state.user_answers, st.session_state.correct_answers, st.session_state.quiz_data_list, st.session_state.randomized_options)):
                            if ro[ua] != ca:
                                with st.expander(f"Question {i + 1}"):
                                    st.info(f"Question: {q['question']}")
                                    st.error(f"Your answer: {ro[ua]}")
                                    st.success(f"Correct answer: {ca}")


def clear_article_selection():
    st.session_state["selected_article_title"] = None
    st.session_state["selected_article_url"] = None
    st.session_state["article_summary"] = None
    st.session_state["quiz_data_list"] = None
    

def main():
    st.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] {{
            width: 350px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    
    keyword_news = None
    category_news = None

    with st.sidebar:
        st.title("📰 News Aggregator")
        tabs = st.tabs(["Search by Keyword", "Search by Category"])

        with tabs[0]:
            st.subheader("🔍 News Topic")
            topic = st.text_input('Enter news keyword:', placeholder='AI, Climate Change').strip()
            searchfields = st.multiselect(
                label="Find Keyword In: ",
                options=["title", "description", "content"],
                default=["title","description", "content"]
            )
            searchfields_str = ",".join(searchfields)
            if st.button("Start Keyword Search 🔍", use_container_width=True):
                keyword_news = to_dataframe(fetch_everything(topic, searchfields_str, newsapi))

        with tabs[1]:
            st.subheader('🔝 Get the top headlines:')
            category = st.selectbox(
                'Category', ('Business', 'Entertainment', 'General', 'Health', 'Science', 'Sports', 'Technology'), index=2
            )
            country = st.selectbox('Country', COUNTRY_NAMES, index=44)
            country_code = get_country_code(country)
            if st.button("Start Category Search 🌏", use_container_width=True):
                category_news = to_dataframe(fetch_headlines(category.lower(), country_code, newsapi))

        # new article selection
        reset_button = st.button("Reset search")
        if reset_button:
            clear_article_selection()

    if keyword_news is not None:
        display_news(keyword_news)
    elif category_news is not None:
        display_news(category_news)

    if st.session_state["selected_article_title"]:
        display_study_page()
            
if __name__ == "__main__":
    main()
