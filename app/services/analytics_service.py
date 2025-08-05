from app.models.user import User
from app.models.resource import Resource
from app.models.event import Event
from app.models.mentorship import Mentorship
from app.extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

def get_platform_summary_stats():
    """Get summary statistics for the entire platform."""
    
    # User stats
    total_users = User.query.count()
    total_mentors = User.query.filter_by(is_mentor=True).count()
    new_users_last_30_days = User.query.filter(User.created_at >= datetime.utcnow() - timedelta(days=30)).count()

    # Resource stats
    total_resources = Resource.query.count()
    pending_resources = Resource.query.filter_by(status='pending').count()

    # Event stats
    total_events = Event.query.count()
    upcoming_events = Event.query.filter(Event.date >= datetime.utcnow()).count()

    # Mentorship stats
    active_mentorships = Mentorship.query.count()

    stats = {
        'users': {
            'total': total_users,
            'mentors': total_mentors,
            'new_last_30_days': new_users_last_30_days
        },
        'resources': {
            'total': total_resources,
            'pending': pending_resources
        },
        'events': {
            'total': total_events,
            'upcoming': upcoming_events
        },
        'mentorships': {
            'active_pairings': active_mentorships
        }
    }
    return stats, "Statistics retrieved successfully."

def generate_users_csv():
    """Generate a CSV string of all users."""
    import io
    import csv

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    header = ['ID', 'First Name', 'Last Name', 'Email', 'Matric No', 'Level', 'Is Mentor', 'Is Admin', 'Is Super Admin', 'Is Active', 'Created At']
    writer.writerow(header)

    users = User.query.all()
    for user in users:
        row = [
            user.id,
            user.firstname,
            user.lastname,
            user.email,
            user.matric_no,
            user.current_level,
            user.is_mentor,
            user.is_admin,
            user.is_super_admin,
            user.is_active,
            user.created_at.isoformat()
        ]
        writer.writerow(row)

    return output.getvalue(), "User CSV generated successfully."

def generate_summary_pdf():
    """Generate a PDF report of platform summary statistics."""
    from fpdf import FPDF

    stats, message = get_platform_summary_stats()
    if not stats:
        return None, message

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=24)
    pdf.cell(200, 10, txt="NAPS Platform Analytics Report", ln=True, align='C')

    pdf.set_font("Helvetica", 'B', size=16)
    pdf.cell(200, 10, txt="Summary Statistics", ln=True, align='L')
    pdf.ln(5)

    pdf.set_font("Helvetica", size=12)
    for category, data in stats.items():
        pdf.set_font("Helvetica", 'B', size=14)
        pdf.cell(200, 10, txt=category.title(), ln=True)
        pdf.set_font("Helvetica", size=12)
        for key, value in data.items():
            pdf.cell(200, 8, txt=f"    {key.replace('_', ' ').title()}: {value}", ln=True)
        pdf.ln(5)

    pdf_output = pdf.output(dest='S').encode('latin-1')
    return pdf_output, "PDF report generated successfully."
