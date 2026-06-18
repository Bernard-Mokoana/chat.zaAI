import os
from dotenv import load_dotenv
from urllib.parse import urlparse
from huggingface_hub import InferenceClient
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class GPT:
    DEFAULT_MODEL_ID = "katanemo/Arch-Router-1.5B"
    DEFAULT_MAX_TOKENS = 32768

    def __init__(self):
        token = os.environ.get('HUGGINGFACE_INFERENCE_TOKEN')
        if not token:
            raise RuntimeError("Missing HUGGINGFACE_INFERENCE_TOKEN in environment.")
        self.client = InferenceClient(
            provider="hf-inference",
            api_key=token
        )
        self.model_id = self._resolve_model_id()

        try:
            self.max_new_tokens = int(os.environ.get("MAX_NEW_TOKENS", self.DEFAULT_MAX_TOKENS))
        except ValueError as exc:
            logger.warning(f"Invalid MAX_NEW_TOKENS value, using default {self.DEFAULT_MAX_TOKENS}: {exc}")
            self.max_new_tokens = self.DEFAULT_MAX_TOKENS

    def _resolve_model_id(self) -> str:
        model_id = os.environ.get("MODEL_ID")
        if model_id:
            return model_id
        url = os.environ.get("MODEL_URL", "")
        if url:
            parsed = urlparse(url)
            path = parsed.path.strip("/")
            if "/models/" in path:
                return path.split("/models/")[-1]
            parts = path.split("/")
            if len(parts) >= 2:
                return "/".join(parts[-2:])
        logger.info(f"Using default model: {self.DEFAULT_MODEL_ID}")
        return self.DEFAULT_MODEL_ID

    def query(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.max_new_tokens,
                stop=["Human:", "User:"]
            )
            if not response.choices:
                raise RuntimeError("Empty response from model")
            
            return (response.choices[0].message.content or "").strip()
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise RuntimeError(f"Model query failed: {e}") from e

if __name__ == "__main__":
    gpt = GPT()
    response = gpt.query("Hello")
    print(response)