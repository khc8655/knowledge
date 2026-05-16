# 知识库平台

上传文档 → 自动入库 → 随时查询 → 结果带原文出处

## 技术栈

- 后端: FastAPI + SQLite
- 前端: React + Vite + TailwindCSS
- 检索引擎: 复用 wiki_test v3.0

## 启动

```bash
# 后端
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8920 --workers 2

# 前端
cd frontend
npm install
npm run dev
```

## 环境变量

- `LLM_API_KEY` - LLM API key
- `LLM_BASE_URL` - API endpoint
- `LLM_MODEL` - 默认 Qwen/Qwen2.5-7B-Instruct
- `EMBEDDING_MODEL` - 默认 BAAI/bge-large-zh-v1.5
