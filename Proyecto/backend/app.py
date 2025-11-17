import os
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
from bcrypt import hashpw, checkpw, gensalt
from werkzeug.utils import secure_filename
import datetime

logging.basicConfig(level=logging.INFO)

# carpetas
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
app = Flask(__name__, template_folder=template_dir, static_folder=static_dir, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret')

# subida de archivos
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads'))
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'webm'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB máximo

# MongoDB
MONGO_URI = os.environ.get('MONGO_URI','mongodb+srv://jaredlcctpa_db_user:9MOKzyLmIbLMS6Ot@cluster0.ux11ghp.mongodb.net/?retryWrites=true&w=majority')
client = MongoClient(MONGO_URI)
db = client['Usuarios']
usuarios_collection = db['Usuario']
video_collection = db['Videos']
comments_collection = db['Comentarios']

# Crear índice único
try:
    usuarios_collection.create_index('username', unique=True)
    usuarios_collection.create_index('email', unique=True)
except Exception:
    logging.exception("No se pudieron crear índices (puede que ya existan).")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_admin(user_id):
    """Verifica si el usuario es admin"""
    try:
        user = usuarios_collection.find_one({'_id': ObjectId(user_id)})
        return user and user.get('role') == 'admin'
    except:
        return False

# ==================== RUTAS DE USUARIOS ====================

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Obtiene todos los usuarios (solo admin)"""
    user = session.get('user')
    if not user or not is_admin(user['user_id']):
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        users = list(usuarios_collection.find({'role': {'$ne': 'admin'}}).limit(100))
        for u in users:
            u['_id'] = str(u['_id'])
            u.pop('password', None)  #par no devolver contraseñas
        return jsonify(users), 200
    except Exception as e:
        logging.exception("Error al obtener usuarios")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/user/<user_id>', methods=['GET'])
def get_user(user_id):
    """Obtiene perfil de un usuario específico"""
    try:
        user = usuarios_collection.find_one({'_id': ObjectId(user_id)})
        if not user:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        
        # contar videos y comentarios
        video_count = video_collection.count_documents({'user_id': user_id})
        comment_count = comments_collection.count_documents({'author': user['username']})
        
        user['stats'] = {'videos': video_count, 'comments': comment_count}
        return jsonify(user), 200
    except Exception as e:
        logging.exception("Error al obtener usuario")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    """Actualiza datos del usuario"""
    current_user = session.get('user')
    if not current_user or (current_user['user_id'] != user_id and not is_admin(current_user['user_id'])):
        return jsonify({'error': 'No autorizado'}), 403
    
    data = request.get_json()
    try:
        update_data = {}
        if data.get('username'):
            update_data['username'] = data['username']
        if data.get('email'):
            update_data['email'] = data['email']
        
        result = usuarios_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_data})
        
        if result.matched_count == 0:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        return jsonify({'message': 'Usuario actualizado exitosamente'}), 200
    except DuplicateKeyError:
        return jsonify({'error': 'Usuario o email ya existe'}), 400
    except Exception as e:
        logging.exception("Error al actualizar usuario")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Elimina un usuario (solo admin o el mismo usuario)"""
    current_user = session.get('user')
    if not current_user or (current_user['user_id'] != user_id and not is_admin(current_user['user_id'])):
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        # eliminar videos del usuario
        videos = list(video_collection.find({'user_id': user_id}))
        for video in videos:
            # eliminar archivo
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], video['filename'])
            if os.path.exists(filepath):
                os.remove(filepath)
        
        video_collection.delete_many({'user_id': user_id})
        
        # eliminar comentarios del usuario
        username = usuarios_collection.find_one({'_id': ObjectId(user_id)}).get('username')
        comments_collection.delete_many({'author': username})
        
        # eliminar usuario
        result = usuarios_collection.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        
        # cerrar sesión si se elimina a sí mismo
        if current_user['user_id'] == user_id:
            session.clear()
        
        return jsonify({'message': 'Usuario eliminado exitosamente'}), 200
    except Exception as e:
        logging.exception("Error al eliminar usuario")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/user/<user_id>/videos', methods=['GET'])
def get_user_videos(user_id):
    """Obtiene todos los videos de un usuario"""
    try:
        videos = list(video_collection.find({'user_id': user_id}).sort('uploaded_at', -1))
        for v in videos:
            v['_id'] = str(v['_id'])
        return jsonify(videos), 200
    except Exception as e:
        logging.exception("Error al obtener videos del usuario")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== RUTAS DE VIDEOS ====================

@app.route('/api/upload', methods=['POST'])
def upload_video():
    if 'user' not in session:
        return jsonify({'error': 'Debes estar logueado'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró archivo'}), 400
    
    file = request.files['file']
    title = request.form.get('title', 'Sin título')
    description = request.form.get('description', '')
    
    if file.filename == '':
        return jsonify({'error': 'Archivo vacío'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Formato no permitido. Usa mp4, avi, mov o webm'}), 400
    
    try:
        filename = secure_filename(file.filename)
        timestamp = str(int(__import__('time').time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        video_data = {
            'title': title,
            'description': description,
            'filename': filename,
            'user_id': session['user']['user_id'],
            'username': session['user']['username'],
            'thumbnail': f"/static/uploads/{filename}",
            'views': 0,
            'date': datetime.datetime.now().strftime('%d/%m/%Y'),
            'uploaded_at': datetime.datetime.now(),
            'type': 'video'
        }
        
        result = video_collection.insert_one(video_data)
        logging.info(f"Video subido: {result.inserted_id}")
        
        return jsonify({'message': 'Video subido exitosamente', 'video_id': str(result.inserted_id)}), 201
    
    except Exception as e:
        logging.exception("Error al subir video")
        return jsonify({'error': 'Error al subir video'}), 500

@app.route('/api/video/<video_id>', methods=['PUT'])
def update_video(video_id):
    """Actualiza un video (solo el creador o admin)"""
    current_user = session.get('user')
    if not current_user:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        video = video_collection.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video no encontrado'}), 404
        
        if video['user_id'] != current_user['user_id'] and not is_admin(current_user['user_id']):
            return jsonify({'error': 'No autorizado'}), 403
        
        data = request.get_json()
        update_data = {}
        if data.get('title'):
            update_data['title'] = data['title']
        if data.get('description'):
            update_data['description'] = data['description']
        
        video_collection.update_one({'_id': ObjectId(video_id)}, {'$set': update_data})
        
        return jsonify({'message': 'Video actualizado exitosamente'}), 200
    except Exception as e:
        logging.exception("Error al actualizar video")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/video/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Elimina un video (solo el creador o admin)"""
    current_user = session.get('user')
    if not current_user:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        video = video_collection.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video no encontrado'}), 404
        
        if video['user_id'] != current_user['user_id'] and not is_admin(current_user['user_id']):
            return jsonify({'error': 'No autorizado'}), 403
        
        # eliminar archivo
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], video['filename'])
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # eliminar video
        video_collection.delete_one({'_id': ObjectId(video_id)})
        
        # eliminar comentarios
        comments_collection.delete_many({'video_id': video_id})
        
        return jsonify({'message': 'Video eliminado exitosamente'}), 200
    except Exception as e:
        logging.exception("Error al eliminar video")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== RUTAS DE COMENTARIOS ====================

@app.route('/api/video/<video_id>/comment', methods=['POST'])
def post_comment(video_id):
    data = request.get_json()
    if not data or not data.get('text'):
        return jsonify({'error': 'Comentario vacío'}), 400
    author = session.get('user', {}).get('username', 'Anonimo')
    comment = {
        'video_id': video_id,
        'author': author,
        'text': data['text'],
        'created_at': datetime.datetime.now()
    }
    try:
        result = comments_collection.insert_one(comment)
        comment['_id'] = str(result.inserted_id)
        comment['created_at'] = comment['created_at'].strftime('%d/%m/%Y %H:%M')
        return jsonify({'message': 'ok', 'comment': comment}), 201
    except Exception:
        logging.exception("Error al guardar comentario")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/comment/<comment_id>', methods=['PUT'])
def update_comment(comment_id):
    """Actualiza un comentario (solo el autor o admin)"""
    current_user = session.get('user')
    if not current_user:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        comment = comments_collection.find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return jsonify({'error': 'Comentario no encontrado'}), 404
        
        if comment['author'] != current_user['username'] and not is_admin(current_user['user_id']):
            return jsonify({'error': 'No autorizado'}), 403
        
        data = request.get_json()
        if data.get('text'):
            comments_collection.update_one({'_id': ObjectId(comment_id)}, {'$set': {'text': data['text']}})
        
        return jsonify({'message': 'Comentario actualizado exitosamente'}), 200
    except Exception as e:
        logging.exception("Error al actualizar comentario")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/comment/<comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Elimina un comentario (solo el autor o admin)"""
    current_user = session.get('user')
    if not current_user:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        comment = comments_collection.find_one({'_id': ObjectId(comment_id)})
        if not comment:
            return jsonify({'error': 'Comentario no encontrado'}), 404
        
        if comment['author'] != current_user['username'] and not is_admin(current_user['user_id']):
            return jsonify({'error': 'No autorizado'}), 403
        
        comments_collection.delete_one({'_id': ObjectId(comment_id)})
        
        return jsonify({'message': 'Comentario eliminado exitosamente'}), 200
    except Exception as e:
        logging.exception("Error al eliminar comentario")
        return jsonify({'error': 'Error del servidor'}), 500

# ==================== RUTAS PRINCIPALES ====================

@app.route('/upload')
def upload_page():
    if 'user' not in session:
        return redirect(url_for('login_page'))
    return render_template('upload.html', user=session.get('user'))

@app.route('/')
def index():
    user = session.get('user')
    try:
        videos = list(video_collection.find({'type': 'video'}).sort('uploaded_at', -1).limit(10))
        for video in videos:
            video['_id'] = str(video['_id'])
    except:
        videos = []
    return render_template('index.html', user=user, videos=videos)

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    user = session.get('user')
    try:
        videos = list(video_collection.find({'title': {'$regex': query, '$options': 'i'}, 'type': 'video'}).limit(10))
        for video in videos:
            video['_id'] = str(video['_id'])
    except:
        videos = []
    return render_template('index.html', user=user, videos=videos)

@app.route('/trending')
def trending():
    user = session.get('user')
    try:
        videos = list(video_collection.find({'type': 'video'}).sort('views', -1).limit(10))
        for video in videos:
            video['_id'] = str(video['_id'])
    except:
        videos = []
    return render_template('index.html', user=user, videos=videos)

@app.route('/subscriptions')
def subscriptions():
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    try:
        videos = list(video_collection.find({'type': 'video'}).limit(10))
        for video in videos:
            video['_id'] = str(video['_id'])
    except:
        videos = []
    return render_template('index.html', user=user, videos=videos)

@app.route('/library')
def library():
    user = session.get('user')
    if not user:
        return redirect(url_for('login_page'))
    try:
        videos = list(video_collection.find({'user_id': user['user_id']}).sort('uploaded_at', -1))
        for video in videos:
            video['_id'] = str(video['_id'])
    except:
        videos = []
    return render_template('index.html', user=user, videos=videos)

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/video/<video_id>')
def video_page(video_id):
    user = session.get('user')
    try:
        vid = video_collection.find_one({'_id': ObjectId(video_id)})
        if not vid:
            return redirect(url_for('index'))
        
        video_collection.update_one({'_id': ObjectId(video_id)}, {'$inc': {'views': 1}})
        
        suggestions = list(video_collection.find({'_id': {'$ne': ObjectId(video_id)}, 'type': 'video'}).limit(6))
        for v in suggestions:
            v['_id'] = str(v['_id'])
        
        comments = list(comments_collection.find({'video_id': video_id}).sort('created_at', -1))
        for c in comments:
            c['_id'] = str(c['_id'])
            c['created_at'] = c['created_at'].strftime('%d/%m/%Y %H:%M')
        vid['_id'] = str(vid['_id'])
    except Exception:
        return redirect(url_for('index'))
    return render_template('video.html', user=user, video=vid, suggestions=suggestions, comments=comments)

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Datos incompletos'}), 400

    try:
        hashed_password = hashpw(data['password'].encode('utf-8'), gensalt()).decode('utf-8')
        new_user = {
            'username': data['username'],
            'email': data['email'],
            'password': hashed_password,
            'role': 'user',  # rol por defecto
            'created_at': datetime.datetime.now()
        }
        result = usuarios_collection.insert_one(new_user)
        logging.info(f"Usuario insertado: {result.inserted_id}")
        return jsonify({'message': 'Usuario registrado exitosamente', 'user_id': str(result.inserted_id)}), 201

    except DuplicateKeyError as e:
        logging.warning("Intento de registro duplicado: %s", e)
        return jsonify({'error': 'Usuario o email ya registrado'}), 400
    except Exception as e:
        logging.exception("Error al registrar usuario")
        return jsonify({'error': 'Error del servidor al registrar'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

    user = usuarios_collection.find_one({'username': data['username']})
    if not user:
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    if not checkpw(data['password'].encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': 'Usuario o contraseña incorrectos'}), 401

    session['user'] = {
        'user_id': str(user['_id']),
        'username': user['username'],
        'email': user['email'],
        'role': user.get('role', 'user')
    }
    return jsonify({'message': 'Login exitoso', 'user_id': str(user['_id']), 'username': user['username'], 'role': user.get('role', 'user')}), 200

# ---  RUTAS ADMIN ---

@app.route('/admin')
def admin_panel():
    user = session.get('user')
    if not user or not is_admin(user['user_id']):
        return redirect(url_for('index'))
    try:
        users = list(usuarios_collection.find().limit(200))
        videos = list(video_collection.find().sort('uploaded_at', -1).limit(200))
        comments = list(comments_collection.find().sort('created_at', -1).limit(200))

        for u in users:
            u['_id'] = str(u['_id'])
            u.pop('password', None)
        for v in videos:
            v['_id'] = str(v['_id'])
        for c in comments:
            c['_id'] = str(c['_id'])
            c['created_at'] = c['created_at'].strftime('%d/%m/%Y %H:%M') if hasattr(c['created_at'], 'strftime') else c.get('created_at')
    except Exception:
        users, videos, comments = [], [], []
    return render_template('admin.html', user=user, users=users, videos=videos, comments=comments)

@app.route('/api/user/<user_id>/role', methods=['PUT'])
def set_user_role(user_id):
    """Cambiar rol de usuario (solo admin)"""
    current_user = session.get('user')
    if not current_user or not is_admin(current_user['user_id']):
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json() or {}
    role = data.get('role')
    if role not in ('user', 'admin'):
        return jsonify({'error': 'Rol inválido'}), 400
    try:
        result = usuarios_collection.update_one({'_id': ObjectId(user_id)}, {'$set': {'role': role}})
        if result.matched_count == 0:
            return jsonify({'error': 'Usuario no encontrado'}), 404
        return jsonify({'message': 'Rol actualizado'}), 200
    except Exception:
        logging.exception("Error al cambiar rol")
        return jsonify({'error': 'Error del servidor'}), 500

@app.route('/api/video/<video_id>/code', methods=['PUT'])
def save_video_code(video_id):
    """Guardar/actualizar código asociado a un video (solo autor o admin)"""
    current_user = session.get('user')
    if not current_user:
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json() or {}
    code = data.get('code', '')
    try:
        video = video_collection.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video no encontrado'}), 404
        # autor o admin guardar

        if video['user_id'] != current_user['user_id'] and not is_admin(current_user['user_id']):
            return jsonify({'error': 'No autorizado'}), 403
        video_collection.update_one({'_id': ObjectId(video_id)}, {'$set': {'code': code}})
        return jsonify({'message': 'Código guardado'}), 200
    except Exception:
        logging.exception("Error al guardar código")
        return jsonify({'error': 'Error del servidor'}), 500

if __name__ == '__main__':
    app.run(debug=True)