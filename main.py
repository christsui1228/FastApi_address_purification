from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse, Response
import pandas as pd
import os
import logging
from uuid import uuid4

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

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application!"}

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # 提供一个默认的 favicon 响应
    return Response(status_code=204)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    logging.info("Received file upload request")
    try:
        contents = await file.read()
        filename = file.filename
        logging.info(f"Received file: {filename}")

        # 使用唯一标识符创建临时文件名，避免文件名冲突
        unique_id = uuid4().hex
        temp_file_path = f"/tmp/{unique_id}_{filename}"
        with open(temp_file_path, 'wb') as f:
            f.write(contents)
        logging.info(f"Saved file to disk: {temp_file_path}")

        try:
            # 根据文件扩展名选择读取方式
            if filename.endswith('.xlsx') or filename.endswith('.xls'):
                df = pd.read_excel(temp_file_path)
            elif filename.endswith('.csv'):
                df = pd.read_csv(temp_file_path)
            else:
                raise HTTPException(status_code=400, detail="Unsupported file format")

            # 获取所有列名
            columns = df.columns

            # 创建一个空的 'sizes' 列
            df['sizes'] = ''

            # 遍历所有列（从第二列开始）
            for column_name in columns[1:]:
                new_column_name = f'size_{column_name}'
                df[new_column_name] = ''
                # 处理每一列的数据，并生成新的列
                df.loc[df[column_name] > 0, new_column_name] = column_name + '*' + df[column_name].fillna(0).astype(int).astype(str) + ','
                # 将新增的列内容合并到 'sizes' 列中
                df['sizes'] += df[new_column_name]

            # 删除所有新增的列
            df.drop(columns=[f'size_{column_name}' for column_name in columns[1:]], inplace=True)

            # 保存处理后的文件
            processed_file_path = f"/tmp/processed_{unique_id}_{filename}.csv"
            df.to_csv(processed_file_path, index=False)
            logging.info(f"Processed file saved to: {processed_file_path}")

            return JSONResponse(content={"message": "文件上传和处理成功", "processed_file_url": f"/download/processed_{unique_id}_{filename}.csv"}, status_code=200)

        finally:
            os.remove(temp_file_path)
            logging.info(f"Removed original file from disk: {temp_file_path}")

    except Exception as e:
        logging.error(f"Error processing file: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = f"/tmp/{file_name}"
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=file_name)
    else:
        raise HTTPException(status_code=404, detail="File not found")