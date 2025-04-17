#import dependencies
import requests
import random
import sqlite3
from bs4 import BeautifulSoup as bs
import time
from flask import Flask, render_template,request, url_for, redirect,session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy



app= Flask(__name__)
app.secret_key="secretkey"

#SQlAlchemy configure
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
db = SQLAlchemy(app)

#database model
class User(db.Model):
    id=db.Column(db.Integer, primary_key =True)
    username=db.Column(db.String(25), unique=True, nullable=False)
    password_hash=db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    full_name = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    nationality = db.Column(db.String(50))
    address = db.Column(db.String(200))
    state = db.Column(db.String(50))
    email = db.Column(db.String(100))
    category = db.Column(db.String(20))
    income = db.Column(db.String(20))
    parent_occupation = db.Column(db.String(100))
    disability = db.Column(db.String(100))
    contact = db.Column(db.String(15))
    education_level = db.Column(db.String(100))
    institution = db.Column(db.String(100))
    board = db.Column(db.String(100))
    passing_year = db.Column(db.String(10))
    score_10 = db.Column(db.String(10))
    score_12 = db.Column(db.String(10))
    score_ug = db.Column(db.String(10))
    score_pg = db.Column(db.String(10))
    current_cgpa = db.Column(db.String(10))

    user = db.relationship("User", backref="profile")



#routing
@app.route('/')
def home():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    if not user:
        return redirect(url_for('login'))

    profile_data = UserProfile.query.filter_by(user_id=user.id).first()

    if not profile_data:
        return redirect(url_for('form'))  # Or show a message that profile isn't complete

    profile = {
        "full_name": profile_data.full_name,
        "dob": profile_data.dob,
        "gender": profile_data.gender,
        "nationality": profile_data.nationality,
        "address": profile_data.address,
        "state": profile_data.state,
        "email": profile_data.email,
        "category": profile_data.category,
        "income": profile_data.income,
        "disability": profile_data.disability,
        "contact": profile_data.contact,
        "education_level": profile_data.education_level,
        "institution": profile_data.institution,
        "board": profile_data.board,
        "passing_year": profile_data.passing_year,
        "score_10": profile_data.score_10,
        "score_12": profile_data.score_12,
        "score_ug": profile_data.score_ug,
        "score_pg": profile_data.score_pg,
        "current_cgpa": profile_data.current_cgpa,
        "parent_occupation": profile_data.parent_occupation
    }

    # Fetch all scholarships (using sqlite3 for now, which is okay here if data is already stored)
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scholarships")
    all_scholarships = cursor.fetchall()
    conn.close()

    eligible_scholarships = []
    for s in all_scholarships:
        title, overview, eligibility, how_to_apply = s[1], s[2], s[3], s[4]
        if not eligibility:
            continue

        e_lower = eligibility.lower()
        matched = (
            profile['category'].lower() in e_lower or
            profile['gender'].lower() in e_lower or
            profile['education_level'].lower() in e_lower or
            str(profile['disability']).lower() in e_lower or
            str(profile['income']) in e_lower
        )
        if matched:
            eligible_scholarships.append({
                "title": title,
                "overview": overview,
                "eligibility": eligibility,
                "how_to_apply": how_to_apply
            })

    return render_template("dashboard.html", profile=profile, scholarships=eligible_scholarships)


    # Fetch all scholarships
    cursor.execute("SELECT * FROM scholarships")
    all_scholarships = cursor.fetchall()

    # Filter based on simple matching rules
    eligible_scholarships = []
    for s in all_scholarships:
        title, overview, eligibility, how_to_apply = s[1], s[2], s[3], s[4]
        if not eligibility:
            continue

        # Convert all to lowercase for matching
        e_lower = eligibility.lower()
        matched = (
            profile['category'].lower() in e_lower or
            profile['gender'].lower() in e_lower or
            profile['education_level'].lower() in e_lower or
            str(profile['disability']).lower() in e_lower or
            str(profile['income']) in e_lower
        )
        if matched:
            eligible_scholarships.append({
                "title": title,
                "overview": overview,
                "eligibility": eligibility,
                "how_to_apply": how_to_apply
            })

    return render_template("dashboard.html", profile=profile, scholarships=eligible_scholarships)



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user:
            return render_template("register.html", error="User already registered")
        else:
            new_user = User(username=username)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect(url_for('form'))
    
    return render_template("register.html")




@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))



@app.route("/form", methods=["GET", "POST"])
def form():
    if "username" not in session:
        return redirect(url_for('home'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == "POST":
        profile = UserProfile(
            user_id=user.id,
            full_name=request.form.get("full_name"),
            dob=request.form.get("dob"),
            gender=request.form.get("gender"),
            nationality=request.form.get("nationality"),
            address=request.form.get("address"),
            state=request.form.get("state"),
            email=request.form.get("email"),
            category=request.form.get("category"),
            income=request.form.get("income"),
            parent_occupation=request.form.get("parent_occupation"),
            disability=request.form.get("disability"),
            contact=request.form.get("contact"),
            education_level=request.form.get("education_level"),
            institution=request.form.get("institution"),
            board=request.form.get("board"),
            passing_year=request.form.get("passing_year"),
            score_10=request.form.get("score_10"),
            score_12=request.form.get("score_12"),
            score_ug=request.form.get("score_ug"),
            score_pg=request.form.get("score_pg"),
            current_cgpa=request.form.get("current_cgpa")
        )
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('dashboard'))
    print(request.form)


    return render_template("form.html", username=session['username'])



@app.route("/profile")
def profile():
    if "username" not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    profile_data = UserProfile.query.filter_by(user_id=user.id).first()

    return render_template("profile.html", user=user, profile=profile_data)



urls_title = [
    'https://scholarshipforme.com/scholarships?state=State&qualification=&category=sc_st_obc&origin=&type=&availability=&form_botcheck=',
    'https://scholarshipforme.com/scholarships?state=State&qualification=&category=girls&origin=&type=&availability=&form_botcheck=',
    'https://scholarshipforme.com/scholarships?state=State&qualification=&category=obc&origin=&type=&availability=&form_botcheck=',
]

details_part1 = [
    'https://scholarshipforme.com/scholarships/the-education-future-international-scholarship',
    'https://scholarshipforme.com/scholarships/national-scholarship-for-higher-education-of-st-students',
    'https://scholarshipforme.com/scholarships/ugc-national-fellowship-for-scheduled-caste-students-nfsc-',
    'https://scholarshipforme.com/scholarships/national-fellowship-and-scholarship-for-higher-education-of-st-students',
    'https://scholarshipforme.com/scholarships/tata-housing-scholarships-for-meritorious-girl-students',
    'https://scholarshipforme.com/scholarships/national-scheme-of-incentive-to-girls-for-secondary-education-nsigse-',
    'https://scholarshipforme.com/scholarships/central-sector-scheme-of-scholarship-for-college-and-university-students2167',
    'https://scholarshipforme.com/scholarships/post-graduate-scholarship-for-professional-courses-for-sc-st-students',
    'https://scholarshipforme.com/scholarships/top-class-education-scheme-for-sc-students',
    'https://scholarshipforme.com/scholarships/-life-s-good-scholarship-program-2024',
]

details_part2 = [
    'https://scholarshipforme.com/scholarships/the-education-future-international-scholarship',
    'https://scholarshipforme.com/scholarships/dxc-progressing-minds-scholarship-2023-24',
    'https://scholarshipforme.com/scholarships/fuel-business-school-csr-scholarship-2023-24',
    'https://scholarshipforme.com/scholarships/aauw-international-fellowship-2023',
    'https://scholarshipforme.com/scholarships/amazon-future-engineer-scholarship',
    'https://scholarshipforme.com/scholarships/u-go-scholarship-programme',
    'https://scholarshipforme.com/scholarships/women-scientist-scheme-c-wos-c-',
    'https://scholarshipforme.com/scholarships/indira-gandhi-scholarship-for-single-girl',
    'https://scholarshipforme.com/scholarships/cbse-single-girl-child-scholarship',
    'https://scholarshipforme.com/scholarships/clinic-plus-scholarship',
    
]

details_part3 = [
    'https://scholarshipforme.com/scholarships/the-education-future-international-scholarship',
    'https://scholarshipforme.com/scholarships/-life-s-good-scholarship-program-2024',
     'https://scholarshipforme.com/scholarships/dr-a-p-j-abdul-kalam-ignite',
     'https://scholarshipforme.com/scholarships/clp-india-this-scholarship',
     'https://scholarshipforme.com/scholarships/drdo-itr-chandipur-graduate-technician-diploma-apprenticeship-2023',
     'https://scholarshipforme.com/scholarships/the-medhaavi-engineering-scholarship-program-2023-24',
     'https://scholarshipforme.com/scholarships/empowerment-and-equity-opportunities-for-excellence-in-science',
     'https://scholarshipforme.com/scholarships/h-h-dalai-lama-sasakawa-scholarship',
     'https://scholarshipforme.com/scholarships/aicte-civil-engineering-internship-cei-9214',
     'https://scholarshipforme.com/scholarships/university-of-southampton---great-scholarships',
]

urls_details = details_part1 + details_part2 + details_part3

# -------------------------------
# 2. SQLite DB Setup
# -------------------------------
conn = sqlite3.connect('users.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS scholarships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    overview TEXT,
    eligibility_criteria TEXT,
    how_to_apply TEXT
)
''')
conn.commit()

# -------------------------------
# 3. Random Header Fetcher
# -------------------------------
def fetch_page(url):
    headers = {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Mozilla/5.0 (X11; Linux x86_64)',
        ])
    }
    try:
        print(f"🔍 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"❌ Status Code {response.status_code} for URL: {url}")
    except Exception as e:
        print(f"🚫 Failed to fetch {url}: {e}")
    return None

# -------------------------------
# 4. Parse Titles (h4 inside .job-content)
# -------------------------------
def parse_titles(html):
    soup = bs(html, 'html.parser')
    titles = []
    for section in soup.find_all("div", class_="job-content"):
        h4 = section.find("h4")
        if h4:
            titles.append(h4.get_text(strip=True))
    return titles

# -------------------------------
# 5. Parse Details
# -------------------------------
def parse_details(html):
    soup = bs(html, 'html.parser')

    # Overview from <ul class="job-overview"><li>
    overview_list = soup.select("ul.job-overview li")
    overview_text = "\n".join([li.get_text(strip=True) for li in overview_list])

    # Eligibility from <ul> inside <article class="scholarshipDetails_sectionBox__2cUvO">
    eligibility_text = ""
    article = soup.find("article", class_="scholarshipDetails_sectionBox__2cUvO")
    if article:
        ul_tag = article.find("ul")
        if ul_tag:
            eligibility_text = "\n".join([li.get_text(strip=True) for li in ul_tag.find_all("li")])

    # How to Apply from last <p> in <div class="job-details-body">
    apply_text = ""
    job_details_div = soup.find("div", class_="job-details-body")
    if job_details_div:
        p_tags = job_details_div.find_all("p")
        if p_tags:
            apply_text = p_tags[-1].get_text(strip=True)

    return overview_text, eligibility_text, apply_text

# -------------------------------
# 6. Insert Titles into DB
# -------------------------------
# 6. Insert up to 30 Titles into DB
total_titles_inserted = 0
max_entries = 30
titles_collected = []

for url in urls_title:
    if total_titles_inserted >= max_entries:
        break
    html = fetch_page(url)
    if html:
        titles = parse_titles(html)
        for title in titles:
            if total_titles_inserted < max_entries:
                cursor.execute("INSERT INTO scholarships (title) VALUES (?)", (title,))
                titles_collected.append(title)
                total_titles_inserted += 1
            else:
                break
    time.sleep(random.uniform(1, 2))

conn.commit()
print(f"✅ Inserted {total_titles_inserted} titles.\n")

# 7. Update Details only for the first 30 detail URLs
for index, url in enumerate(urls_details[:max_entries]):
    html = fetch_page(url)
    if html:
        overview, eligibility, apply = parse_details(html)
        cursor.execute('''
            UPDATE scholarships
            SET overview = ?, eligibility_criteria = ?, how_to_apply = ?
            WHERE id = ?
        ''', (overview, eligibility, apply, index + 1))
        conn.commit()
    time.sleep(random.uniform(1, 2))


conn.commit()
print(f"✅ Inserted {total_titles_inserted} titles.\n")

# -------------------------------
# 7. Update Details into DB by ID
# -------------------------------
for index, url in enumerate(urls_details):
    html = fetch_page(url)
    if html:
        overview, eligibility, apply = parse_details(html)
        cursor.execute('''
            UPDATE scholarships
            SET overview = ?, eligibility_criteria = ?, how_to_apply = ?
            WHERE id = ?
        ''', (overview, eligibility, apply, index + 1))
        conn.commit()
    time.sleep(random.uniform(1, 2))

print("✅ All detail data updated successfully.")

# -------------------------------
# 8. Optional: Show Results
# -------------------------------
cursor.execute("SELECT * FROM scholarships")
for row in cursor.fetchall():
    print(row)

conn.close()



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)