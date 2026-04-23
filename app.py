import os
import json
import uuid
import asyncio
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import httpx
from github import Github
from dotenv import load_dotenv

load_dotenv()

# ==================== CONFIGURATION ====================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
HISTORY_FILE = "history.json"

# Detect Replit environment
IS_REPLIT = os.path.exists('/home/runner') or os.environ.get('REPL_ID') is not None
HOST_ENV = "replit" if IS_REPLIT else "local"

# ==================== FASTAPI SETUP ====================
app = FastAPI(title="DualMindAI v1.0", description="Dual Model AI Project Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

active_tasks = {}

# ==================== PYDANTIC MODELS ====================
class AnalyzeRequest(BaseModel):
    command: str

# ==================== HISTORY FUNCTIONS ====================
def load_history() -> List[Dict]:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history: List[Dict]):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

# ==================== DUAL MODEL DEEPSEEK CALLS ====================

async def call_deepseek_fast(messages: List[Dict]) -> Dict:
    """Model 1: Fast analyzer - 1-2 seconds response"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            }
        )
        if response.status_code != 200:
            raise Exception(f"API error: {response.text}")
        data = response.json()
        return json.loads(data["choices"][0]["message"]["content"])

async def call_deepseek_deep(messages: List[Dict]) -> Dict:
    """Model 2: Deep coder - 8-12 seconds with reasoning"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.2,
                "response_format": {"type": "json_object"}
            }
        )
        if response.status_code != 200:
            raise Exception(f"API error: {response.text}")
        data = response.json()
        return json.loads(data["choices"][0]["message"]["content"])

# ==================== STEP 1: SMART ANALYZER (Model 1) ====================

async def smart_analyze(command: str) -> Dict:
    """Model 1: Analyzes what code to write, where to host, etc."""
    
    system_prompt = f"""You are a Smart Software Architect. Analyze the user's request and determine:
1. What type of code to write (Python, JavaScript, Node.js, React, etc.)
2. How it will be hosted (Replit environment detected: {HOST_ENV})
3. Project structure for Replit compatibility

Return JSON with:
{{
    "detected_language": "python|javascript|typescript|go|rust",
    "framework": "fastapi|express|react|flask|none",
    "project_type": "web_app|api|bot|cli|automation",
    "replit_compatible": true,
    "files_needed": ["main.py", "requirements.txt", "README.md"],
    "main_file": "main.py",
    "start_command": "python main.py",
    "reasoning": "Brief explanation of why this tech stack",
    "benefits": ["benefit1", "benefit2"],
    "complexity": "simple|medium|complex"
}}

Important: Since hosting is on Replit, ensure:
- Use environment variables for secrets (os.getenv for Python, process.env for Node)
- Use PORT environment variable for web servers
- Include proper requirements.txt or package.json
- Main file should be runnable directly"""

    return await call_deepseek_fast([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this request (hosting: Replit): {command}"}
    ])

# ==================== STEP 2: CODE GENERATOR (Model 2) ====================

async def smart_generate(command: str, analysis: Dict, task_id: str, send_progress) -> Dict:
    """Model 2: Generates actual code with deep reasoning"""
    
    await send_progress(f"🧠 Model 2 (Deep Coder) activated...", 10)
    await send_progress(f"📊 Detected: {analysis.get('detected_language', 'unknown')} with {analysis.get('framework', 'none')}", 15)
    
    language = analysis.get('detected_language', 'python')
    
    if language == 'python':
        system_prompt = f"""You are a Senior Python Developer. Write production-ready code for Replit hosting.
        
Project Analysis: {json.dumps(analysis, indent=2)}
User Request: {command}

Return JSON with:
{{
    "summary": "Brief explanation",
    "files": [
        {{"path": "main.py", "content": "code here"}},
        {{"path": "requirements.txt", "content": "dependencies"}},
        {{"path": "README.md", "content": "setup instructions"}}
    ]
}}

Replit-specific requirements:
- Use `os.getenv('PORT', 8000)` for port
- Use `if __name__ == "__main__":` block
- Include error handling
- Add docstrings and comments
- Use `.env` for sensitive data"""

    elif language == 'javascript' or analysis.get('framework') == 'express':
        system_prompt = f"""You are a Senior Node.js Developer. Write production-ready code for Replit hosting.
        
Return JSON with files: server.js, package.json, README.md

Replit-specific:
- Use `process.env.PORT` for port
- Include proper error handling
- Add console logs for debugging"""

    elif analysis.get('framework') == 'react':
        system_prompt = f"""You are a Senior React Developer. Write production-ready code for Replit hosting.
        
Return JSON with files: App.js, package.json, index.html, README.md

Replit-specific:
- Use Vite or Create React App structure
- Include proper build scripts"""

    else:
        system_prompt = f"""You are a Senior Developer. Write production-ready code for Replit hosting in {language}.
        
Return JSON with appropriate files for {language}."""

    await send_progress(f"🔧 Generating {analysis.get('files_needed', ['code'])[0]}...", 30)
    
    response = await call_deepseek_deep([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate complete project for: {command}\n\nAnalysis: {json.dumps(analysis, indent=2)}"}
    ])
    
    files = response.get('files', [])
    total = len(files)
    
    for i, file in enumerate(files):
        await send_progress(f"📝 Creating {file['path']}... ({i+1}/{total})", 30 + int((i/total) * 60))
        await asyncio.sleep(0.1)
    
    await send_progress(f"✅ Generation complete! {total} files created.", 95)
    
    return {
        "summary": response.get('summary', 'Project generated'),
        "files": files,
        "total_files": total,
        "language": language,
        "start_command": analysis.get('start_command', 'python main.py')
    }

# ==================== SSE PROGRESS STREAM ====================

async def progress_generator(task_id: str):
    if task_id not in active_tasks:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Task not found'})}\n\n"
        return
    
    task = active_tasks[task_id]
    
    while True:
        if task['status'] == 'completed':
            yield f"data: {json.dumps({'type': 'complete', 'project': task['result']})}\n\n"
            break
        elif task['status'] == 'error':
            yield f"data: {json.dumps({'type': 'error', 'message': task['error']})}\n\n"
            break
        
        if task.get('progress_messages'):
            for msg in task['progress_messages']:
                yield f"data: {json.dumps({'type': 'progress', 'message': msg['text'], 'percentage': msg.get('percentage')})}\n\n"
            task['progress_messages'] = []
        
        await asyncio.sleep(0.5)

# ==================== API ENDPOINTS ====================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "is_replit": IS_REPLIT})

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    try:
        analysis = await smart_analyze(request.command)
        task_id = str(uuid.uuid4())[:8]
        
        active_tasks[task_id] = {
            "command": request.command,
            "analysis": analysis,
            "status": "analyzed",
            "progress_messages": []
        }
        
        return {
            "success": True,
            "task_id": task_id,
            "analysis": analysis,
            "host_env": HOST_ENV
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate/{task_id}")
async def generate_project(task_id: str):
    if task_id not in active_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = active_tasks[task_id]
    task['status'] = 'generating'
    task['progress_messages'] = []
    
    async def send_progress(message: str, percentage: int = None):
        task['progress_messages'].append({
            'text': message,
            'percentage': percentage,
            'timestamp': datetime.now().isoformat()
        })
    
    try:
        result = await smart_generate(
            task['command'],
            task['analysis'],
            task_id,
            send_progress
        )
        
        project_id = str(uuid.uuid4())[:8]
        project_data = {
            "id": project_id,
            "command": task['command'],
            "analysis": task['analysis'],
            "summary": result['summary'],
            "files": result['files'],
            "language": result['language'],
            "timestamp": datetime.now().isoformat()
        }
        
        history = load_history()
        history.insert(0, project_data)
        save_history(history)
        
        task['status'] = 'completed'
        task['result'] = {
            "project_id": project_id,
            "summary": result['summary'],
            "files": result['files'],
            "total_files": result['total_files'],
            "language": result['language'],
            "start_command": result.get('start_command', 'python main.py')
        }
        
        return {"success": True}
        
    except Exception as e:
        task['status'] = 'error'
        task['error'] = str(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/progress/{task_id}")
async def get_progress(task_id: str):
    return StreamingResponse(
        progress_generator(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/history")
async def get_history():
    return {"history": load_history()}

@app.post("/api/push-to-github")
async def push_to_github(project_id: str, repo_name: str):
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=400, detail="GitHub token not configured")
    
    history = load_history()
    project = None
    for p in history:
        if p['id'] == project_id:
            project = p
            break
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        
        repo = user.create_repo(
            name=repo_name,
            description=project.get('analysis', {}).get('reasoning', 'Generated by DualMindAI v1.0'),
            private=False,
            auto_init=False
        )
        
        for file in project.get('files', []):
            try:
                repo.create_file(
                    path=file['path'],
                    message=f"Add {file['path']}",
                    content=file['content'],
                    branch="main"
                )
            except Exception as e:
                print(f"Error: {e}")
        
        return {"success": True, "repo_url": repo.html_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))