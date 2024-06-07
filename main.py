from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 设置允许的源
origins = [
    "http://localhost:5173",  # 替换为你的前端地址
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logging.info("Received file upload request")
    try:
        contents = await file.read()
        filename = file.filename
        logging.info(f"Received file: {filename}")

        with open(filename, 'wb') as f:
            f.write(contents)
        logging.info(f"Saved file to disk: {filename}")

        if filename.endswith('.csv'):
            df = pd.read_csv(filename)
            logging.info("File read as CSV")
        elif filename.endswith('.xlsx'):
            df = pd.read_excel(filename)
            logging.info("File read as Excel")
        else:
            os.remove(filename)
            logging.error("Unsupported file type")
            raise HTTPException(status_code=400, detail="不支持的文件类型")

        # 在这里可以对数据进行进一步处理
        logging.info(f"Data preview:\n{df.head()}")

        os.remove(filename)
        logging.info(f"Removed file from disk: {filename}")

        return JSONResponse(content={"message": "文件上传和读取成功"}, status_code=200)

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)