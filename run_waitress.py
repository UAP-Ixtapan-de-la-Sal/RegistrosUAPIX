from waitress import serve
from config.wsgi import application  # Nombre de la carpeta de proyecto

if __name__ == '__main__':
    print("Iniciando Waitress en http://127.0.0.1:8000 ...")
    serve(application, host='127.0.0.1', port=8000)