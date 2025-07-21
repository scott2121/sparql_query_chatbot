from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from .models import Conversation, ChatMessage
from .database import get_session, create_db_and_tables
from typing import Optional
from pydantic import BaseModel

import asyncio

from flair.data import Sentence
from flair.models import EntityMentionLinker
from flair.nn import Classifier

print("Loading models...")
tagger = Classifier.load("hunflair2")
species_linker = EntityMentionLinker.load("species-linker")
gene_linker = EntityMentionLinker.load("gene-linker")
print("Loading models... Done")

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

class ConversationCreate(BaseModel):
    title: str

class AddMessageRequest(BaseModel):
    user_question: Optional[str]
    sparql_query: str
    assistant_answer: str


@app.post("/conversations/")
async def create_conversation(conversation_data: ConversationCreate, session: Session = Depends(get_session)):
    conversation = Conversation(title=conversation_data.title)
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation

# Add a message to a conversation
@app.post("/conversations/{conversation_id}/messages/")
async def add_message(
    conversation_id: int,
    message_request: AddMessageRequest,  # リクエストボディを Pydantic モデルとして受け取る
    session: Session = Depends(get_session)
):
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # 新しいメッセージを作成
    message = ChatMessage(
        conversation_id=conversation_id,
        user_question=message_request.user_question,
        sparql_query=message_request.sparql_query,
        assistant_answer=message_request.assistant_answer,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

# Retrieve all messages in a conversation
@app.get("/conversations/{conversation_id}/messages/")
async def get_conversation_messages(conversation_id: int, session: Session = Depends(get_session)):
    conversation = session.get(Conversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = session.exec(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id)).all()
    return {"conversation": conversation, "messages": messages}

# Retrieve all conversations
@app.get("/conversations/")
# Retrieve all conversations
@app.get("/conversations")
async def get_conversations(session: Session = Depends(get_session)):
    conversations = session.exec(select(Conversation)).all()
    if not conversations:
        return []

    return [
        {
            "conversation_id": conversation.id,
            "title": conversation.title or f"Conversation {conversation.id}",
            "created_at": conversation.created_at
        }
        for conversation in conversations
    ]


async def predict_gene(user_input):
    sentence = Sentence(user_input)
    tagger.predict(sentence)
    gene_linker.predict(sentence)
    return sentence


async def predict_species(user_input):
    sentence = Sentence(user_input)
    tagger.predict(sentence)
    species_linker.predict(sentence)
    return sentence


@app.post("/huflair2/")
async def huflair2(user_input: str):
    sentence_gene, sentence_species = await asyncio.gather(
        predict_gene(user_input),
        predict_species(user_input)
    )

    normalized_sentence = user_input
    for entity in sentence_gene.get_labels("link"):
        print(entity)
        original_entity = str(entity).split('"')[1].split('"')[0]
        normalized_entity = str(entity).split(" → ")[1].split("/")[0] + " (uniprot_ncbigene)"
        normalized_sentence = normalized_sentence.replace(original_entity, 'ncbigene:'+normalized_entity)
    
    for entity in sentence_species.get_labels("link"):
        original_entity = str(entity).split('"')[1].split('"')[0]
        normalized_entity = str(entity).split("=")[1].split(" (")[0] + " (taxonomy_scientific_name)"
        normalized_sentence = normalized_sentence.replace(original_entity, normalized_entity)
    
    return normalized_sentence