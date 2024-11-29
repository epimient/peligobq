from app import app, db
from models import Barrio

# Función para poblar la base de datos
def populate_data():
    with app.app_context():
        barrios = [
            Barrio(nombre='El Prado', latitud=10.9993, longitud=-74.8006),
            Barrio(nombre='Alto Prado', latitud=11.0041, longitud=-74.8068),
            Barrio(nombre='Villa Country', latitud=10.9936, longitud=-74.8134),
            Barrio(nombre='Ciudad Jardín', latitud=10.9948, longitud=-74.8062),
            Barrio(nombre='Miramar', latitud=11.0232, longitud=-74.8201),
            Barrio(nombre='Boston', latitud=10.9941, longitud=-74.7947),
            Barrio(nombre='Porvenir', latitud=10.9884, longitud=-74.7872),
            Barrio(nombre='San Isidro', latitud=10.9867, longitud=-74.7891),
            Barrio(nombre='Simón Bolívar', latitud=10.9675, longitud=-74.7842),
            Barrio(nombre='Las Nieves', latitud=10.9643, longitud=-74.7685),
            Barrio(nombre='Rebolo', latitud=10.9637, longitud=-74.7714),
            Barrio(nombre='El Bosque', latitud=10.9514, longitud=-74.8033),
            Barrio(nombre='Los Andes', latitud=10.9864, longitud=-74.7922),
            Barrio(nombre='La Concepción', latitud=10.9862, longitud=-74.7994),
            Barrio(nombre='El Silencio', latitud=10.9841, longitud=-74.8089),
            Barrio(nombre='La Libertad', latitud=10.9849, longitud=-74.8151),
            Barrio(nombre='Las Mercedes', latitud=10.9902, longitud=-74.8076),
        ]
        db.session.add_all(barrios)
        db.session.commit()
        print("Datos insertados correctamente en la base de datos.")

# Ejecutar el script
if __name__ == "__main__":
    populate_data()
