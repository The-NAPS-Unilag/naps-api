from app.extensions import db

class Forum(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())
    is_general = db.Column(db.Boolean, default=False)  # General forum for all users

    def __repr__(self):
        return f'<Forum {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_on': self.created_on.isoformat(),
            'is_general': self.is_general,
            'member_count': ForumMember.query.filter_by(forum_id=self.id).count(),
            'thread_count': Thread.query.filter_by(forum_id=self.id).count()
        }


class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    views = db.Column(db.Integer, default=0)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='threads')
    messages = db.relationship('Message', backref='thread', lazy='dynamic')
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Thread {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'body': self.body,
            'forum_id': self.forum_id,
            'created_by': {
                'id': self.creator.id,
                'firstname': self.creator.firstname,
                'lastname': self.creator.lastname,
                'profile_picture': self.creator.profile_picture
            },
            'created_on': self.created_on.isoformat(),
            'views': self.views,
            'comment_count': self.messages.count()
        }


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    sent_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sent_on = db.Column(db.DateTime, default=db.func.current_timestamp())
    parent_message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=True)  # For replies
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    likes = db.Column(db.Integer, default=0)
    attachment_url = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Message {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'thread_id': self.thread_id,
            'sent_by': self.sent_by,
            'sent_on': self.sent_on.isoformat(),
            'parent_message_id': self.parent_message_id,
            'reply_count': self.replies.count(),
            'likes': self.likes,
            'attachment_url': self.attachment_url
        }


class ForumMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forum.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    joined_on = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<ForumMember {self.forum_id} - {self.user_id}>'