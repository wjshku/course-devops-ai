import os
from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# 1. 检查 API Key
# 在 AWS App Runner 中，这将由 AWS Secrets Manager 安全注入
if "OPENAI_API_KEY" not in os.environ:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

# --- 应用启动时：加载模型和向量 ---
print("Loading RAG model and vector store...")
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.load_local(
    "faiss_index", 
    embeddings, 
    # 兼容最新版 LangChain
    allow_dangerous_deserialization=True 
)
retriever = vectorstore.as_retriever()

# RAG 的 Prompt 模板
prompt_template = """Use the following pieces of context to answer the question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Context: {context}
Question: {question}
Helpful Answer:"""
QA_PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])

# LLM 模型
llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

# RAG Chain
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs={"prompt": QA_PROMPT}
)
print("✅ RAG Application is ready.")
# --- 加载完成 ---

app = FastAPI()

class Query(BaseModel):
    question: str

@app.get("/")
def read_root():
    return {"message": "BEE EDU RAG Application is live!"}

@app.post("/chat")
def chat(query: Query):
    try:
        # 调用 RAG chain
        result = rag_chain.invoke({"query": query.question})
        return {"answer": result['result']}
    except Exception as e:
        # 返回错误信息
        return {"error": str(e)}, 500