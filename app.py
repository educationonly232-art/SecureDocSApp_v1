# app.py (Final Version for Render Deployment)
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
# ----------------------------------------------------------------------
# CONFIGURATION (HARDCODED FOR RENDER DEPLOYMENT)
# ----------------------------------------------------------------------

# 1. Secret Key (Hardcoded)
app.secret_key = '7T3u0G2f4Q8h1R6y9K5n2M1s8V9w0X4a3C'

# 2. Database URI (HARDCODED - Uses your Internal Render URL)
DATABASE_URL_HARDCODED = 'postgresql://balgopal_db_user:gjQdSZ8nbHDkAOyGYv5Mw7xvTsl5RccA@dpg-d466fvje5dus73cifcl0-a/balgopal_db'

# Fix for SQLAlchemy connection scheme
if DATABASE_URL_HARDCODED.startswith("postgres://"):
    DATABASE_URL_HARDCODED = DATABASE_URL_HARDCODED.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL_HARDCODED
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. File Uploads Configuration (Files will be TEMPORARY on Render Free Tier!)
basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

db = SQLAlchemy(app)


# ----------------------------------------------------------------------
# DATABASE MODELS, HELPERS, AND INITIALIZATION
# ----------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)


class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    purpose = db.Column(db.String(200), nullable=False)
    date_signed = db.Column(db.Date, nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('documents', lazy=True))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(folder, filename):
    filename = secure_filename(filename)
    base, ext = os.path.splitext(filename)
    candidate = filename
    i = 1
    while os.path.exists(os.path.join(folder, candidate)):
        candidate = f"{base}_{i}{ext}"
        i += 1
    return candidate


with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        default = User(username='director1',
                       password_hash=generate_password_hash('password123'))
        db.session.add(default)
        db.session.commit()

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ----------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session invalid. Please login again.', 'danger')
        return redirect(url_for('login'))
    return render_template('profile.html', user=user)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if user is None:
        session.clear()
        flash('Session invalid. Please login again.', 'danger')
        return redirect(url_for('login'))

    documents = Document.query.order_by(Document.date_signed.desc()).all()
    return render_template('dashboard.html',
                           documents=documents,
                           user=user,
                           edit_doc=None)


@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('dashboard'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Only PDF, DOC, DOCX allowed.', 'danger')
        return redirect(url_for('dashboard'))

    # Save file with unique name (TEMPORARY on Render Free Tier!)
    filename = unique_filename(app.config['UPLOAD_FOLDER'], file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # Metadata
    name = (request.form.get('name') or '').strip()
    purpose = (request.form.get('purpose') or '').strip()
    date_signed_str = request.form.get('date_signed') or ''

    if not (name and purpose and date_signed_str):
        # cleanup uploaded file
        try:
            os.remove(save_path)
        except Exception:
            pass
        flash('Missing required fields', 'danger')
        return redirect(url_for('dashboard'))

    try:
        date_signed = datetime.strptime(date_signed_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            os.remove(save_path)
        except Exception:
            pass
        flash('Invalid date format', 'danger')
        return redirect(url_for('dashboard'))

    doc = Document(name=name,
                   purpose=purpose,
                   date_signed=date_signed,
                   filename=filename,
                   user_id=session['user_id'])
    db.session.add(doc)
    db.session.commit()
    flash('Document uploaded successfully (Warning: File is temporary)', 'warning')
    return redirect(url_for('dashboard'))


@app.route('/edit/<int:doc_id>', methods=['GET', 'POST'])
def edit(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doc = Document.query.get_or_404(doc_id)
    user = User.query.get(session['user_id'])
    if user is None:
        session.clear()
        flash('Session invalid. Please login again.', 'danger')
        return redirect(url_for('login'))

    documents = Document.query.order_by(Document.date_signed.desc()).all()

    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        purpose = (request.form.get('purpose') or '').strip()
        date_signed_str = request.form.get('date_signed') or ''

        if not (name and purpose and date_signed_str):
            flash('Missing required fields', 'danger')
            return render_template('dashboard.html',
                                   documents=documents,
                                   user=user,
                                   edit_doc=doc)

        try:
            date_signed = datetime.strptime(date_signed_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format', 'danger')
            return render_template('dashboard.html',
                                   documents=documents,
                                   user=user,
                                   edit_doc=doc)

        doc.name = name
        doc.purpose = purpose
        doc.date_signed = date_signed

        # Optional file replacement
        file = request.files.get('file')
        if file and file.filename != '':
            if not allowed_file(file.filename):
                flash('Invalid file type. Only PDF, DOC, DOCX allowed.', 'danger')
                return render_template('dashboard.html',
                                       documents=documents,
                                       user=user,
                                       edit_doc=doc)

            # Save new file first, then remove old if successful
            new_filename = unique_filename(app.config['UPLOAD_FOLDER'], file.filename)
            new_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
            file.save(new_path)

            # remove old file
            try:
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            except Exception:
                pass

            doc.filename = new_filename

        db.session.commit()
        flash('Document updated successfully', 'success')
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html',
                           documents=documents,
                           user=user,
                           edit_doc=doc)


@app.route('/delete/<int:doc_id>', methods=['POST'])
def delete(doc_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    doc = Document.query.get_or_404(doc_id)
    
    path = os.path.join(app.config['UPLOAD_FOLDER'], doc.filename)
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted successfully', 'success')
    return redirect(url_for('dashboard'))


@app.route('/view/<path:filename>')
def view(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum allowed size is 1GB.', 'danger')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
