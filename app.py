from flask import Flask, render_template, request, redirect, url_for
from config import create_app, db
from models import Usuario, Barrio, Rating
import folium
import matplotlib.pyplot as plt
import io
import base64
from transformers import pipeline

# Inicializar el pipeline de análisis de sentimientos
sentiment_pipeline = pipeline("sentiment-analysis", model="finiteautomata/beto-sentiment-analysis")

# Función de análisis combinado (reglas + BETO)
def analizar_sentimiento_combinado(texto):
    # Listas de palabras clave
    palabras_positivas = ["seguro", "tranquilo", "bueno", "excelente", "positivo", "maravilloso", "cómodo", "agradable", "pacifico"]
    palabras_negativas = ["inseguro", "peligroso", "atraco", "roban", "malo", "horrible", "negativo", "conflictivo", "violento", "amenazante"]

    # Convertir el texto a minúsculas para facilitar la comparación
    texto = texto.lower()

    # Buscar palabras negativas primero
    for palabra in palabras_negativas:
        if palabra in texto:
            return {"sentimiento": "NEG", "confianza": 1.0}

    # Buscar palabras positivas
    for palabra in palabras_positivas:
        if palabra in texto:
            return {"sentimiento": "POS", "confianza": 1.0}

    # Si no hay coincidencias claras, usar el modelo BETO
    resultado = sentiment_pipeline(texto)
    return {
        "sentimiento": resultado[0]['label'],
        "confianza": resultado[0]['score']
    }

# Inicializar la aplicación Flask
app = create_app()

# Crear tablas y agregar datos iniciales
with app.app_context():
    db.create_all()

    # Datos iniciales para pruebas (solo si están vacíos)
    if Usuario.query.count() == 0:
        usuarios = [
            Usuario(nombre='Carlos Pérez', correo='carlos@example.com'),
            Usuario(nombre='Ana Gómez', correo='ana@example.com'),
            Usuario(nombre='Luis Martínez', correo='luis@example.com'),
        ]
        db.session.add_all(usuarios)
        db.session.commit()


@app.route('/')
def index():
    barrios = Barrio.query.all()  # Obtener todos los barrios

    # Crear el mapa con Folium
    mapa = folium.Map(location=[10.96854, -74.78132], zoom_start=12)  # Ubicación inicial en Barranquilla
    for barrio in barrios:
        nivel = Rating.query.filter_by(barrio_id=barrio.id).with_entities(db.func.avg(Rating.nivel_peligrosidad)).scalar()
        if nivel is None:
            nivel = 0  # Valor predeterminado si no hay ratings
        color = "green" if nivel <= 2 else "orange" if nivel <= 4 else "red"
        folium.Marker(
            location=[barrio.latitud, barrio.longitud],
            popup=f"{barrio.nombre}: {nivel:.1f}" if nivel > 0 else f"{barrio.nombre}: Sin datos",
            icon=folium.Icon(color=color)
        ).add_to(mapa)

    # Convertir el mapa a HTML
    mapa_html = mapa._repr_html_()

    return render_template('index.html', barrios=barrios, mapa_html=mapa_html)


@app.route('/mapa')
def mapa():
    mapa = folium.Map(location=[10.96854, -74.78132], zoom_start=12)  # Barranquilla
    barrios = Barrio.query.all()
    for barrio in barrios:
        # Determinar color según nivel de peligrosidad
        nivel = Rating.query.filter_by(barrio_id=barrio.id).with_entities(db.func.avg(Rating.nivel_peligrosidad)).scalar()
        if nivel is None:
            nivel = 0  # Valor predeterminado si no hay ratings
        color = "green" if nivel <= 2 else "orange" if nivel <= 4 else "red"
        folium.Marker(
            location=[barrio.latitud, barrio.longitud],
            popup=f"{barrio.nombre}: {nivel:.1f}" if nivel > 0 else f"{barrio.nombre}: Sin datos",
            icon=folium.Icon(color=color)
        ).add_to(mapa)
    
    # Renderizar el mapa como HTML sin guardarlo en el disco
    map_html = mapa._repr_html_()
    return render_template('mapa.html', map_html=map_html)


@app.route('/add_barrio', methods=['POST'])
def add_barrio():
    nombre = request.form.get('nombre')
    latitud = float(request.form.get('latitud'))
    longitud = float(request.form.get('longitud'))
    nuevo_barrio = Barrio(nombre=nombre, latitud=latitud, longitud=longitud)
    db.session.add(nuevo_barrio)
    db.session.commit()
    return redirect(url_for('index', message="Barrio añadido con éxito"))


@app.route('/rate', methods=['GET', 'POST'])
def rate():
    if request.method == 'POST':
        # Validar que los IDs existan en la base de datos
        usuario_id = request.form.get('usuario_id')
        barrio_id = request.form.get('barrio_id')
        nivel_peligrosidad = request.form.get('nivel_peligrosidad')
        comentario = request.form.get('comentario')

        if not (usuario_id and barrio_id and nivel_peligrosidad):
            return "Por favor, complete todos los campos", 400

        # Convertir valores y manejar errores
        try:
            usuario_id = int(usuario_id)
            barrio_id = int(barrio_id)
            nivel_peligrosidad = int(nivel_peligrosidad)

            # Validar que los IDs existan
            usuario = Usuario.query.get(usuario_id)
            barrio = Barrio.query.get(barrio_id)

            if not usuario or not barrio:
                return "Usuario o barrio no encontrado", 404

            # Crear un nuevo registro en la tabla Rating
            nuevo_rating = Rating(
                usuario_id=usuario_id,
                barrio_id=barrio_id,
                nivel_peligrosidad=nivel_peligrosidad,
                comentario=comentario
            )
            db.session.add(nuevo_rating)
            db.session.commit()
            return redirect(url_for('index', message="Calificación registrada con éxito"))
        except ValueError:
            return "Datos inválidos", 400

    # Para método GET, renderizamos el formulario
    barrios = Barrio.query.all()
    usuarios = Usuario.query.all()
    return render_template('rate.html', barrios=barrios, usuarios=usuarios)


@app.route('/grafica')
def grafica():
    barrios = Barrio.query.all()
    nombres = []
    promedios = []
    colores = []

    for barrio in barrios:
        promedio = Rating.query.filter_by(barrio_id=barrio.id).with_entities(db.func.avg(Rating.nivel_peligrosidad)).scalar()
        if promedio is not None:
            nombres.append(barrio.nombre)
            promedios.append(promedio)
            # Asignar color según el nivel de peligrosidad
            if promedio <= 2:
                colores.append('green')
            elif promedio <= 4:
                colores.append('orange')
            else:
                colores.append('red')

    # Crear la gráfica con colores y etiquetas
    plt.figure(figsize=(10, 5))
    bars = plt.bar(nombres, promedios, color=colores)
    plt.title('Promedio de Peligrosidad por Barrio')
    plt.xlabel('Barrios')
    plt.ylabel('Nivel Promedio de Peligrosidad (1 a 5)')
    plt.xticks(rotation=45, ha='right')

    # Añadir etiquetas sobre las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, f'{height:.1f}', ha='center', va='bottom')

    # Guardar la gráfica como imagen
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Codificar la imagen en base64
    img_base64 = base64.b64encode(img.getvalue()).decode('utf8')
    return render_template('grafica.html', img_base64=img_base64)

@app.route('/analisis')
def analisis():
    # Obtener comentarios de la base de datos
    comentarios = Rating.query.with_entities(Rating.comentario, Rating.fecha).all()
    comentarios = [{"comentario": c[0], "fecha": c[1]} for c in comentarios if c[0]]

    # Inicializar contadores de sentimientos
    positivos = 0
    negativos = 0
    neutrales = 0
    fechas = []
    sentimientos = []

    # Inicializar extremos
    comentario_positivo = {"comentario": "Sin comentarios positivos", "sentimiento": "N/A"}
    comentario_negativo = {"comentario": "Sin comentarios negativos", "sentimiento": "N/A"}

    if comentarios:
        for item in comentarios:
            comentario = item["comentario"]
            fecha = item["fecha"]

            # Analizar sentimiento del comentario
            resultado = analizar_sentimiento_combinado(comentario)
            sentimiento = resultado["sentimiento"]

            # Actualizar contadores
            if sentimiento == "POS":
                positivos += 1
                # Guardar el primer comentario positivo encontrado
                if comentario_positivo["comentario"] == "Sin comentarios positivos":
                    comentario_positivo = {"comentario": comentario, "sentimiento": "Positivo"}
            elif sentimiento == "NEG":
                negativos += 1
                # Guardar el primer comentario negativo encontrado
                if comentario_negativo["comentario"] == "Sin comentarios negativos":
                    comentario_negativo = {"comentario": comentario, "sentimiento": "Negativo"}
            else:
                neutrales += 1

            # Guardar fecha y sentimiento para la línea de tiempo
            fechas.append(fecha)
            sentimientos.append(sentimiento)

    # Crear gráfico de torta
    plt.figure(figsize=(6, 6))
    labels = ['Positivos', 'Negativos', 'Neutrales']
    valores = [positivos, negativos, neutrales]
    colores = ['green', 'red', 'blue']
    plt.pie(valores, labels=labels, autopct='%1.1f%%', colors=colores, startangle=140)
    plt.title('Distribución de Sentimientos')
    img_torta = io.BytesIO()
    plt.savefig(img_torta, format='png')
    img_torta.seek(0)
    plt.close()

    # Crear gráfico de línea de tiempo
    if fechas:
        sentimiento_valores = [1 if s == "POS" else -1 if s == "NEG" else 0 for s in sentimientos]
        plt.figure(figsize=(10, 5))
        plt.plot(fechas, sentimiento_valores, marker='o', linestyle='-', color='blue')
        plt.axhline(0, color='gray', linewidth=0.8, linestyle='--')
        plt.title('Sentimientos a lo Largo del Tiempo')
        plt.xlabel('Fecha')
        plt.ylabel('Sentimiento')
        plt.xticks(rotation=45, ha='right')
        img_linea = io.BytesIO()
        plt.savefig(img_linea, format='png')
        img_linea.seek(0)
        plt.close()
        img_linea_base64 = base64.b64encode(img_linea.getvalue()).decode('utf8')
    else:
        img_linea_base64 = None

    # Codificar gráfico de torta en base64
    img_torta_base64 = base64.b64encode(img_torta.getvalue()).decode('utf8')

    return render_template(
        'analisis.html',
        img_torta=img_torta_base64,
        img_linea=img_linea_base64,
        comentario_positivo=comentario_positivo,
        comentario_negativo=comentario_negativo,
    )

@app.route('/buscar', methods=['GET'])
def buscar():
    query = request.args.get('search', '')  # Obtener texto ingresado en la búsqueda
    resultados = Barrio.query.filter(Barrio.nombre.contains(query)).all()  # Buscar coincidencias por nombre
    return render_template('buscar.html', query=query, resultados=resultados)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Procesar inicio de sesión (validar usuario y contraseña)
        pass
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Procesar registro (guardar nuevo usuario)
        pass
    return render_template('register.html')


if __name__ == '__main__':
    app.run(debug=True)
