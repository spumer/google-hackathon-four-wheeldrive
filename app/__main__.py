from .api import app

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, port=5000, debug=True, access_log=False)
