"""
llm.py — Génération de réponses avec Qwen2.5 via Ollama (Gratuit, Local)
Utilise LangChain pour l'intégration et la gestion du prompt juridique arabe
"""
import logging
from typing import List, Dict, AsyncGenerator
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough

from app.config import settings

logger = logging.getLogger(__name__)

# Prompt système spécialisé pour les questions juridiques arabes
# Indique au LLM comment répondre à partir des contextes fournis
RAG_PROMPT_TEMPLATE = """أنت مساعد قانوني متخصص في القانون المغربي والعربي.
مهمتك هي الإجابة على الأسئلة القانونية بناءً على الوثائق المقدمة إليك.

قواعد مهمة:
- استخدم المعلومات الواردة في السياق أدناه للإجابة
- اذكر رقم المادة أو الفصل عند الاقتضاء
- إذا كانت المعلومات في السياق جزئية، أجب بما هو متاح وأشر إلى ذلك
- إذا لم تجد أي معلومة ذات صلة مطلقاً، قل: "لم أجد معلومات كافية في الوثائق المتاحة"
- كن دقيقاً ومفصلاً في إجابتك
- يمكنك الإجابة بالعربية أو الفرنسية حسب لغة السؤال

السياق من الوثائق القانونية:
{context}

السؤال:
{question}

الإجابة:"""


class LLMGenerator:
    """
    Génère des réponses aux questions juridiques en utilisant Qwen2.5 via Ollama.
    """

    def __init__(self):
        self.llm = Ollama(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=0.1,     # Faible pour des réponses juridiques précises
            num_ctx=4096,        # Augmenté pour contenir le contexte arabe dense
            num_predict=1024,    # Augmenté pour des réponses complètes
            num_thread=8,        # Utilise tous les cœurs CPU disponibles
            verbose=False,
        )
        self.prompt = PromptTemplate(
            template=RAG_PROMPT_TEMPLATE,
            input_variables=["context", "question"],
        )
        self.chain = self.prompt | self.llm

    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Formate les chunks récupérés en contexte lisible pour le LLM.
        """
        parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            doc_name = meta.get("document_name", "Document")
            page = meta.get("page_number", "?")
            text = chunk.get("text", "")
            parts.append(f"[{i}] {doc_name} — صفحة {page}:\n{text}")
        return "\n\n---\n\n".join(parts)

    def generate(self, question: str, chunks: List[Dict]) -> str:
        """
        Génère une réponse à partir de la question et des chunks pertinents.

        Args:
            question: Question de l'utilisateur (arabe ou français)
            chunks: Chunks re-classés par le reranker

        Returns:
            Réponse textuelle du LLM
        """
        if not chunks:
            return "لم أجد وثائق مفهرسة. يرجى تحميل وثائق قانونية أولاً."

        # 5 chunks pour un meilleur contexte (était 3)
        chunks = chunks[:5]
        context = self._format_context(chunks)
        logger.info(
            f"Génération réponse: {len(chunks)} chunks, "
            f"contexte={len(context)} chars"
        )

        try:
            response = self.chain.invoke({
                "context": context,
                "question": question,
            })
            return response.strip()
        except Exception as e:
            logger.error(f"Erreur génération LLM: {e}")
            if "connection" in str(e).lower():
                raise ConnectionError(
                    "Ollama non accessible. Vérifiez qu'Ollama est démarré : "
                    "`ollama serve` puis `ollama pull qwen2.5:7b`"
                )
            raise

    def is_ollama_available(self) -> bool:
        """Vérifie si Ollama est accessible."""
        try:
            import httpx
            resp = httpx.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=3)
            return resp.status_code == 200
        except Exception:
            return False


# Instance globale
llm_generator = LLMGenerator()
