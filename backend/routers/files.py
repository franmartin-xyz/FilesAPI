import os
import tempfile
import mimetypes
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
import traceback

from database import SessionLocal, engine
from models import FileUpload as FileUploadModel, Conversation as ConversationModel
from adapters.anthropic_adapter import AnthropicClient

router = APIRouter(prefix="/api/files", tags=["files"])

# Pydantic models
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    created_at: datetime
    mime_type: Optional[str] = None
    session_id: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    file_id: str

class ChatResponse(BaseModel):
    response: str

# Initialize Anthropic client
llm = AnthropicClient(api_key=os.getenv("LLM_API_KEY"))

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = Form(""),  # Make session_id optional with empty string as default
    db: Session = Depends(get_db)
):
    """Upload a file to Anthropic's storage."""
    temp_file_path = None
    try:
        print(f"📤 Starting file upload for {file.filename} (size: {file.size} bytes)")
        
        # Generate a new session ID if none provided
        if not session_id:
            session_id = str(uuid.uuid4())
            print(f"🆕 Generated new session ID: {session_id}")
        else:
            print(f"🔑 Using provided session ID: {session_id}")
            
        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
            print(f"💾 Saved file to temporary location: {temp_file_path}")
        
        # Upload to Anthropic
        print("⬆️  Uploading file to Anthropic...")
        result = await llm.upload_file(temp_file_path)
        print(f"✅ File uploaded to Anthropic. Response: {result}")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        print(f"📄 Detected MIME type: {mime_type}")
        
        # Ensure the result has the expected fields
        if not result or not isinstance(result, dict):
            raise ValueError(f"Unexpected response from Anthropic: {result}")
            
        if "id" not in result:
            raise ValueError(f"Missing 'id' in Anthropic response: {result}")
            
        if "bytes" not in result:
            print(f"⚠️ 'bytes' field not found in Anthropic response. Available keys: {list(result.keys())}")
            result["bytes"] = file.size  # Fall back to original file size
        
        # Save file metadata to database
        file_record = FileUploadModel(
            session_id=session_id,
            file_id=result["id"],
            filename=file.filename,
            size=result.get("bytes", file.size),  # Fall back to file.size if bytes is missing
            mime_type=mime_type,
            created_at=datetime.utcnow()
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        print(f"💾 Saved file metadata to database. ID: {file_record.id}")
        
        response_data = {
            "file_id": result["id"],
            "filename": file.filename,
            "size": result.get("bytes", file.size),
            "created_at": file_record.created_at,
            "mime_type": mime_type,
            "session_id": session_id
        }
        print(f"📤 Sending response: {response_data}")
        
        return response_data
        
    except Exception as e:
        error_msg = f"❌ Error during file upload: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"🧹 Deleted temporary file: {temp_file_path}")
            except Exception as e:
                print(f"⚠️ Error deleting temporary file: {e}")

@router.post("/chat", response_model=ChatResponse)
async def chat_with_file(
    request: ChatRequest,
    session_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """Chat with the AI using an uploaded file."""
    try:
        # Verify the file belongs to this session
        file_record = db.query(FileUploadModel).filter(
            FileUploadModel.session_id == session_id,
            FileUploadModel.file_id == request.file_id
        ).first()
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or access denied"
            )
        
        # Convert messages to the format expected by Anthropic
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Get response from Anthropic
        response = await llm.chat_with_file(
            messages=messages,
            file_id=request.file_id
        )
        
        # Save the conversation to database
        conversation = ConversationModel(
            session_id=session_id,
            file_id=request.file_id,
            messages=[msg.dict() for msg in request.messages],
            response=response,
            created_at=datetime.utcnow()
        )
        db.add(conversation)
        db.commit()
        
        return {"response": response}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_files(
    session_id: str,
    db: Session = Depends(get_db)
):
    """List all files uploaded in the current session."""
    try:
        files = db.query(FileUploadModel).filter(
            FileUploadModel.session_id == session_id
        ).order_by(FileUploadModel.created_at.desc()).all()
        
        return [
            {
                "file_id": f.file_id,
                "filename": f.filename,
                "size": f.size,
                "mime_type": f.mime_type,
                "created_at": f.created_at.isoformat()
            }
            for f in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
