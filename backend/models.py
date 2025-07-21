from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List, Optional

class Conversation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None)  # Title of the conversation
    created_at: datetime = Field(default_factory=datetime.utcnow)

    messages: List["ChatMessage"] = Relationship(back_populates="conversation")

class ChatMessage(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", nullable=False)
    user_question: Optional[str] = Field(default=None)  # User's input message
    sparql_query: Optional[str] = Field(default=None)  # SPARQL query generated
    assistant_answer: Optional[str] = Field(default=None)  # Bot's response
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    conversation: Conversation = Relationship(back_populates="messages")
