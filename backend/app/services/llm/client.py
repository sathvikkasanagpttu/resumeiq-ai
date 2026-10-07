import hashlib
import json
import re
import time
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger
from app.models.audit import ModelRun

class LLMClient:
    """
    Hardened LLM Client supporting Google Gemini API via official google-genai SDK,
    paired with circuit breaker, exponential backoff retries, content-hash caching,
    JSON schema validation & repair, per-user token budgeting, and ModelRun auditing.
    """
    def __init__(self):
        self._client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("Initialized Google GenAI LLM client.")
            except Exception as e:
                logger.warning(f"Failed to initialize GenAI client: {e}. Fallback enabled.")

        # Circuit breaker state
        self.circuit_state: str = "CLOSED"  # "CLOSED", "OPEN", "HALF_OPEN"
        self.failure_count: int = 0
        self.failure_threshold: int = 5
        self.recovery_timeout: float = 30.0
        self.last_failure_time: float = 0.0

        # Caching & per-user budgeting
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._user_token_usage: Dict[str, int] = {}
        self.user_daily_token_budget: int = 100_000

        # Backoff parameters
        self.backoff_base: float = 0.005
        self.max_retries: int = 2

    def _record_model_run(
        self,
        task_type: str,
        status: str,
        latency_ms: float = 0.0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        error_message: Optional[str] = None
    ) -> None:
        try:
            import app.core.database as db_module
            with db_module.SessionLocal() as session:
                run = ModelRun(
                    task_type=task_type,
                    model_name=settings.GEMINI_MODEL,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    latency_ms=latency_ms,
                    status=status,
                    error_message=error_message
                )
                session.add(run)
                session.commit()
        except Exception as e:
            logger.debug(f"Could not persist ModelRun: {e}")

    def generate_structured(
        self,
        prompt: str,
        task_type: str = "generation",
        fallback_data: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes structured generation with resilience guarantees.
        """
        start_time = time.time()

        # 1. Per-user token budget check
        if user_id:
            used = self._user_token_usage.get(user_id, 0)
            if used >= self.user_daily_token_budget:
                logger.warning(f"User {user_id} exceeded token budget: {used}/{self.user_daily_token_budget}")
                return {"llm_available": False, "explanation": None, "error": "Daily token budget exceeded"}

        # 2. Circuit breaker check
        if self.circuit_state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.circuit_state = "HALF_OPEN"
                logger.info("Circuit breaker entered HALF_OPEN state.")
            else:
                return {"llm_available": False, "explanation": None, "error": "Circuit breaker OPEN"}

        # 3. Content-hash cache check
        cache_key = hashlib.sha256(f"{settings.GEMINI_MODEL}:{prompt}".encode()).hexdigest()
        if cache_key in self._cache:
            self._record_model_run(
                task_type=task_type,
                status="cached",
                latency_ms=0.0,
                prompt_tokens=0,
                completion_tokens=0
            )
            return self._cache[cache_key]

        # 4. Availability check
        if not self._client:
            if fallback_data is not None:
                return fallback_data
            return {"llm_available": False, "explanation": None}

        # 5. Execute with exponential backoff retries
        last_error = None
        response_text = ""
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                time.sleep(self.backoff_base * (2 ** (attempt - 1)))
            try:
                response = self._client.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=prompt,
                )
                response_text = getattr(response, "text", "") or ""
                last_error = None
                break
            except Exception as e:
                last_error = str(e)
                logger.warning(f"GenAI generation attempt {attempt + 1} failed: {e}")

        # Handle failure across all retries
        if last_error is not None:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.failure_threshold:
                self.circuit_state = "OPEN"
                logger.error(f"Circuit breaker tripped to OPEN after {self.failure_count} consecutive failures.")

            latency = round((time.time() - start_time) * 1000, 2)
            self._record_model_run(
                task_type=task_type,
                status="error",
                latency_ms=latency,
                error_message=last_error
            )
            if fallback_data is not None:
                return fallback_data
            return {"llm_available": False, "explanation": None, "error": last_error}

        # Successful invocation: reset circuit breaker
        self.failure_count = 0
        self.circuit_state = "CLOSED"
        latency = round((time.time() - start_time) * 1000, 2)

        # 6. Parse and repair JSON schema
        clean_json_str = response_text.strip()
        if "```json" in clean_json_str:
            clean_json_str = clean_json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json_str:
            clean_json_str = clean_json_str.split("```")[1].split("```")[0].strip()

        # Isolate outermost JSON brackets if surrounded by extraneous commentary
        first_brace = clean_json_str.find("{")
        last_brace = clean_json_str.rfind("}")
        if first_brace != -1 and last_brace != -1:
            clean_json_str = clean_json_str[first_brace:last_brace + 1]

        parsed_data = None
        try:
            parsed_data = json.loads(clean_json_str)
        except Exception:
            # Repair pass: remove trailing commas before closing braces/brackets
            repaired = re.sub(r',\s*([\]}])', r'\1', clean_json_str)
            try:
                parsed_data = json.loads(repaired)
            except Exception:
                logger.warning("Could not parse or repair LLM response as JSON.")

        if parsed_data is None:
            self._record_model_run(
                task_type=task_type,
                status="error",
                latency_ms=latency,
                error_message="Invalid JSON response"
            )
            if fallback_data is not None:
                return fallback_data
            return {"llm_available": False, "explanation": None, "error": "Invalid JSON response"}

        # Token counting and budget tracking
        prompt_tokens = max(1, len(prompt) // 4)
        completion_tokens = max(1, len(response_text) // 4)
        if user_id:
            self._user_token_usage[user_id] = self._user_token_usage.get(user_id, 0) + prompt_tokens + completion_tokens

        # Cache valid response
        self._cache[cache_key] = parsed_data

        self._record_model_run(
            task_type=task_type,
            status="success",
            latency_ms=latency,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        return parsed_data

llm_client = LLMClient()
