from gateway.app import Application
app = Application()
fastApiInstance = app.createApp()
FILE_LIMIT = 3 * 1024**3
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:fastApiInstance", host="0.0.0.0", port=8000, reload=True,h11_max_incomplete_event_size=FILE_LIMIT)
