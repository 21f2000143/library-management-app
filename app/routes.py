from flask import redirect,render_template,url_for,Blueprint,request,flash, make_response, send_from_directory
from flask import session, g
from flask_login import LoginManager,current_user,login_user,logout_user,login_required
from .database import *
from werkzeug.security import generate_password_hash,check_password_hash
from . import db
from functools import wraps
import fitz  # PyMuPDF
import datetime
from sqlalchemy import or_
from flask import request

# Open the PDF file





route = Blueprint('route', __name__)

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user is None or current_user.role != role:
                return render_template('login.html')
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@route.route('/')
def home():
    exist_libra=User.query.filter_by(username="ds@harsh").first()
    if not exist_libra:
        librarian = User(username="ds@harsh", role="librarian", password_hash=generate_password_hash("password",method='scrypt'))
        db.session.add(librarian)
        db.session.commit()
    return render_template('home.html')

@route.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        user = User.query.filter(input_username==User.username).first()
        if user:
            if check_password_hash(user.password_hash, input_password):
                flash("login sucessfully",category='success')
                login_user(user,remember=False)
                id = user.id
                return redirect(f'/user_dashboard/{id}')
            else:
                flash("wrong credentials",category="danger")
                return redirect('/')
        else:
            flash("User not registered try to register from signup page",category='error')
            return redirect('/signup')
    return render_template('login.html',user=current_user)

@route.route('/signup',methods=['GET','POST'])
def signup():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(username == User.username).first()
        if user:
            flash("Username is already taken try with different name",category='error')
        elif len(password) < 5:
            flash("Password should be of minimum 5 characters", category="error")
        else:
            user = User(username=username, role="user", password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("User created successfully",category='success')
            return redirect('/login')
    return render_template('signup.html',user=current_user)

@route.route('/update/section/<int:id>',methods=['POST'])
def update_section(id):
    if request.method=="POST":
        title = request.form.get('title')
        section = Section.query.filter_by(id=id).first()
        if section:
            section_by_name = Section.query.filter_by(name=title).first()
            if section_by_name and section_by_name.id != section.id:
                flash("Section already exists",category='error')
                sections = Section.query.all()
                return render_template('librarian_dashboard.html',sections=sections)
            section.name = request.form.get('title')
            section.date = datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            section.description = request.form.get('description')
            db.session.commit()
            flash("Section updated successfully",category='success')
            sections = Section.query.all()
            return render_template('librarian_dashboard.html',sections=sections)
        flash("Section not found",category='error')
        sections = Section.query.all()
        return render_template('librarian_dashboard.html',sections=sections)
@route.route('/update/book/<int:id>',methods=['POST'])
def update_book(id):
    if request.method=="POST":
        title = request.form.get('title')
        book = Book.query.filter_by(id=id).first()
        if book:
            book_by_name = Book.query.filter_by(title=title).first()
            if book_by_name and book_by_name.id != book.id:
                flash("Book already exists",category='error')
                books = Book.query.all()
                sections = Section.query.all()
                return render_template('books.html',books=books, sections=sections)
            book.title = request.form.get('title')
            book.author = request.form.get('author')
            book.price = request.form.get('price')
            book.content = request.files['content'].read()
            book.section_id = request.form.get('section_id')
            book.date = datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            book.description = request.form.get('description')
            db.session.commit()
            flash("Book updated successfully",category='success')
            books = Book.query.all()
            sections = Section.query.all()
            return render_template('books.html',books=books, sections=sections)
        flash("Book not found",category='error')
        books = Book.query.all()
        sections = Section.query.all()
        return render_template('books.html',books=books, sections=sections)    
@route.route('/delete/section/<int:id>')
def delete_section(id):
        section = Section.query.filter_by(id=id).first()
        if section:
            db.session.delete(section)
            db.session.commit()
            flash("Section deleted successfully",category='success')
            sections = Section.query.all()
            return render_template('librarian_dashboard.html',sections=sections)
        flash("Section not found",category='error')
        sections = Section.query.all()
        return render_template('librarian_dashboard.html',sections=sections)
@route.route('/delete/book/<int:id>')
def delete_book(id):
    book = Book.query.filter_by(id=id).first()
    if book:
        db.session.delete(book)
        db.session.commit()
        flash("Book deleted successfully",category='success')
        books = Book.query.all()
        sections = Section.query.all()
        return render_template('books.html',books=books, sections=sections)
    flash("Book not found",category='error')
    books = Book.query.all()
    sections = Section.query.all()
    return render_template('books.html',books=books, sections=sections)
@route.route('/reuested/book/<int:id>')
def reuested_book(id):
    book = Book.query.filter_by(id=id).first()
    if book:
        register = Register(username=current_user.username, book_name=book.title, request_status='pending', user_id=current_user.id, book_id=book.id)
        db.session.add(register)
        db.session.commit()
        flash("Book requested successfully",category='success')
        return redirect(url_for('route.add_books'))
    flash("Book not found",category='error')
    return redirect(url_for('route.add_books'))
@route.route('/reject/book/<int:id>')
def reject_book(id):
    register = Register.query.filter_by(id=id).first()
    if register:
        register.request_status = 'rejected'
        db.session.commit()
        flash("Book rejected successfully",category='success')
        return redirect(url_for('route.add_books'))
    flash("Request not found",category='error')
    return redirect(url_for('route.add_books'))

@route.route('/revoke/book/<int:id>')
def revoke_book(id):
    register = Register.query.filter_by(id=id).first()
    if register:
        register.request_status = 'revoked'
        db.session.commit()
        flash("Book revoked successfully",category='success')
        return redirect(url_for('route.add_books'))
    flash("Request not found",category='error')
    return redirect(url_for('route.add_books'))
@route.route('/grant/book/<int:id>')
def grant_book(id):
    register = Register.query.filter_by(id=id).first()
    if register:
        register.request_status = 'granted'
        db.session.commit()
        flash("Book granted successfully",category='success')
        return redirect(url_for('route.add_books'))
    flash("Request not found",category='error')
    return redirect(url_for('route.add_books'))

@route.route('/books',methods=['GET','POST'])
def add_books():
    if request.method=='POST':
        title = request.form.get('title')
        author = request.form.get('author')
        price = request.form.get('price')
        content = request.files['content'].read()
        description = request.form.get('description')
        section_id = request.form.get('section_id')
        if Book.query.filter_by(title=title).first():
            flash("Book already exists",category='error')
            books = Book.query.all()
            sections = Section.query.all()
            return render_template('books.html',books=books, sections=sections)
        date = request.form.get('date')
        book = Book(title=title, author=author, price=price, content=content, section_id=section_id, description=description, date=datetime.datetime.strptime(date, '%Y-%m-%d').date())
        db.session.add(book)
        db.session.commit()
        flash("Book added successfully",category='success')
        books = Book.query.all()
        sections = Section.query.all()
        return render_template('books.html',books=books, sections=sections)
    param = request.args.get('param')
    remove = request.args.get('remove')
    search_word=request.args.get('search')
    books=None
    if search_word:
        books = Book.query.filter(or_(
            Book.title.ilike(f'%{search_word}%'),
            Book.author.ilike(f'%{search_word}%'),
            Book.description.ilike(f'%{search_word}%'),
            Book.section.has(Section.name.ilike(f'%{search_word}%'))
        )).all()
        sections = Section.query.all()
        return render_template('books.html',books=books, sections=sections, search_by = search_word)
    elif param:
        if not session.get('params'):
            session['params']=[]
        result = []
        session['params'].append(param)
        session.modified = True
        for i in session['params']:
            if i=='today':
                books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                for book in books:
                    if book not in result:
                        result.append(book)
            elif i=='last week':
                books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                for book in books:
                    if book not in result:
                        result.append(book)
            elif i=='last month':
                books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                for book in books:
                    if book not in result:
                        result.append(book)
            elif i=='last year':
                books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                for book in books:
                    if book not in result:
                        result.append(book)
        books = result
        g.params = session.get('params')
        sections = Section.query.all()
        return render_template('books.html', books=books, sections = sections)
    elif remove:
        print(session.get('params'))
        if session.get('params'):
            session['params'].remove(remove)
            session.modified = True
            result = []
            for i in session.get('params'):
                if i=='today':
                    books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                    for book in books:
                        if book not in result:
                            result.append(book)
                elif i=='last week':
                    books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                    for book in books:
                        if book not in result:
                            result.append(book)
                elif i=='last month':
                    books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                    for book in books:
                        if book not in result:
                            result.append(book)
                elif i=='last year':
                    books=Book.query.filter(Book.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                    for book in books:
                        if book not in result:
                            result.append(book)
            books = result
            params = session.get('params')
            if params is None:
                g.params = None
            else:
                g.params = params
                sections = Section.query.all()
                return render_template('books.html',books=books, sections=sections)
        else:
            return redirect(url_for('route.add_books'))
    if session.get('params'):
        session.pop('params')
    books = Book.query.all()
    sections = Section.query.all()
    return render_template('books.html',books=books, sections=sections)

@route.route('/favicon.ico')
def favicon():
    return send_from_directory(route.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
@route.route('/requests',methods=['GET','POST'])
def requests():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(username == User.username).first()
        if user:
            flash("Username is already taken try with different name",category='error')
        elif len(password) < 5:
            flash("Password should be of minimum 5 characters", category="error")
        else:
            user = User(username=username, role="user", password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("User created successfully",category='success')
            return redirect('/login')
        
    requesteds = Register.query.all()
    data_list =[]
    for requested in requesteds:
        data_dic={}
        data_dic['id'] = requested.id
        data_dic['username'] = requested.username
        data_dic['book_name'] = requested.book_name
        data_dic['request_status'] = requested.request_status
        data_dic['no_book_issued'] = len(Register.query.filter_by(request_status="granted", user_id=requested.user_id).all())
        data_dic['no_book_requested'] = len(Register.query.filter_by(request_status="pending", user_id=requested.user_id).all())
        data_dic['user_id'] = requested.user_id
        data_dic['book_id'] = requested.book_id
        if requested.date_issued:
            data_dic['date_issued'] = requested.date_issued.strftime('%d-%m-%Y')
        if requested.return_date:
            data_dic['return_date'] = requested.return_date.strftime('%d-%m-%Y')
        data_dic['requested_date'] = "today" if (datetime.datetime.now()-requested.requested_date).days==0 \
              else (datetime.datetime.now()-requested.requested_date).days
        data_list.append(data_dic)
    return render_template('librarian_request.html', requesteds=data_list)

@route.route('/stats',methods=['GET','POST'])
def stats():
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(username == User.username).first()
        if user:
            flash("Username is already taken try with different name",category='error')
        elif len(password) < 5:
            flash("Password should be of minimum 5 characters", category="error")
        else:
            user = User(username=username, role="user", password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("User created successfully",category='success')
            return redirect('/login')
    return render_template('stats.html')

@route.route('/reading/room/<int:id>',methods=['GET','POST'])
def reading_room(id):
    if request.method=='POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter(username == User.username).first()
        if user:
            flash("Username is already taken try with different name",category='error')
        elif len(password) < 5:
            flash("Password should be of minimum 5 characters", category="error")
        else:
            user = User(username=username, role="user", password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash("User created successfully",category='success')
            return redirect('/login')
    return render_template('reading_room.html', id=id)

@route.route('/docs/<id>')
def get_pdf(id=None):
    if id is not None:
        book = Book.query.filter_by(id=id).first()
        binary_pdf = book.content
        response = make_response(binary_pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = \
            'inline; filename=%s.pdf' % 'yourfilename'
        return response

@route.route('/librarian_login',methods=['GET','POST'])
def librarian_login():
    if request.method=='POST':
        input_username = request.form.get('username')
        input_password = request.form.get('password')
        user = User.query.filter_by(username=input_username).first()
        if user:
            if user.role=='librarian' and user.username=='ds@harsh' and check_password_hash(user.password_hash,input_password):
                flash("login sucessfully",category='success')
                login_user(user,remember=False)
                return redirect(url_for('route.librarian_dashboard'))
            else:
                flash("you don't have admin rights or wrong credentials",category='error')
                return render_template('librarian_login.html')
        else:
            flash("Admin not registered",category='error')
    return render_template('librarian_login.html')

@route.route('/librarian_dashboard', methods=['GET','POST', 'PUT', 'DELETE'])
@login_required
@role_required('librarian')
def librarian_dashboard():
    if request.method=="POST":
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        if Section.query.filter_by(name=title).first():
            flash("Section already exists",category='error')
            sections = Section.query.all()
            return render_template('librarian_dashboard.html',sections=sections)
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        section = Section(name=title, date=date, description=description)
        db.session.add(section)
        db.session.commit()
        flash("Section created successfully",category='success')
        sections = Section.query.all()
        return render_template('librarian_dashboard.html',sections=sections)
    param = request.args.get('param')
    remove = request.args.get('remove')
    search_word=request.args.get('search')
    sections=None
    if search_word:
        sections = Section.query.filter(or_(
            Section.name.ilike(f'%{search_word}%'),
            Section.description.ilike(f'%{search_word}%'),
            Section.date.ilike(f'%{search_word}%')
        )).all()
        return render_template('librarian_dashboard.html',sections=sections, search_by = search_word)
    elif param:
        if not session.get('params'):
            session['params']=[]
        result = []
        session['params'].append(param)
        session.modified = True
        for i in session.get('params'):
            if i=='today':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last week':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last month':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last year':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
        sections = result
        g.params = session.get('params')
        print(g.params, session.get('params'))
        return render_template('librarian_dashboard.html',sections=sections)
    elif remove:
        if len(session.get('params'))>0:
            session['params'].remove(remove)
            session.modified = True
            result = []
            for i in session.get('params'):
                if i=='today':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last week':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last month':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last year':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
            sections = result
            params = session.get('params')
            if params is None:
                g.params = None
            else:
                g.params = params
                return render_template('librarian_dashboard.html',sections=sections)
        else:
            return redirect(url_for('route.librarian_dashboard'))
    if session.get('params'):
        session.pop('params', None)
        session.modified = True
        params = session.get('params')
        if params is None:
            g.params = Noneparams = session.get('params')
            if params is None:
                g.params = None
            else:
                g.params = params
        else:
            g.params = params
    sections = Section.query.all()
    return render_template('librarian_dashboard.html',sections=sections)

@route.route('/download_book/<int:id>')
def download_book(id):
    book = Book.query.filter_by(id=id).first()
    if book:
        purchase=Purchase(book_id=book.id,user_id=current_user.id, purchase_date=datetime.datetime.now(),price=book.price)
        db.session.add(purchase)
        db.session.commit()
        binary_pdf = book.content
        response = make_response(binary_pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=%s.pdf' % book.title
        return response
    
@route.route('/user_dashboard/<int:id>')
@login_required
@role_required('user')
def user_dashboard(id):
    if request.method=="POST":
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        title = request.form.get('title')
        date = request.form.get('date')
        description = request.form.get('description')
        if Section.query.filter_by(name=title).first():
            flash("Section already exists",category='error')
            sections = Section.query.all()
            return render_template('user_dashboard.html',sections=sections)
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        section = Section(name=title, date=date, description=description)
        db.session.add(section)
        db.session.commit()
        flash("Section created successfully",category='success')
        sections = Section.query.all()
        return render_template('librarian_dashboard.html',sections=sections)
    param = request.args.get('param')
    remove = request.args.get('remove')
    search_word=request.args.get('search')
    sections=None
    if search_word:
        sections = Section.query.filter(or_(
            Section.name.ilike(f'%{search_word}%'),
            Section.description.ilike(f'%{search_word}%'),
            Section.date.ilike(f'%{search_word}%')
        )).all()
        return render_template('user_dashboard.html',sections=sections, search_by = search_word)
    elif param:
        if not session.get('params'):
            session['params']=[]
        result = []
        session['params'].append(param)
        session.modified = True
        for i in session.get('params'):
            if i=='today':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last week':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last month':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
            elif i=='last year':
                sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                for section in sections:
                    if section not in result:
                        result.append(section)
        sections = result
        g.params = session.get('params')
        print(g.params, session.get('params'))
        return render_template('user_dashboard.html',sections=sections)
    elif remove:
        if len(session.get('params'))>0:
            session['params'].remove(remove)
            session.modified = True
            result = []
            for i in session.get('params'):
                if i=='today':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=0)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last week':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last month':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
                elif i=='last year':
                    sections = Section.query.filter(Section.date>=(datetime.datetime.now() - datetime.timedelta(days=365)).strftime('%Y-%m-%d')).all()
                    for section in sections:
                        if section not in result:
                            result.append(section)
            sections = result
            params = session.get('params')
            if params is None:
                g.params = None
            else:
                g.params = params
                return render_template('user_dashboard.html',sections=sections)
        else:
            return redirect(url_for('route.user_dashboard', id=current_user.id))
    if session.get('params'):
        session.pop('params', None)
        session.modified = True
        params = session.get('params')
        if params is None:
            g.params = Noneparams = session.get('params')
            if params is None:
                g.params = None
            else:
                g.params = params
        else:
            g.params = params
    sections = Section.query.all()
    return render_template('user_dashboard.html',sections=sections)

@route.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')