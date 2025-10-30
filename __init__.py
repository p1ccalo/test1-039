
import os
import argparse
from flask import Flask, jsonify, request, render_template, redirect, url_for, flash
from flask_cors import CORS
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from backend.models import Base, Client, Exercise, Program, ProgramExercise, Product, Service, Article

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///orthospin.db')
FLASK_SECRET = os.getenv('FLASK_SECRET', 'change_me')
PORT = int(os.getenv('PORT', '8000'))

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = FLASK_SECRET
CORS(app)

engine = create_engine(DATABASE_URL, future=True)

def init_db():
    Base.metadata.create_all(engine)

# ---------------- API ----------------
@app.get('/api/health')
def api_health():
    return jsonify(status='ok')

@app.get('/api/client/by_tg/<tg_id>')
def api_client_by_tg(tg_id):
    with Session(engine) as s:
        c = s.query(Client).filter(Client.tg_id == tg_id).first()
        if not c:
            return jsonify(error='not_found'), 404
        data = {
            'id': c.id, 'tg_id': c.tg_id, 'name': c.name, 'phone': c.phone, 'email': c.email,
            'complaints': c.complaints, 'diagnosis': c.diagnosis, 'recommendations': c.recommendations,
            'photo_before': c.photo_before, 'photo_after': c.photo_after,
            'program_id': c.program_id,
        }
        return jsonify(data)

@app.get('/api/program/<int:client_id>')
def api_program(client_id):
    with Session(engine) as s:
        c = s.get(Client, client_id)
        if not c or not c.program_id:
            return jsonify(exercises=[])
        # витягуємо впорядкований список вправ
        prog = s.get(Program, c.program_id)
        out = []
        for pe in prog.exercises:
            e = pe.exercise
            out.append({
                'id': e.id, 'title': e.title, 'description': e.description,
                'impact_zone': e.impact_zone, 'difficulty': e.difficulty,
                'comment': e.comment, 'tags': e.tags, 'media_url': e.media_url,
                'order': pe.sort_order
            })
        return jsonify(program={'id': prog.id, 'title': prog.title, 'description': prog.description, 'exercises': out})

@app.get('/api/products')
def api_products():
    category = request.args.get('category')
    with Session(engine) as s:
        q = s.query(Product).filter(Product.active == True)
        if category:
            q = q.filter(Product.category == category)
        items = [ {'id': p.id, 'title': p.title, 'category': p.category, 'description': p.description, 'photo_url': p.photo_url} for p in q.all() ]
        return jsonify(products=items)

@app.get('/api/services')
def api_services():
    with Session(engine) as s:
        q = s.query(Service).filter(Service.active == True)
        items = [{'id': s_.id, 'title': s_.title, 'description': s_.description, 'price': s_.price, 'category': s_.category} for s_ in q.all()]
        return jsonify(services=items)

@app.get('/api/articles')
def api_articles():
    with Session(engine) as s:
        q = s.query(Article).filter(Article.active == True)
        items = [{'id': a.id, 'title': a.title, 'content': a.content, 'category': a.category} for a in q.all()]
        return jsonify(articles=items)

# --------- прості адмін-сторінки (Jinja) ---------
@app.get('/admin')
def admin_home():
    return render_template('admin/index.html')

@app.get('/admin/products')
def admin_products():
    with Session(engine) as s:
        items = s.query(Product).all()
    return render_template('admin/products.html', items=items)

@app.post('/admin/products')
def admin_products_create():
    data = request.form
    with Session(engine) as s:
        s.add(Product(title=data.get('title',''), category=data.get('category',''), description=data.get('description',''), photo_url=data.get('photo_url',''), active=True))
        s.commit()
    flash('Товар додано', 'success')
    return redirect(url_for('admin_products'))

@app.post('/admin/products/<int:pid>/delete')
def admin_products_delete(pid):
    with Session(engine) as s:
        s.execute(delete(Product).where(Product.id == pid))
        s.commit()
    flash('Видалено', 'success')
    return redirect(url_for('admin_products'))

@app.get('/admin/services')
def admin_services():
    with Session(engine) as s:
        items = s.query(Service).all()
    return render_template('admin/services.html', items=items)

@app.post('/admin/services')
def admin_services_create():
    data = request.form
    price = float(data.get('price', '0') or 0)
    with Session(engine) as s:
        s.add(Service(title=data.get('title',''), category=data.get('category',''), description=data.get('description',''), price=price, active=True))
        s.commit()
    flash('Послугу додано', 'success')
    return redirect(url_for('admin_services'))

@app.post('/admin/services/<int:sid>/delete')
def admin_services_delete(sid):
    with Session(engine) as s:
        s.execute(delete(Service).where(Service.id == sid))
        s.commit()
    flash('Видалено', 'success')
    return redirect(url_for('admin_services'))

@app.get('/admin/exercises')
def admin_exercises():
    with Session(engine) as s:
        items = s.query(Exercise).all()
    return render_template('admin/exercises.html', items=items)

@app.post('/admin/exercises')
def admin_exercises_create():
    data = request.form
    with Session(engine) as s:
        s.add(Exercise(
            title=data.get('title',''), description=data.get('description',''),
            impact_zone=data.get('impact_zone',''), difficulty=data.get('difficulty',''),
            comment=data.get('comment',''), tags=data.get('tags',''), media_url=data.get('media_url','')
        ))
        s.commit()
    flash('Вправу додано', 'success')
    return redirect(url_for('admin_exercises'))

@app.post('/admin/exercises/<int:eid>/delete')
def admin_exercises_delete(eid):
    with Session(engine) as s:
        s.execute(delete(Exercise).where(Exercise.id == eid))
        s.commit()
    flash('Видалено', 'success')
    return redirect(url_for('admin_exercises'))

@app.get('/admin/programs')
def admin_programs():
    with Session(engine) as s:
        progs = s.query(Program).all()
        exercises = s.query(Exercise).all()
    return render_template('admin/programs.html', programs=progs, exercises=exercises)

@app.post('/admin/programs')
def admin_programs_create():
    data = request.form
    title = data.get('title','')
    description = data.get('description','')
    with Session(engine) as s:
        p = Program(title=title, description=description)
        s.add(p); s.flush()
        # додаємо обрані вправи (ids через кому) з порядком
        ids = (data.get('exercise_ids','') or '').split(',')
        for idx, val in enumerate([i.strip() for i in ids if i.strip().isdigit()], start=1):
            s.add(ProgramExercise(program_id=p.id, exercise_id=int(val), sort_order=idx))
        s.commit()
    flash('Програму створено', 'success')
    return redirect(url_for('admin_programs'))

@app.post('/admin/programs/<int:pid>/delete')
def admin_programs_delete(pid):
    with Session(engine) as s:
        s.execute(delete(Program).where(Program.id == pid))
        s.commit()
    flash('Видалено', 'success')
    return redirect(url_for('admin_programs'))

@app.get('/admin/clients')
def admin_clients():
    with Session(engine) as s:
        items = s.query(Client).all()
        programs = s.query(Program).all()
    return render_template('admin/clients.html', items=items, programs=programs)

@app.post('/admin/clients')
def admin_clients_create():
    data = request.form
    with Session(engine) as s:
        c = Client(
            tg_id=data.get('tg_id',''), name=data.get('name',''),
            phone=data.get('phone',''), email=data.get('email',''),
            complaints=data.get('complaints',''), diagnosis=data.get('diagnosis',''),
            recommendations=data.get('recommendations',''), photo_before=data.get('photo_before',''),
            photo_after=data.get('photo_after',''), program_id=int(data.get('program_id') or 0) or None
        )
        s.add(c); s.commit()
    flash('Клієнта створено', 'success')
    return redirect(url_for('admin_clients'))

@app.post('/admin/clients/<int:cid>/delete')
def admin_clients_delete(cid):
    with Session(engine) as s:
        s.execute(delete(Client).where(Client.id == cid))
        s.commit()
    flash('Видалено', 'success')
    return redirect(url_for('admin_clients'))

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--initdb', action='store_true')
    parser.add_argument('--seed', action='store_true')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=str(PORT))
    args = parser.parse_args()

    if args.initdb:
        init_db()
        print('DB initialized')

    app.run(host=args.host, port=int(args.port))

if __name__ == '__main__':
    run()
