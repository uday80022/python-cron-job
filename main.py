import requests
import schedule
import smtplib
import datetime
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
import re
from collections import Counter
import nltk
nltk.download('punkt')

# ===== CONFIGURATION =====
EMAIL_FROM = "your_email@example.com"
EMAIL_TO = "your_email@example.com"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@example.com"
SMTP_PASS = "your_password_or_app_password"

SEARCH_QUERIES = [
    "Python backend engineer AI jobs India remote full time",
    "LLM engineer jobs India remote full time",
    "AI Software engineer jobs India remote",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ===== FUNCTIONS =====

def fetch_links(query):
    """Perform a web search and extract job posting direct links."""
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}+site:linkedin.com/jobs+OR+site:indeed.com"
    resp = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(resp.text, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if href and ("linkedin.com/jobs" in href or "indeed.com" in href):
            direct = re.search(r'https?://[^\s&]+', href)
            if direct:
                links.append(direct.group(0))
    return list(set(links))

def parse_job(url):
    """Fetch job page and extract basic fields."""
    resp = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)[:5000]

    # Simple extraction heuristics (will vary by site)
    title = soup.find("h1")
    title = title.get_text(strip=True) if title else "Job Title"
    location = re.search(r"(India|Remote|Hybrid)", text) or "Remote / India"
    company = re.search(r"([A-Z][A-Za-z]+ (?:Inc|Ltd|LLP|Solutions|Technologies))", text) or "Company"
    job_type = re.search(r"(Full-time|Part-time|Contract|Remote|Hybrid)", text) or "Full-time/Remote"

    return {
        "title": title,
        "company": company.group(0) if hasattr(company, 'group') else company,
        "location": location.group(0) if hasattr(location, 'group') else location,
        "job_type": job_type.group(0),
        "link": url,
        "description": text
    }

def extract_keywords(text):
    """Top 10 word tokens from job text relevant to AI/Backend skills."""
    tokens = nltk.word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalpha()]
    stop = set(nltk.corpus.stopwords.words('english'))
    filtered = [t for t in tokens if t not in stop]
    common = Counter(filtered).most_common(20)
    return [w for w, _ in common[:10]]

def extract_skills(text):
    SKILL_SET = [
        "python","django","fastapi","flask","sql","postgresql","nosql",
        "tensorflow","pytorch","llms","langchain","vector search",
        "ai","ml","nlp","huggingface","docker","kubernetes","aws"
    ]
    found = [skill for skill in SKILL_SET if skill in text.lower()]
    return found[:10]

def send_email(table_html):
    msg = MIMEText(table_html, "html")
    msg["Subject"] = f"Daily Job Report — {datetime.date.today()}"
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)
    server.quit()

def run_daily():
    jobs = []
    for q in SEARCH_QUERIES:
        try:
            for link in fetch_links(q):
                job = parse_job(link)
                job["keywords"] = extract_keywords(job["description"])
                job["skills"] = extract_skills(job["description"])
                jobs.append(job)
        except Exception as e:
            print("fetch error", e)

    # Generate table
    table = "<table border='1'><tr>"
    cols = ["Company","Job Title","Location","Job Type","Direct Link","Top Keywords","Top Skills"]
    for c in cols:
        table += f"<th>{c}</th>"
    table += "</tr>"

    for j in jobs:
        table += "<tr>"
        table += f"<td>{j['company']}</td>"
        table += f"<td>{j['title']}</td>"
        table += f"<td>{j['location']}</td>"
        table += f"<td>{j['job_type']}</td>"
        table += f"<td><a href='{j['link']}'>{j['link']}</a></td>"
        table += f"<td>{', '.join(j['keywords'])}</td>"
        table += f"<td>{', '.join(j['skills'])}</td>"
        table += "</tr>"
    table += "</table>"

    send_email(table)

# ===== SCHEDULE =====
# schedule.every().day.at("09:00").do(run_daily)

if __name__ == "__main__":
    run_daily()
