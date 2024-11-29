from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Inicialización de SQLAlchemy
db = SQLAlchemy()

def create_app():
    """Función para crear la aplicación Flask con configuración inicial."""
    app = Flask(__name__)
    
    # Configuración de la base de datos
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar SQLAlchemy con la app
    db.init_app(app)
    
    return app
