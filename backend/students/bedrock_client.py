import os
import boto3
import json
from typing import Dict, List, Any, Tuple
from django.conf import settings

class BedrockKnowledgeBaseClient:
    def __init__(self):
        # Environment-first configuration. Do not hardcode real KB IDs or AWS details.
        self.kb_id = (
            os.getenv('BEDROCK_KB_ID')
            or os.getenv('AWS_KB_ID')
            or os.getenv('BEDROCK_KNOWLEDGE_BASE_ID')
            or os.getenv('AWS_BEDROCK_KB_ID')
            or getattr(settings, 'AWS_KB_ID', '')
        ).strip()
        self.model_arn = (
            os.getenv('AWS_BEDROCK_MODEL_ARN')
            or os.getenv('AWS_BEDROCK_MODEL_ID')
            or os.getenv('BEDROCK_SMART_MODEL_ID')
            or getattr(settings, 'AWS_BEDROCK_MODEL_ARN', '')
        ).strip()
        self.region = (os.getenv('BEDROCK_REGION') or os.getenv('AWS_REGION') or getattr(settings, 'AWS_REGION', 'us-east-1') or 'us-east-1').strip()
        self.client = boto3.client('bedrock-agent-runtime', region_name=self.region)

    def ask_question_with_citations(self, prompt: str, session_id: str = None) -> Tuple[str, List[Dict]]:
        """
        Sends a prompt to the Bedrock Knowledge Base and returns the answer and a list of citations.
        """
        if not self.kb_id or not self.model_arn:
            return "The knowledge base is not configured yet. Set AWS_KB_ID/BEDROCK_KB_ID and AWS_BEDROCK_MODEL_ID in the environment.", []

        config = {
            "type": "KNOWLEDGE_BASE",
            "knowledgeBaseConfiguration": {
                "knowledgeBaseId": self.kb_id,
                "modelArn": self.model_arn,
            }
        }
        if session_id:
            config["knowledgeBaseConfiguration"]["sessionId"] = session_id

        try:
            response_stream = self.client.retrieve_and_generate_stream(
                input={"text": prompt},
                retrieveAndGenerateConfiguration=config
            )
        except Exception as e:
            return f"An error occurred while querying the knowledge base: {e}", []

        full_answer = ""
        citations = []
        for event in response_stream['stream']:
            if 'output' in event:
                chunk = event['output']['text']
                full_answer += chunk
            elif 'citation' in event:
                citation_data = event['citation']
                retrieved_refs = citation_data.get('retrievedReferences', [])
                for ref in retrieved_refs:
                    citation_info = {
                        'text': ref.get('content', {}).get('text', ''),
                        's3_uri': '',
                        'document_name': 'Knowledge source',
                    }
                    citations.append(citation_info)
        return full_answer, citations