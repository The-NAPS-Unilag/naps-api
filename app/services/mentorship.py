from app.models.mentorship import MentorshipApplication, MentorApplication, Mentorship, MentorshipSession, MentorshipFeedback
from app.models.user import User
from app.extensions import db
from app.services.notification_service import send_email
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from flask_mail import Message
from app import mail

class MentorshipService:
    # --- Mentee Application Services ---
    @staticmethod
    def apply_for_mentorship(student_id, student_name, matric_no, level, areas_of_interest):
        """Create a mentee mentorship application."""
        try:
            application = MentorshipApplication(
                student_id=student_id,
                matric_no=matric_no,
                level=level,
                areas_of_interest=areas_of_interest
            )
            db.session.add(application)
            db.session.commit()
            return application
        except SQLAlchemyError:
            db.session.rollback()
            raise

    @staticmethod
    def apply_to_be_mentor(
        applicant_id,
        applicant_name,
        applicant_email,
        phone_no,
        academic_background,
        area_of_expertise,
        preferred_mode,
        areas_of_interest=None
    ):
        """Create a mentor application."""
        try:
            application = MentorApplication(
                applicant_id=applicant_id,
                phone_no=phone_no,
                academic_background=academic_background,
                area_of_expertise=area_of_expertise,
                areas_of_interest=areas_of_interest,
                preferred_mode=preferred_mode
            )
            db.session.add(application)
            db.session.commit()
            return application, "Mentor application submitted successfully."
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}"

    @staticmethod
    def get_all_mentee_applications(status=None):
        """Get all mentee applications, filterable by status."""
        query = MentorshipApplication.query
        if status:
            query = query.filter_by(status=status)
        return query.all()

    @staticmethod
    def approve_mentee_application(application_id):
        """Approve a mentee application."""
        application = MentorshipApplication.query.get(application_id)
        if not application:
            return None, "Application not found."
        if application.status != 'pending':
            return None, f"Application is already {application.status}."

        try:
            application.status = 'approved'
            db.session.commit()
            # Notify applicant
            subject = "Your Mentee Application has been Approved!"
            html_body = f"<p>Hi {application.student.firstname},</p><p>Your application to become a mentee has been approved. You can now be matched with a mentor.</p>"
            send_email(subject, [application.student.email], html_body)
            return application, "Mentee application approved."
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}"

    @staticmethod
    def reject_mentee_application(application_id):
        """Reject a mentee application."""
        application = MentorshipApplication.query.get(application_id)
        if not application:
            return None, "Application not found."
        if application.status != 'pending':
            return None, f"Application is already {application.status}."

        try:
            application.status = 'rejected'
            db.session.commit()
            # Notify applicant
            subject = "Update on Your Mentee Application"
            html_body = f"<p>Hi {application.student.firstname},</p><p>Thank you for your interest. After careful review, we are unable to approve your mentee application at this time.</p>"
            send_email(subject, [application.student.email], html_body)
            return application, "Mentee application rejected."
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}"

    # --- Mentor Application Services ---
    @staticmethod
    def get_all_mentor_applications(status=None):
        """Get all mentor applications, filterable by status."""
        query = MentorApplication.query
        if status:
            query = query.filter_by(status=status)
        return query.all()

    # --- Mentorship Pairing Service ---
    @staticmethod
    def create_mentorship_pairing(mentor_id, mentee_id):
        """Create a mentorship pairing between a mentor and a mentee."""
        mentor = User.query.filter_by(id=mentor_id, is_mentor=True).first()
        if not mentor:
            return None, "Mentor not found or user is not a mentor."

        mentee = User.query.get(mentee_id)
        if not mentee:
            return None, "Mentee not found."

        # Check if mentee has an approved application
        mentee_application = MentorshipApplication.query.filter_by(student_id=mentee_id, status='approved').first()
        if not mentee_application:
            return None, "Mentee does not have an approved application."

        try:
            mentorship = Mentorship(mentor_id=mentor_id, mentee_id=mentee_id)
            db.session.add(mentorship)
            db.session.commit()

            # Notify both users
            mentor_subject = "You have a new Mentee!"
            mentor_body = f"<p>Hi {mentor.firstname},</p><p>You have been paired with a new mentee, {mentee.firstname} {mentee.lastname}.</p>"
            send_email(mentor_subject, [mentor.email], mentor_body)

            mentee_subject = "You have a new Mentor!"
            mentee_body = f"<p>Hi {mentee.firstname},</p><p>You have been paired with a new mentor, {mentor.firstname} {mentor.lastname}.</p>"
            send_email(mentee_subject, [mentee.email], mentee_body)

            return mentorship, "Mentorship pairing created successfully."
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error: {str(e)}"

    @staticmethod
    def get_pending_mentorship_applications():
        """Get all pending mentorship applications"""
        return MentorshipApplication.query.filter_by(status='pending').all()

    @staticmethod
    def get_pending_mentor_applications():
        """Get all pending mentor applications"""
        return MentorApplication.query.filter_by(status='pending').all()

    @staticmethod
    def approve_mentor_application(application_id, admin_id):
        """Approve a mentor application"""
        application = MentorApplication.query.get(application_id)
        if not application:
            return None, "Application not found."

        application.status = 'approved'
        application.updated_at = datetime.now()

        # Update user role to mentor
        user = User.query.get(application.applicant_id)
        user.is_mentor = True

        db.session.commit()

        # Send approval email
        msg = Message(
            subject="Mentor Application Approved",
            recipients=[user.email],
            body=f"Congratulations! Your mentor application has been approved."
        )
        mail.send(msg)

        return application, "Mentor application approved successfully."

    @staticmethod
    def reject_mentor_application(application_id, reason):
        """Reject a mentor application"""
        application = MentorApplication.query.get(application_id)
        if not application:
            return None, "Application not found."

        application.status = 'rejected'
        application.updated_at = datetime.now()
        db.session.commit()

        # Send rejection email
        user = User.query.get(application.applicant_id)
        msg = Message(
            subject="Mentor Application Decision",
            recipients=[user.email],
            body=f"Your mentor application was not approved. Reason: {reason}"
        )
        mail.send(msg)

        return application, "Mentor application rejected."

    @staticmethod
    def assign_mentor(mentorship_application_id, mentor_id, admin_id):
        """Assign a mentor to a student"""
        application = MentorshipApplication.query.get(mentorship_application_id)
        if not application:
            return None, "Mentorship application not found."

        mentor = User.query.get(mentor_id)
        if not mentor or not mentor.is_mentor:
            return None, "Invalid mentor selected."

        # Create mentorship relationship
        mentorship = Mentorship(
            mentor_id=mentor_id,
            mentee_id=application.student_id
        )
        db.session.add(mentorship)

        # Update application status
        application.status = 'approved'
        application.updated_at = datetime.now()

        db.session.commit()

        # Send notifications to both parties
        mentee = User.query.get(application.student_id)

        # Email to mentee
        msg_mentee = Message(
            subject="Mentor Assigned",
            recipients=[mentee.email],
            body=f"You have been matched with a mentor: {mentor.firstname} {mentor.lastname}"
        )
        mail.send(msg_mentee)

        # Email to mentor
        msg_mentor = Message(
            subject="New Mentee Assigned",
            recipients=[mentor.email],
            body=f"You have been assigned a new mentee: {mentee.firstname} {mentee.lastname}"
        )
        mail.send(msg_mentor)

        return mentorship, "Mentor assigned successfully."

    @staticmethod
    def schedule_session(mentorship_id, scheduled_time, duration, notes=None):
        """Schedule a mentorship session"""
        mentorship = Mentorship.query.get(mentorship_id)
        if not mentorship:
            return None, "Mentorship relationship not found."

        session = MentorshipSession(
            mentorship_id=mentorship_id,
            scheduled_time=scheduled_time,
            duration=duration,
            notes=notes
        )
        db.session.add(session)
        db.session.commit()

        # Notify both parties
        mentor = User.query.get(mentorship.mentor_id)
        mentee = User.query.get(mentorship.mentee_id)

        # Email to mentee
        msg_mentee = Message(
            subject="Mentorship Session Scheduled",
            recipients=[mentee.email],
            body=f"A new mentorship session has been scheduled for {scheduled_time}."
        )
        mail.send(msg_mentee)

        # Email to mentor
        msg_mentor = Message(
            subject="Mentorship Session Scheduled",
            recipients=[mentor.email],
            body=f"A new mentorship session has been scheduled for {scheduled_time}."
        )
        mail.send(msg_mentor)

        return session, "Session scheduled successfully."

    @staticmethod
    def submit_feedback(session_id, feedback_by, rating, comments):
        """Submit feedback for a mentorship session"""
        session = MentorshipSession.query.get(session_id)
        if not session:
            return None, "Session not found."

        feedback = MentorshipFeedback(
            session_id=session_id,
            feedback_by=feedback_by,
            rating=rating,
            comments=comments
        )
        db.session.add(feedback)

        # Update session status if both parties have submitted feedback
        feedback_count = MentorshipFeedback.query.filter_by(session_id=session_id).count()
        if feedback_count >= 2:  # Assuming both mentor and mentee provide feedback
            session.status = 'completed'

        db.session.commit()

        return feedback, "Feedback submitted successfully."

    @staticmethod
    def get_mentorship_sessions(mentorship_id):
        """Get all sessions for a mentorship"""
        return MentorshipSession.query.filter_by(mentorship_id=mentorship_id).all()

    @staticmethod
    def get_mentor_mentorships(mentor_id):
        """Get all mentorship relationships for a mentor"""
        return Mentorship.query.filter_by(mentor_id=mentor_id).all()

    @staticmethod
    def get_mentee_mentorships(mentee_id):
        """Get all mentorship relationships for a mentee"""
        return Mentorship.query.filter_by(mentee_id=mentee_id).all()

    @staticmethod
    def complete_mentorship(mentorship_id):
        """Mark a mentorship as completed"""
        mentorship = Mentorship.query.get(mentorship_id)
        if not mentorship:
            return None, "Mentorship not found."

        mentorship.status = 'completed'
        mentorship.end_date = datetime.now()
        db.session.commit()

        return mentorship, "Mentorship marked as completed."
