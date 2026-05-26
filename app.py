from flask import Flask, render_template
from datetime import datetime
from datetime import date
import os
import secrets
import requests
import PyPDF2
import re
import calendar
import requests
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))


def get_todays_date():
    """Return today's date in a readable format"""
    return datetime.now().strftime("%B %d, %Y")


def is_odd_or_even_day():
    """
    Fetches the public Google Doc and returns either 'Odd' or 'Even',
    whichever appears first in the document. Returns None if neither found.
    """
    try:
        url = "https://docs.google.com/document/d/15ioQ4ZNdx_BoY8GVmws3yaRgoG_6242T36waxOqUnb8/export?format=txt"
        r = requests.get(url)
        r.raise_for_status()
        text = r.text

        match = re.search(r"\b(Odd|Even)\b", text, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
        return "Day type unavailable"
    except:
        return "Day type unavailable"


def extract_text(pdf_path):
    text = ""
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""

    return text


def get_today_lunch(text):
    today = datetime.now().day
    index1 = text.find(str(today))
    index2 = text.find(str(today+1))
    indexLast = text.find("Bag")

    if index1 == -1:
        menu = "No lunch found for today"
    elif index2 == -1:
        menu = text[index1:indexLast]
    else:
        menu = text[index1:index2]
    menu = menu.replace(str(today), "")
    return menu


def get_lunch_menu():


    # Re-upload the lunch pdf every month
    LUNCH_PATH = "/home/spackweb/App Code/lunch.pdf"

    pdf_text = extract_text(LUNCH_PATH)
    lunch_today = get_today_lunch(pdf_text)
    return lunch_today

def build_calendar(year, month):
    cal = calendar.Calendar(firstweekday=6)  # Sunday start
    return [[{"day": d.day, "date": d} if d.month == month else None
             for d in week]
             for week in cal.monthdatescalendar(year, month)]

def get_breakfast_menu():
    day = datetime.now().strftime("%A")
    menu = {
        "Monday": "Warm jumbo muffin",
        "Tuesday": "Toasted cheese bagel",
        "Wednesday": "Cereal bowl and string cheese",
        "Thursday": "Whole grain breakfast round",
        "Friday": "Cinnamon toasted bagel"
    }
    return menu.get(day, "No breakfast served today.")

def get_events_from_ics(url):
    response = requests.get(url)
    response.raise_for_status()

    text = response.text
    lines = text.splitlines()
    current_event = None

    events_list = []
    for line in lines:
        line = line.strip()

        if line == "BEGIN:VEVENT":
            current_event = {}

        elif line == "END:VEVENT" and current_event is not None:
            if 'date' in current_event and 'event' in current_event:
                events_list.append(current_event)
            current_event = None
        elif current_event is not None:
            if line.startswith("SUMMARY:"):
                summary = line[len("SUMMARY:"):].strip()
                if summary.startswith(' '):
                    summary = summary[1:]
                current_event['event'] = summary

            elif line.startswith("DTSTART"):

                match = re.search(r':(\d{8})', line)
                if not match:
                    continue
                date_part = match.group(1)

                try:
                    year = int(date_part[0:4])
                    month = int(date_part[4:6])
                    day = int(date_part[6:8])
                    current_event['date'] = date(year, month, day)

                except ValueError:
                    print(f"Skipping event due to bad date values: {date_part}")
                    current_event = None

    return events_list

def get_upcoming_events():
    events = []
    events.extend(get_events_from_ics("https://calendar.google.com/calendar/ical/sufsdny.org_1ngptog7qjb30l6ui6hm5ht3ds%40group.calendar.google.com/public/basic.ics"))
    events.extend(get_events_from_ics("https://calendar.google.com/calendar/ical/sufsdny.org_fh27vfmov68e0adc5dsmodmq3g%40group.calendar.google.com/public/basic.ics"))
    events.extend(get_events_from_ics("https://calendar.google.com/calendar/ical/sufsdny.org_6jlotfuojmgn8lij5d1ipe89i4@group.calendar.google.com/public/basic.ics"))
    return events



def download_spreadsheet(url, output):
    response = requests.get(url)
    response.raise_for_status()
    with open(output, 'wb') as f:
        f.write(response.content)


@app.route('/courses')
def courses():
    """Course Selector page (placeholder)"""
    download_spreadsheet("https://docs.google.com/spreadsheets/d/1uyv8i91GqHdRurJf3JMm1bZxOfQwnRZkRjhpEytvMuc/export?format=csv&gid=0#gid=0", "/home/spackweb/App Code/static/courses.csv")
    return render_template('courses.html')



@app.route('/')
def home():
    """Main page with date, odd/even, lunch, breakfast, and events"""
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    context = {
        'date': get_todays_date(),
        'odd_even': is_odd_or_even_day(),
        'lunch': get_lunch_menu(),
        'breakfast': get_breakfast_menu(),
        'events': get_upcoming_events(),
        'calendar': build_calendar(current_year, current_month)
    }
    return render_template('home.html', **context)





@app.route('/clubs')
def clubs():
    """School Clubs page (placeholder)"""
    return render_template('clubs.html')




if __name__ == '__main__':
    app.run(debug=True)
