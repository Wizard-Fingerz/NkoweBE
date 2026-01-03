import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elearning.settings')
import django
django.setup()

import requests
from bs4 import BeautifulSoup
from bs4 import Tag
import csv
from django.utils import timezone
import datetime

from courses.subjects.models import Subject
from exams.models import Exam, Question, Choice
from users.models import ExaminationType

BASE_URL = 'https://nigerianscholars.com'
BASE_PATH = '/past-questions/biology/jamb/year/2019/'
page = 5

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

MAX_PAGES = 9  # Set this to the number of pages you want to scrape

questions = []

for page in range(1, MAX_PAGES + 1):
    if page == 1:
        url = BASE_URL + BASE_PATH
    else:
        url = f"{BASE_URL}{BASE_PATH}page/{page}/"
    print(f"Scraping: {url}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    page_questions = []
    for q_div in soup.select('.question_block'):
        question_el = q_div.select_one('.question_text')
        question_text = question_el.get_text(strip=True) if question_el else None

        options = [opt.get_text(strip=True) for opt in q_div.select('.q_option')]

        answer_el = q_div.select_one('.ans_label')
        answer = answer_el.get_text(strip=True) if answer_el else None

        page_questions.append({
            'question': question_text,
            'options': options,
            'answer': answer
        })

    if not page_questions:
        print(f"Questions found: 0 (stopping)")
        break
    print(f"Questions found: {len(page_questions)}")
    questions.extend(page_questions)

# Print the results
for q in questions:
    print("Question:", q['question'])
    print("Options:", q['options'])
    print("Answer:", q['answer'])
    print("-" * 40)

print(f'Scraping complete! Total questions scraped: {len(questions)}')

subject, _ = Subject.objects.get_or_create(name="Biology")
exam, _ = Exam.objects.get_or_create(
    subject=subject,
    title="JAMB 2019 Biology",
    examination_type = ExaminationType.objects.get(name = 'JAMB'),
    
    defaults={
        "description": "JAMB 2019 Biology Questions",
        "duration": timezone.timedelta(seconds=3600),  # 1 hour
        "total_marks": 100,
        "year": 2019,
        "passing_marks": 40,
        "start_time": timezone.now(),
        "end_time": timezone.now() + timezone.timedelta(hours=1),
        "is_published": True,
    }
)

for idx, q in enumerate(questions, start=1):
    question_obj = Question.objects.create(
        exam=exam,
        question_text=q['question'],
        question_type='multiple_choice',  # or as appropriate
        marks=1,  # or as appropriate
        order=idx
    )
    for opt in q['options']:
        is_correct = (opt == q['answer'])
        Choice.objects.create(
            question=question_obj,
            choice_text=opt,
            is_correct=is_correct
        )

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f'scraped_questions_{timestamp}.csv'

with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow(['question_text', 'option_1', 'option_2', 'option_3', 'option_4', 'correct_option'])
    for q in questions:
        row = [
            q['question'],
            q['options'][0] if len(q['options']) > 0 else '',
            q['options'][1] if len(q['options']) > 1 else '',
            q['options'][2] if len(q['options']) > 2 else '',
            q['options'][3] if len(q['options']) > 3 else '',
            q['answer'] or ''
        ]
        writer.writerow(row)
print(f'Questions exported to {csv_filename}')