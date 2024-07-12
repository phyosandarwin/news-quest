from bs4 import BeautifulSoup
import requests
import random

def parse_article(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')

        if not paragraphs:
            return None  # No paragraphs found

        text = [paragraph.get_text().strip() for paragraph in paragraphs]
        article_text = ' '.join(text)
        return article_text

    except requests.RequestException as e:
        print(f"Error fetching article: {e}")
        return None

def summarise_article(text, chat):
    summary_text = chat.send_message("Summarize these chunks of text into a concise paragraph of 100 words: " + text)
    return summary_text.text

def generate_quiz_questions(summary_text, chat):
    # Send a big prompt to the model to generate multiple-choice questions based on the summary
    response = chat.send_message([
    f"""
    You are a helpful assistant programmed to generate 3 distinct questions based on the text in {summary_text} provided. 
    Each of these questions will also have 3 possible answers: one correct answer and two incorrect ones. 
    Structure your response in a way that emulates a Python list of lists. 

    Your output should be shaped as follows:

    1. An outer list that contains 3 inner lists.
    2. Each inner list represents a set of question and answers, and contains exactly 4 strings in this order:
    - The generated question.
    - The correct answer.
    - The first incorrect answer.
    - The second incorrect answer.

    Your output should follow this structure:
    [
        ["Generated Question 1", "Correct Answer 1", "Incorrect Answer 1.1", "Incorrect Answer 1.2"],
        ["Generated Question 2", "Correct Answer 2", "Incorrect Answer 2.1", "Incorrect Answer 2.2"],
        ["Generated Question 3", "Correct Answer 3", "Incorrect Answer 3.1", "Incorrect Answer 3.2"]
    ]
    This is the summary text: {summary_text}
    """
    ])

    # Parse the response into a list of lists
    quiz_data = eval(response.text.strip())
    # Format the quiz data for display
    formatted_quiz_data = []
    for i, question_data in enumerate(quiz_data):
        # Extract the question and options
        question = question_data[0]
        options = question_data[1:]

        # randomly shuffle options
        random.shuffle(options)

        # Find the index of the correct answer (correct option initially the first one) after shuffling
        correct_answer_index = options.index(question_data[1])

        # Add the formatted question data to the list
        formatted_quiz_data.append({
            "question": f"Question {i+1}: {question}",
            "options": options,
            "correct_answer_index": correct_answer_index
        })
    return formatted_quiz_data