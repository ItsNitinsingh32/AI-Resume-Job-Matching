from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

# =========================
# Skills List
# =========================

SKILLS = [
    "python",
    "java",
    "kotlin",
    "c++",
    "c#",
    "javascript",
    "html",
    "css",
    "sql",
    "mysql",
    "flask",
    "django",
    "react",
    "android",
    "android sdk",
    "jetpack compose",
    "firebase",
    "git",
    "github",
    "gitlab",
    "docker",
    "aws",
    "machine learning",
    "artificial intelligence",
    "ai",
    "data science",
    "pandas",
    "numpy",
    "tensorflow",
    "pytorch",
]
# =========================
# Resume Skills Extraction
# =========================

def extract_skills(text):

    text = text.lower()

    found_skills = []

    for skill in SKILLS:

        if skill in text:
            found_skills.append(skill)

    return found_skills
app = Flask(__name__)
# =========================
# Job Matching Function
# =========================
def calculate_match(resume_skills, required_skills):

    resume_skills = [
        skill.lower().strip()
        for skill in resume_skills
    ]

    required_skills = [
        skill.lower().strip()
        for skill in required_skills.split(",")
    ]

    matched_skills = []
    missing_skills = []

    for skill in required_skills:

        if skill in resume_skills:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    if len(required_skills) == 0:
        match_percentage = 0
    else:
        match_percentage = (
            len(matched_skills) / len(required_skills)
        ) * 100

    return matched_skills, missing_skills, match_percentage
# Session ke liye secret key
app.secret_key = os.getenv("SECRET_KEY")


# =========================
# MySQL Database Connection
# =========================
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


# =========================
# Resume Upload Settings
# =========================

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# Upload folder automatically create karna
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# File extension check karna
def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
# =========================
# PDF Resume Text Extraction
# =========================
def extract_pdf_text(filepath):

    text = ""

    reader = PdfReader(filepath)

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text

# =========================
# Home Page
# =========================
@app.route("/")
def home():

    return render_template("index.html")


# =========================
# Registration Page
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():

    # Registration page open karna
    if request.method == "GET":
        return render_template("register.html")

    # Form se data lena
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    # Password match check
    if password != confirm_password:
        return "Passwords do not match!"

    # Database cursor
    cursor = db.cursor()

    # Check email already registered hai ya nahi
    cursor.execute(
        "SELECT id FROM users WHERE email = %s",
        (email,)
    )

    existing_user = cursor.fetchone()

    if existing_user:

        cursor.close()

        return render_template("email_exists.html")

    # Password ko hash karna
    hashed_password = generate_password_hash(password)

    # User ko database mein insert karna
    cursor.execute(
        """
        INSERT INTO users (name, email, password)
        VALUES (%s, %s, %s)
        """,
        (name, email, hashed_password)
    )

    db.commit()

    cursor.close()

    return render_template("registration_success.html")

@app.route("/admin_register", methods=["GET", "POST"])
def admin_register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        cursor = db.cursor()

        cursor.execute(
            """
            INSERT INTO admins (name, email, password)
            VALUES (%s, %s, %s)
            """,
            (name, email, hashed_password)
        )

        db.commit()
        cursor.close()

        return "Admin registered successfully!"

    return render_template("admin_register.html")
   
# =========================
# Admin Login
# =========================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "GET":
        return render_template("admin_login.html")

    email = request.form["email"]
    password = request.form["password"]

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, name, email, password
        FROM admins
        WHERE email = %s
        """,
        (email,)
    )

    admin = cursor.fetchone()

    cursor.close()

    if not admin:
        return "Invalid admin email or password!"

    if not check_password_hash(admin[3], password):
        return "Invalid admin email or password!"

    session["admin_id"] = admin[0]
    session["admin_name"] = admin[1]
    session["admin_email"] = admin[2]

    return "Admin login successful!"
# =========================
# Admin Dashboard
# =========================

@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    return render_template("admin_dashboard.html")    

# =========================
# Admin - View Applications
# =========================

@app.route("/admin_applications")
def admin_applications():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor = db.cursor()

    cursor.execute(
        """
     SELECT
        job_applications.id,
        users.name,
        users.email,
        jobs.title,
        jobs.company,
        job_applications.applied_at,
        job_applications.status
        FROM job_applications
        JOIN users
            ON job_applications.user_id = users.id
        JOIN jobs
            ON job_applications.job_id = jobs.id
        ORDER BY job_applications.applied_at DESC
        """
    )

    applications = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_applications.html",
        applications=applications
    )

# =========================
# Admin - Update Application Status
# =========================

@app.route("/admin_update_status/<int:application_id>", methods=["POST"])
def admin_update_status(application_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    status = request.form["status"]

    allowed_statuses = [
        "Applied",
        "Shortlisted",
        "Rejected",
        "Selected"
    ]

    if status not in allowed_statuses:
        return "Invalid application status!"

    cursor = db.cursor()

    cursor.execute(
        """
        UPDATE job_applications
        SET status = %s
        WHERE id = %s
        """,
        (status, application_id)
    )

    db.commit()
    cursor.close()

    return redirect(url_for("admin_applications"))

# =========================
# Login Page
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    # Login page open karna
    if request.method == "GET":
        return render_template("login.html")

    # Login form se data lena
    email = request.form["email"]
    password = request.form["password"]

    # Database cursor
    cursor = db.cursor()

    # Email ke basis par user search karna
    cursor.execute(
        "SELECT id, name, email, password FROM users WHERE email = %s",
        (email,)
    )

    user = cursor.fetchone()

    cursor.close()

    # User nahi mila
    if not user:

         return render_template("login_error.html")

    # Password verify karna
    if not check_password_hash(user[3], password):

         return render_template("login_error.html")

    # User information session mein store karna
    session["user_id"] = user[0]
    session["user_name"] = user[1]
    session["user_email"] = user[2]

    # Successful login ke baad Dashboard par jana
    return redirect(url_for("dashboard"))


# =========================
# Dashboard Page
# =========================
@app.route("/dashboard")
def dashboard():

    # Check user login hai ya nahi
    if "user_id" not in session:

        return redirect(url_for("login"))

    # Database cursor
    cursor = db.cursor()

    # Logged-in user ke resumes database se lana
    cursor.execute(
        """
        SELECT id, filename, filepath, uploaded_at
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        """,
        (session["user_id"],)
    )

    resumes = cursor.fetchall()

    cursor.close()

    # Dashboard ko resumes data bhejna
    return render_template(
        "dashboard.html",
        resumes=resumes
    )
# =========================
# Profile
# =========================
@app.route("/profile")
def profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT name, email, created_at
        FROM users
        WHERE id = %s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    cursor.close()

    return render_template("profile.html", user=user)

# =========================
# Logout
# =========================
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

# =========================
# Upload Resume Page
# =========================
@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "GET":
        return render_template("upload_resume.html")

    if "resume" not in request.files:
        return "No resume file selected!"

    file = request.files["resume"]

    if file.filename == "":
        return "No resume file selected!"

    if not allowed_file(file.filename):
        return "Only PDF, DOC and DOCX files are allowed!"

    filename = secure_filename(file.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(filepath)

    # PDF se text extract karna
    resume_text = ""

    if filename.lower().endswith(".pdf"):

        resume_text = extract_pdf_text(filepath)

        print("\n================ RESUME TEXT ================\n")
        print(resume_text)
        print("\n==============================================\n")

        # Resume se skills extract karna
        found_skills = extract_skills(resume_text)

        print("\n================ FOUND SKILLS ================\n")
        print(found_skills)
        print("\n===============================================\n")

    # Database mein resume save karna
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO resumes (user_id, filename, filepath)
        VALUES (%s, %s, %s)
        """,
        (
            session["user_id"],
            filename,
            filepath
        )
    )

    db.commit()
    cursor.close()

    return redirect(url_for("screening"))

# =========================
# Jobs Page
# =========================
@app.route("/jobs")
def jobs():

    if "user_id" not in session:
        return redirect(url_for("login"))

    # Current user ka latest resume nikalna
    cursor = db.cursor()

    cursor.execute(
        """
        SELECT filepath
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    # Agar resume upload nahi kiya hai
    if not resume:
        cursor.close()
        return "Please upload a resume first!"

    resume_filepath = resume[0]

    # Resume se text extract karna
    resume_text = extract_pdf_text(resume_filepath)

    # Resume se skills extract karna
    resume_skills = extract_skills(resume_text)

    # Saare jobs nikalna
    cursor.execute(
        """
        SELECT id, title, company, required_skills, description
        FROM jobs
        ORDER BY created_at DESC
        """
    )

    jobs_data = cursor.fetchall()

    cursor.close()

    # Har job ka matching percentage calculate karna
    matched_jobs = []

    for job in jobs_data:

        matched_skills, missing_skills, match_percentage = calculate_match(
            resume_skills,
            job[3]
        )

        matched_jobs.append(
            (
                job[0],
                job[1],
                job[2],
                job[3],
                job[4],
                matched_skills,
                missing_skills,
                match_percentage
            )
        )
    # Match percentage ke according jobs sort karna
    matched_jobs.sort(key=lambda job: job[7], reverse=True)    

    return render_template(
        "jobs.html",
        jobs=matched_jobs
    ) 
    
# =========================
# Job Details
# =========================
@app.route("/job/<int:job_id>")
def job_details(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, title, company, required_skills, description
        FROM jobs
        WHERE id = %s
        """,
        (job_id,)
    )

    job = cursor.fetchone()

    cursor.close()

    if not job:
        return "Job not found!"

    return render_template(
        "job_details.html",
        job=job
    )

# =========================
# Apply for Job
# =========================
@app.route("/apply/<int:job_id>")
def apply_job(job_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    # Check job exists
    cursor.execute(
        "SELECT id FROM jobs WHERE id = %s",
        (job_id,)
    )

    job = cursor.fetchone()

    if not job:
        cursor.close()
        return "Job not found!"

    # Check user already applied or not
    cursor.execute(
        """
        SELECT id
        FROM job_applications
        WHERE user_id = %s AND job_id = %s
        """,
        (
            session["user_id"],
            job_id
        )
    )

    existing_application = cursor.fetchone()

    if existing_application:
        cursor.close()
        return "You have already applied for this job!"

    # Save application
    cursor.execute(
        """
        INSERT INTO job_applications (user_id, job_id)
        VALUES (%s, %s)
        """,
        (
            session["user_id"],
            job_id
        )
    )

    db.commit()

    cursor.close()

    return render_template("application_success.html")

# =========================
# Admin - Manage Jobs
# =========================

@app.route("/admin_jobs")
def admin_jobs():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT id, title, company, required_skills, description
        FROM jobs
        ORDER BY created_at DESC
        """
    )

    jobs_data = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_jobs.html",
        jobs=jobs_data
    )
   
# =========================
# My Applications
# =========================
@app.route("/my_applications")
def my_applications():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT
            job_applications.id,
            jobs.title,
            jobs.company,
            job_applications.applied_at,
            job_applications.status
        FROM job_applications
        JOIN jobs
            ON job_applications.job_id = jobs.id
        WHERE job_applications.user_id = %s
        ORDER BY job_applications.applied_at DESC
        """,
        (session["user_id"],)
    )

    applications = cursor.fetchall()

    cursor.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )
# =========================
# Resume Screening Result
# =========================
@app.route("/screening")
def screening():

    if "user_id" not in session:
        return redirect(url_for("login"))

    cursor = db.cursor()

    cursor.execute(
        """
        SELECT filename, filepath
        FROM resumes
        WHERE user_id = %s
        ORDER BY uploaded_at DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    resume = cursor.fetchone()

    if not resume:
        cursor.close()
        return "Please upload a resume first!"

    filename = resume[0]
    resume_filepath = resume[1]

    # Resume se text extract karna
    resume_text = extract_pdf_text(resume_filepath)

    # Resume se skills extract karna
    resume_skills = extract_skills(resume_text)

    cursor.close()

    return render_template(
        "screening.html",
        filename=filename,
        skills=resume_skills
    )
 
# =========================
# Admin - Add New Job
# =========================

@app.route("/admin_add_job", methods=["GET", "POST"])
def admin_add_job():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "GET":
        return render_template("admin_add_job.html")

    title = request.form["title"]
    company = request.form["company"]
    required_skills = request.form["required_skills"]
    description = request.form["description"]

    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO jobs
        (title, company, required_skills, description)
        VALUES (%s, %s, %s, %s)
        """,
        (
            title,
            company,
            required_skills,
            description
        )
    )

    db.commit()

    cursor.close()

    return redirect(url_for("admin_jobs"))

# =========================
# Admin - Delete Job
# =========================

@app.route("/admin_delete_job/<int:job_id>")
def admin_delete_job(job_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM jobs
        WHERE id = %s
        """,
        (job_id,)
    )

    db.commit()

    cursor.close()

    return redirect(url_for("admin_jobs"))    

# =========================
# Admin - Logout
# =========================

@app.route("/admin_logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_name", None)
    session.pop("admin_email", None)

    return redirect(url_for("admin_login"))

@app.errorhandler(404)
def page_not_found(error):
    return "Page not found! Please check the URL.", 404

@app.errorhandler(500)
def internal_server_error(error):
    return "Something went wrong on the server. Please try again later.", 500
    
# =========================
# Run Flask Application
# =========================
if __name__ == "__main__":

    app.run(debug=False)
