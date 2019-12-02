if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', port=8000, debug=True, access_log=False)
