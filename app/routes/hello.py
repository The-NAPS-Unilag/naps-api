from flask import Blueprint, render_template_string

hello_bp = Blueprint('hello_bp', __name__)

@hello_bp.route('/', methods=['GET'])
def hello_devs():
    message = (
        '<p>Hello, developers! All routes start with /api.</p>'
        '<p>You can view the <a href="/api/docs">Swagger docs here</a>.</p>'
    )
    return render_template_string(message)