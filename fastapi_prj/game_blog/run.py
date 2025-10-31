from uvicorn import run
from main import create_app


app = create_app()

if __name__ == '__main__':
    run('run:app', host='127.0.0.1', port=5000, reload=True)
