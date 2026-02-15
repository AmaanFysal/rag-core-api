from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def generate_answer(question: str, context: str) -> str:

    system_prompt = """
You are an AI assistant.
Answer ONLY using the provided context.
If the answer is not in the context, say:
"I cannot find this information in the uploaded documents."
"""

    user_prompt = f"""
Context:
{context}

Question:
{question}
"""

    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content
