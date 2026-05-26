from flask import Flask, render_template, send_from_directory
from datetime import datetime
from datetime import date
import os
import secrets
import requests
import PyPDF2
import re
import calendar
import json


app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', secrets.token_hex(32))

@app.route("/.well-known/<path:filename>")
def well_known(filename):
    return send_from_directory("static/.well-known", filename)

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
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        text = reader.pages[0].extract_text() or ""

    with open("lunch.txt", "w", encoding="utf-8") as file:
        file.write(text)

    return text


def get_today_lunch(text):
    today = datetime.now().day
    pattern = r"\n(\d{1,2})\n(.*?)(?=\n\d{1,2}\n|$)"
    matches = re.findall(pattern, text, re.DOTALL)
    menu_dict = {}
    for day, content in matches:
        menu_dict[int(day)] = content.strip()
    if today not in menu_dict:
        return "No lunch found for today"
    menu = menu_dict[today]
    lines = [
        line.strip()
        for line in menu.splitlines()
        if line.strip()
    ]
    return "\n".join(lines)

def get_lunch_menu():
    LUNCH_PATH = "lunch.pdf"
    now = datetime.now()
    month_name = now.strftime("%B")  
    year = now.year
    if now.month >= 8:
        school_year = f"{year}-{year + 1}"
    else:
        school_year = f"{year - 1}-{year}"
    pdf_name = f"SHS_{month_name}_Menu_Carb_Counter.pdf"
    url = (
        "https://cdnsm5-ss18.sharpschool.com/"
        "UserFiles/Servers/Server_269531/File/"
        f"Departments/Food%20Services/{school_year}/{pdf_name}"
    )
    output_file = LUNCH_PATH
    response = requests.get(url)
    if response.status_code == 200:
        with open(output_file, "wb") as file:
            file.write(response.content)
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

from datetime import datetime, date
import requests
import re

def get_events_from_ics(url):
    response = requests.get(url)
    response.raise_for_status()

    text = response.text
    lines = text.splitlines()
    current_event = None

    now = datetime.now()
    current_year = now.year
    current_month = now.month

    events_list = []

    for line in lines:
        line = line.strip()

        if line == "BEGIN:VEVENT":
            current_event = {}

        elif line == "END:VEVENT" and current_event is not None:
            if 'date' in current_event and 'event' in current_event:
                event_date = current_event['date']

                # FILTER HERE
                if event_date.year == current_year and event_date.month == current_month:
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
    download_spreadsheet("https://docs.google.com/spreadsheets/d/1uyv8i91GqHdRurJf3JMm1bZxOfQwnRZkRjhpEytvMuc/export?format=csv&gid=0#gid=0", "static/courses.csv")
    return render_template('courses.html')

@app.route('/clubs')
def clubs():
    download_spreadsheet("https://docs.google.com/spreadsheets/d/1uyv8i91GqHdRurJf3JMm1bZxOfQwnRZkRjhpEytvMuc/export?format=csv&gid=1463261106#gid=1463261106", "static/clubs.csv")
    return render_template('clubs.html')





CACHE_FILE = "daily_home_cache.json"


def load_cached_context():
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)

        if data.get("date_key") == datetime.now().strftime("%Y-%m-%d"):
            return data.get("context")

    except Exception:
        return None

    return None


def make_json_safe(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_json_safe(i) for i in obj]
    return obj

def save_cached_context(context):
    data = {
        "date_key": datetime.now().strftime("%Y-%m-%d"),
        "context": make_json_safe(context)
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


@app.route('/')
def home():
    """Main page with daily cached context"""
    cached = load_cached_context()
    if cached:
        return render_template("home.html", **cached)

    now = datetime.now()
    current_year = now.year
    current_month = now.month
    month = now.strftime("%B")

    context = {
        'date': get_todays_date(),
        'odd_even': is_odd_or_even_day(),
        'lunch': get_lunch_menu(),
        'breakfast': get_breakfast_menu(),
        'events': get_upcoming_events(),
        'month': month,
        'calendar': build_calendar(current_year, current_month)
    }

    save_cached_context(context)
    return render_template('home.html', **context)



if __name__ == '__main__':
    app.run(debug=True)
