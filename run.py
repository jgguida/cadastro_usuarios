import uvicorn
import os

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, root_path=os.path.dirname(os.path.abspath(__file__))) 