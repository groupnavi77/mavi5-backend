import uvicorn

if __name__ == "__main__":
    # La aplicación se pasa como un string con el formato "modulo.archivo:aplicacion"
    # Asegúrate de reemplazar 'mi_proyecto_core'
    uvicorn.run("app.asgi:application", host="127.0.0.1", port=8000, reload=True)