import os
import asyncio
import logging
from typing import Dict, Any

from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase

from generation.groq import get_groq_client

# In-memory store for evaluation results
evaluation_results: Dict[str, Any] = {}

class GroqLlama(DeepEvalBaseLLM):
    def __init__(self, model_name: str = "llama-3.1-8b-instant"):
        self.model_name = model_name
        self.client = get_groq_client()
        
    def load_model(self):
        return self.client
        
    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024,
        )
        return response.choices[0].message.content
        
    async def a_generate(self, prompt: str) -> str:
        # groq client is synchronous, but we can run it in a thread or just return it directly
        return self.generate(prompt)

    def get_model_name(self) -> str:
        return self.model_name


def run_evaluation(message_id: str, eval_payload: dict):
    logging.info(f"Starting background evaluation for message {message_id}")
    evaluation_results[message_id] = {"status": "pending", "eval_payload": eval_payload}
    
    try:
        custom_llm = GroqLlama(model_name="llama-3.1-8b-instant")
        
        # We define the test case for Answer Relevancy (only needs input and actual_output)
        test_case = LLMTestCase(
            input=eval_payload.get("question", ""),
            actual_output=eval_payload.get("answer", "")
        )
        
        metrics = {
            "answer_relevancy": AnswerRelevancyMetric(threshold=0.5, model=custom_llm)
        }
        
        metrics_data = {}
        total_score = 0.0
        success_count = 0
        
        import time
        # Measure metrics sequentially for safety
        for key, metric in metrics.items():
            try:
                logging.info(f"Measuring {key} for {message_id}")
                metric.measure(test_case)
                score = getattr(metric, 'score', 0.0)
                passed = getattr(metric, 'is_successful', False)
                reason = getattr(metric, 'reason', '')
                
                metrics_data[key] = {
                    "score": round(score, 2),
                    "passed": passed,
                    "reason": reason
                }
                total_score += score
                success_count += 1
                
                # Sleep to respect Groq rate limits (free tier often limits requests per minute)
                time.sleep(5)
            except Exception as metric_err:
                logging.warning(f"Metric {key} failed: {metric_err}")
                metrics_data[key] = {
                    "score": 0.0,
                    "passed": False,
                    "reason": f"Evaluation failed: {str(metric_err)}"
                }
                time.sleep(2)
                
        overall_score = total_score / max(success_count, 1)
        
        evaluation_results[message_id] = {
            "status": "completed",
            "overall_score": round(overall_score, 2),
            "metrics": metrics_data,
            "eval_payload": eval_payload
        }
        logging.info(f"Completed background evaluation for message {message_id}")
        
    except Exception as e:
        logging.error(f"Background evaluation error for {message_id}: {e}")
        evaluation_results[message_id] = {
            "status": "error",
            "error": str(e),
            "eval_payload": eval_payload
        }
