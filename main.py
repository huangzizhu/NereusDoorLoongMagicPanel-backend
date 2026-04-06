from gateway.app import Application
app = Application()

fastApiInstance = app.createApp()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:fastApiInstance", host="0.0.0.0", port=8000, reload=True)