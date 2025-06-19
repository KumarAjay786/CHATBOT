import os
import time
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.memory.buffer import ConversationBufferMemory
from django.utils import timezone
from chat.models import CustomUser

load_dotenv()


class ChatService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            api_key=os.getenv('OPENAI_API_KEY')
        )
        self.memory = ConversationBufferMemory()

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant named 'DjangoBot'. Respond concisely and helpfully."),
            ("human", "{input}")
        ])

        self.chain = self.prompt | self.llm

    def get_response(self, user_input, conversation_history=None):
        # Reset memory for each request
        self.memory.clear()

        # Load conversation history into memory
        if conversation_history:
            for msg in conversation_history:
                if msg['is_user']:
                    self.memory.chat_memory.add_user_message(msg['content'])
                else:
                    self.memory.chat_memory.add_ai_message(msg['content'])

        # Get AI response
        response = self.chain.invoke({"input": user_input})

        # Add to memory
        self.memory.chat_memory.add_ai_message(response.content)

        # Simulate typing delay
        time.sleep(max(1, min(len(response.content) / 50, 3)))

        return response.content


# Singleton instance
chat_service = ChatService()
