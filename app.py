from flask import Flask, render_template, request, make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import io
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# RIASEC questions (5 per type)
questions = {
    'R': [
        "I like to work on cars",
        "I like to build things",
        "I like to take care of animals",
        "I like putting things together or assembling things",
        "I like working outdoors"
    ],
    'I': [
        "I like to do puzzles",
        "I like to do experiments",
        "I enjoy science",
        "I like to analyze things (problems/situations)",
        "I'm good at math"
    ],
    'A': [
        "I like to read about art and music",
        "I enjoy creative writing",
        "I am a creative person",
        "I like to play instruments or sing",
        "I like acting in plays"
    ],
    'S': [
        "I like to work in teams",
        "I like to teach or train people",
        "I like trying to help people solve their problems",
        "I am interested in healing people",
        "I like helping people"
    ],
    'E': [
        "I am an ambitious person, I set goals for myself",
        "I like to try to influence or persuade people",
        "I like selling things",
        "I would like to start my own business",
        "I like to give speeches"
    ],
    'C': [
        "I like to organize things (files, desks/offices)",
        "I like to have clear instructions to follow",
        "I wouldn't mind working 8 hours per day in an office",
        "I pay attention to details",
        "I like to do filing or typing"
    ]
}

# Type descriptions
type_descriptions = {
    'R': "Realistic (Doers): You enjoy hands-on work, building, and practical activities.",
    'I': "Investigative (Thinkers): You like solving problems, science, and analytical tasks.",
    'A': "Artistic (Creators): You thrive on creativity, expression, and originality.",
    'S': "Social (Helpers): You enjoy working with people, teaching, and helping others.",
    'E': "Enterprising (Persuaders): You like leading, persuading, and entrepreneurial activities.",
    'C': "Conventional (Organizers): You prefer structured tasks, organization, and details."
}

# Careers with O*NET links (10 per type)
careers = {
    'R': [
        {"title": "Cutters and Trimmers, Hand", "link": "https://www.onetonline.org/link/summary/51-9031.00"},
        {"title": "Derrick Operators, Oil and Gas", "link": "https://www.onetonline.org/link/summary/47-5011.00"},
        {"title": "Fallers", "link": "https://www.onetonline.org/link/summary/45-4021.00"},
        {"title": "Floor Sanders and Finishers", "link": "https://www.onetonline.org/link/summary/47-2043.00"},
        {"title": "Graders and Sorters, Agricultural Products", "link": "https://www.onetonline.org/link/summary/45-2041.00"},
        {"title": "Helpers--Painters, Paperhangers, Plasterers, and Stucco Masons", "link": "https://www.onetonline.org/link/summary/47-3014.00"},
        {"title": "Painting, Coating, and Decorating Workers", "link": "https://www.onetonline.org/link/summary/51-9123.00"},
        {"title": "Pipelayers", "link": "https://www.onetonline.org/link/summary/47-2151.00"},
        {"title": "Pressers, Textile, Garment, and Related Materials", "link": "https://www.onetonline.org/link/summary/51-6021.00"},
        {"title": "Rock Splitters, Quarry", "link": "https://www.onetonline.org/link/summary/47-5051.00"}
    ],
    'I': [
        {"title": "Computer Systems Engineers/Architects", "link": "https://www.onetonline.org/link/summary/15-1299.08"},
        {"title": "Atmospheric and Space Scientists", "link": "https://www.onetonline.org/link/summary/19-2021.00"},
        {"title": "Biofuels/Biodiesel Technology and Product Development Managers", "link": "https://www.onetonline.org/link/summary/11-9041.01"},
        {"title": "Computer Network Architects", "link": "https://www.onetonline.org/link/summary/15-1241.00"},
        {"title": "Conservation Scientists", "link": "https://www.onetonline.org/link/summary/19-1031.00"},
        {"title": "Environmental Engineers", "link": "https://www.onetonline.org/link/summary/17-2081.00"},
        {"title": "Environmental Science and Protection Technicians, Including Health", "link": "https://www.onetonline.org/link/summary/19-4042.00"},
        {"title": "Geographers", "link": "https://www.onetonline.org/link/summary/19-3092.00"},
        {"title": "Health and Safety Engineers, Except Mining Safety Engineers and Inspectors", "link": "https://www.onetonline.org/link/summary/17-2111.00"},
        {"title": "Histotechnologists", "link": "https://www.onetonline.org/link/summary/29-2011.04"}
    ],
    'A': [
        {"title": "Graphic Designers", "link": "https://www.onetonline.org/link/summary/27-1024.00"},
        {"title": "Actors", "link": "https://www.onetonline.org/link/summary/27-2011.00"},
        {"title": "Writers and Authors", "link": "https://www.onetonline.org/link/summary/27-3043.00"},
        {"title": "Musicians and Singers", "link": "https://www.onetonline.org/link/summary/27-2042.00"},
        {"title": "Fine Artists, Including Painters, Sculptors, and Illustrators", "link": "https://www.onetonline.org/link/summary/27-1013.00"},
        {"title": "Photographers", "link": "https://www.onetonline.org/link/summary/27-4021.00"},
        {"title": "Interior Designers", "link": "https://www.onetonline.org/link/summary/27-1025.00"},
        {"title": "Fashion Designers", "link": "https://www.onetonline.org/link/summary/27-1022.00"},
        {"title": "Film and Video Editors", "link": "https://www.onetonline.org/link/summary/27-4032.00"},
        {"title": "Dancers", "link": "https://www.onetonline.org/link/summary/27-2031.00"}
    ],
    'S': [
        {"title": "Career/Technical Education Teachers, Postsecondary", "link": "https://www.onetonline.org/link/summary/25-1194.00"},
        {"title": "Dietetic Technicians", "link": "https://www.onetonline.org/link/summary/29-2051.00"},
        {"title": "Self-Enrichment Teachers", "link": "https://www.onetonline.org/link/summary/25-3021.00"},
        {"title": "Teaching Assistants, Preschool, Elementary, Middle, and Secondary School, Except Special Education", "link": "https://www.onetonline.org/link/summary/25-9042.00"},
        {"title": "Teaching Assistants, Special Education", "link": "https://www.onetonline.org/link/summary/25-9043.00"},
        {"title": "Tutors", "link": "https://www.onetonline.org/link/summary/25-3041.00"},
        {"title": "Adult Basic Education, Adult Secondary Education, and English as a Second Language Instructors", "link": "https://www.onetonline.org/link/summary/25-3011.00"},
        {"title": "Career/Technical Education Teachers, Middle School", "link": "https://www.onetonline.org/link/summary/25-2023.00"},
        {"title": "Kindergarten Teachers, Except Special Education", "link": "https://www.onetonline.org/link/summary/25-2012.00"},
        {"title": "Rehabilitation Counselors", "link": "https://www.onetonline.org/link/summary/21-1015.00"}
    ],
    'E': [
        {"title": "First-Line Supervisors of Construction Trades and Extraction Workers", "link": "https://www.onetonline.org/link/summary/47-1011.00"},
        {"title": "First-Line Supervisors of Correctional Officers", "link": "https://www.onetonline.org/link/summary/33-1011.00"},
        {"title": "First-Line Supervisors of Farming, Fishing, and Forestry Workers", "link": "https://www.onetonline.org/link/summary/45-1011.00"},
        {"title": "First-Line Supervisors of Landscaping, Lawn Service, and Groundskeeping Workers", "link": "https://www.onetonline.org/link/summary/37-1012.00"},
        {"title": "First-Line Supervisors of Mechanics, Installers, and Repairers", "link": "https://www.onetonline.org/link/summary/49-1011.00"},
        {"title": "First-Line Supervisors of Production and Operating Workers", "link": "https://www.onetonline.org/link/summary/51-1011.00"},
        {"title": "Wholesale and Retail Buyers, Except Farm Products", "link": "https://www.onetonline.org/link/summary/13-1022.00"},
        {"title": "Advertising and Promotions Managers", "link": "https://www.onetonline.org/link/summary/11-2011.00"},
        {"title": "Advertising Sales Agents", "link": "https://www.onetonline.org/link/summary/41-3011.00"},
        {"title": "Biofuels Production Managers", "link": "https://www.onetonline.org/link/summary/11-3051.03"}
    ],
    'C': [
        {"title": "Bill and Account Collectors", "link": "https://www.onetonline.org/link/summary/43-3011.00"},
        {"title": "Correspondence Clerks", "link": "https://www.onetonline.org/link/summary/43-4021.00"},
        {"title": "Counter and Rental Clerks", "link": "https://www.onetonline.org/link/summary/41-2021.00"},
        {"title": "Couriers and Messengers", "link": "https://www.onetonline.org/link/summary/43-5021.00"},
        {"title": "Court, Municipal, and License Clerks", "link": "https://www.onetonline.org/link/summary/43-4031.00"},
        {"title": "Credit Authorizers, Checkers, and Clerks", "link": "https://www.onetonline.org/link/summary/43-4041.00"},
        {"title": "Data Entry Keyers", "link": "https://www.onetonline.org/link/summary/43-9021.00"},
        {"title": "Dispatchers, Except Police, Fire, and Ambulance", "link": "https://www.onetonline.org/link/summary/43-5032.00"},
        {"title": "File Clerks", "link": "https://www.onetonline.org/link/summary/43-4071.00"},
        {"title": "Gambling and Sports Book Writers and Runners", "link": "https://www.onetonline.org/link/summary/39-3012.00"}
    ]
}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
        
        # Calculate scores
        for typ in questions:
            for i in range(5):
                key = f"{typ}_{i}"
                scores[typ] += int(request.form.get(key, 0))
        
        # Get top 3 types
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_types = [t[0] for t in sorted_scores]
        
        # Generate PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        y = height - inch
        
        p.drawString(inch, y, "RIASEC Career Assessment Analysis")
        y -= 0.5 * inch
        p.drawString(inch, y, f"Email: {email}")
        y -= 0.5 * inch
        p.drawString(inch, y, "Scores:")
        y -= 0.25 * inch
        for typ, score in scores.items():
            p.drawString(inch, y, f"{typ} ({type_descriptions[typ].split(':')[0]}): {score}/25")
            y -= 0.25 * inch
        
        y -= 0.5 * inch
        p.drawString(inch, y, "Top Types and Career Advice:")
        y -= 0.25 * inch
        for typ in top_types:
            p.drawString(inch, y, type_descriptions[typ])
            y -= 0.25 * inch
            p.drawString(inch, y, "Recommended Careers:")
            y -= 0.25 * inch
            for career in careers[typ]:
                p.drawString(1.25 * inch, y, f"- {career['title']} ({career['link']})")
                y -= 0.25 * inch
            y -= 0.25 * inch
        
        p.save()
        buffer.seek(0)
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = os.getenv('EMAIL_SENDER')
        msg['To'] = email
        msg['Subject'] = "Your RIASEC Career Assessment Results"
        msg.attach(MIMEText("Attached is your career analysis PDF."))
        pdf_attach = MIMEApplication(buffer.read(), _subtype="pdf")
        pdf_attach.add_header('Content-Disposition', 'attachment', filename="riasec_analysis.pdf")
        msg.attach(pdf_attach)
        
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_SENDER'), os.getenv('EMAIL_PASSWORD'))
            server.sendmail(os.getenv('EMAIL_SENDER'), email, msg.as_string())
        
        return "Analysis sent to your email!"
    
    # Flatten questions for form
    flat_questions = []
    for typ in ['R', 'I', 'A', 'S', 'E', 'C']:
        for i, q in enumerate(questions[typ]):
            flat_questions.append({'id': f"{typ}_{i}", 'text': q})
    
    return render_template('index.html', questions=flat_questions)

if __name__ == '__main__':
    app.run(debug=True)
