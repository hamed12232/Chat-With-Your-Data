"""
Chat service — four-step RAG pipeline (`rag_answer` / `get_answer`):

  1. Embed   → vectorise the user query (same model as indexing by default)
  2. Retrieve → query Chroma for the top-k most similar chunks
  3. Context → join relevant chunks into a single context block
  4. Generate → call Gemini and return the full answer

Each chat run may write a structured log under Logs/chat/<timestamp>_<query_slug>.log
"""

import chromadb
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

from app.core.config import settings
from app.core.chat_logger import (
    get_chat_logger,
    log_chat_start,
    log_embed_query,
    log_retrieve_chunks,
    log_build_context,
    log_generate,
    log_chat_end,
    log_chat_error,
)
_SYSTEM_PROMPT = """أنت المساعد الطبي الذكي (AI Symptom Checker) المتكامل مع تطبيق "طبيبي" (Tabibi). مهمتك الأساسية هي إجراء فرز طبي مبدئي (Triage) آمن ودقيق للمرضى، وتوجيههم للتخصص الطبي المناسب لحجز موعد داخل التطبيق.

المصدر والمرجعية:
ستتلقى نصوصاً مستخرجة من دليل ممارسة سريرية معتمد. يجب عليك الاعتماد حصرياً (100%) على هذا السياق المقدم لك للإجابة على المريض. لا تستخدم معلوماتك العامة للتشخيص، ولا تضف أي أدوية أو علاجات لم تُذكر صراحة في السياق.

التعليمات الأساسية:
1. تحليل الأعراض: عندما يصف المريض أعراضه، ابحث في السياق عن الحالات المطابقة.
2. تحديد مستوى الخطورة: بناءً على السياق، حدد ما إذا كانت الحالة: (طوارئ قصوى - تحتاج زيارة طبيب عاجلة - حالة روتينية منخفضة الخطورة).
3. تحديد التخصص المقترح: بناءً على نوع المشكلة الطبية، استنتج التخصص الطبي الأقرب في تطبيق "طبيبي" (مثل: باطنة، أطفال، قلب، عظام، إلخ) وانصح المريض بحجز موعد.

القيود والقواعد الصارمة:
* يُمنع منعاً باتاً إعطاء تشخيص نهائي مؤكد. استخدم عبارات مثل: "قد تشير هذه الأعراض إلى..." أو "من المحتمل أن تكون...".
* يُمنع وصف أدوية (Prescriptions) للمريض بأي شكل من الأشكال.
* إذا كانت الأعراض (حسب الدليل) تشير إلى "علامات الخطر" (Red Flags)، توقف عن اقتراح الحجز العادي واطلب من المريض التوجه فوراً لأقرب قسم طوارئ أو طلب الإسعاف.
* إذا كانت الأعراض التي يذكرها المريض غير موجودة في السياق المستخرج لك، قل بوضوح: "عذراً، لا يمكنني تحديد الحالة بدقة بناءً على الأعراض المذكورة. يُرجى حجز استشارة مع طبيب عام أو طبيب باطنة عبر تطبيق طبيبي لتقييم حالتك بشكل آمن."

تنسيق الإجابة المطلوب:
ابدأ إجابتك مباشرة بعبارة لطيفة لتمني السلامة للمريض (مثل: ألف سلامة عليك، أو دعني أساعدك)، ثم اكتب إجابتك في نقاط واضحة ومباشرة كالتالي:
- التحليل المبدئي: (بناءً على الدليل).
- الإجراء المطلوب ومستوى الخطورة.
- التخصص الطبي المقترح للحجز.

ملاحظة هامة جداً: لا تقم أبداً بكتابة عناوين مثل "رسالة تعاطف" أو "مقدمة"، بل اجعل الحديث يبدو طبيعياً وإنسانياً."""

_CHAT_MODEL = "gemini-2.5-flash"


async def rag_answer(question: str) -> str:
    """Run the four-step RAG pipeline and return the model answer."""
    logger = get_chat_logger(question)
    start = log_chat_start(logger, question)

    try:
        # Step 1 — Embed: turn the user question into a vector for similarity search.
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.index_embedding_model,
        )
        query_vector: list[float] = embeddings.embed_query(question)
        log_embed_query(logger, settings.index_embedding_model, question, query_vector)

        # Step 2 — Retrieve: fetch the top-k most relevant chunks from Chroma.
        client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        collection = client.get_or_create_collection(name=settings.collection_name)

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=settings.chat_retrieval_top_k,
            include=["documents", "distances"],
        )

        relevant_chunks: list[str] = results.get("documents", [[]])[0]
        raw_distances = results.get("distances", [[]])[0]
        distances: list[float] | None = (
            [float(d) for d in raw_distances] if raw_distances else None
        )

        log_retrieve_chunks(
            logger,
            settings.chat_retrieval_top_k,
            relevant_chunks,
            distances,
        )

        if not relevant_chunks:
            log_chat_end(logger, start)
            return "عذراً، لا يمكنني تحديد الحالة بدقة بناءً على الأعراض المذكورة. يُرجى حجز استشارة مع طبيب عام عبر تطبيق طبيبي لتقييم حالتك بشكل آمن."

        # Step 3 — Context: concatenate relevant chunks into one prompt block for the LLM.
        context = "Context:\n\n" + "\n\n".join(relevant_chunks)
        log_build_context(logger, relevant_chunks, context)

        # Step 4 — Generate: call the chat model with system prompt + context + question.
        llm = ChatGoogleGenerativeAI(
            model=_CHAT_MODEL,
            google_api_key=settings.google_api_key,
        )

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=f"{context}\n\nQuestion: {question}"),
        ]

        response = await llm.ainvoke(messages)
        answer = str(response.content)
        log_generate(
            logger,
            _CHAT_MODEL,
            _SYSTEM_PROMPT,
            question,
            context,
            answer,
        )
        log_chat_end(logger, start)
        return answer

    except Exception as exc:
        log_chat_error(logger, "chat pipeline", exc, start)
        raise


async def get_answer(message: str) -> str:
    """Alias for :func:`rag_answer` (same return value)."""
    return await rag_answer(message)