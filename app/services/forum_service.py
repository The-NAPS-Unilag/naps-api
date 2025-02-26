from app.models.forum import Forum, Thread, Message, ForumMember
from app.extensions import db

class ForumService:
    @staticmethod
    def create_forum(name, description, is_general=False):
        """Create a new forum."""
        forum = Forum(
            name=name,
            description=description,
            is_general=is_general
        )
        db.session.add(forum)
        db.session.commit()
        return forum

    @staticmethod
    def get_all_forums():
        """Retrieve all forums."""
        return Forum.query.all()

    @staticmethod
    def get_forum_by_id(forum_id):
        """Retrieve a specific forum by its ID."""
        return Forum.query.get(forum_id)

    @staticmethod
    def join_forum(forum_id, user_id):
        """Join a forum."""
        if ForumMember.query.filter_by(forum_id=forum_id, user_id=user_id).first():
            return None, "You are already a member of this forum."

        forum_member = ForumMember(forum_id=forum_id, user_id=user_id)
        db.session.add(forum_member)
        db.session.commit()
        return forum_member, "You have successfully joined the forum."

    @staticmethod
    def create_thread(forum_id, title, user_id):
        """Create a new thread in a forum."""
        thread = Thread(title=title, forum_id=forum_id, created_by=user_id)
        db.session.add(thread)
        db.session.commit()
        return thread

    @staticmethod
    def send_message(thread_id, content, user_id, parent_message_id=None):
        """Send a message in a thread."""
        if len(content) > 1000:
            return None, "Message exceeds the character limit of 1000."

        message = Message(
            content=content,
            thread_id=thread_id,
            sent_by=user_id,
            parent_message_id=parent_message_id
        )
        db.session.add(message)
        db.session.commit()
        return message, "Message sent successfully."

    @staticmethod
    def get_thread_messages(thread_id):
        """Retrieve all messages in a thread."""
        return Message.query.filter_by(thread_id=thread_id).order_by(Message.sent_on.asc()).all()

    @staticmethod
    def like_message(message_id):
        """Like a message."""
        message = Message.query.get(message_id)
        if message:
            message.likes += 1
            db.session.commit()
            return message
        return None