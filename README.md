# AI Resume Screening & Job Matching System

An AI-based Resume Screening and Job Matching System developed using Flask and MySQL.

## Project Overview

This project helps users upload their resumes, extract relevant skills, screen their resumes, and find suitable job opportunities based on skill matching.

The system also provides an admin panel for managing job postings and tracking job applications.

## Features

### User Features
- User Registration
- User Login and Logout
- Secure Password Hashing
- Resume Upload
- PDF Resume Text Extraction
- Resume Skill Extraction
- Resume Screening
- Job Matching with Match Percentage
- Matched and Missing Skills
- Job Details
- Job Application
- My Applications
- Application Status Tracking
- User Profile

### Admin Features
- Admin Registration
- Admin Login and Logout
- Admin Dashboard
- View Job Applications
- Update Application Status
- Add New Jobs
- Manage Jobs
- Delete Jobs

## Technologies Used

- Python
- Flask
- MySQL
- HTML
- CSS
- PyPDF2
- python-dotenv
- Werkzeug Security

## Project Structure

```text
AI-Resume-Job-Matching/
│
├── app.py
├── .gitignore
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── upload_resume.html
│   ├── screening.html
│   ├── jobs.html
│   ├── job_details.html
│   ├── my_applications.html
│   ├── profile.html
│   └── admin/
│
└── uploads/
