from typing import Dict, Sequence, Optional

import requests

from edenai_apis.features import ProviderInterface, TextInterface, ImageInterface
from edenai_apis.features.image.completion import CompletionDataClass
from edenai_apis.features.image.embeddings import EmbeddingsDataClass, EmbeddingDataClass
from edenai_apis.features.image.question_answer import QuestionAnswerDataClass
from edenai_apis.features.text import SummarizeDataClass
from edenai_apis.loaders.data_loader import ProviderDataEnum
from edenai_apis.loaders.loaders import load_provider
from edenai_apis.utils.exception import ProviderException
from edenai_apis.utils.types import ResponseType

from aleph_alpha_client import Client, Prompt, SemanticEmbeddingRequest, QaRequest, Image, SemanticRepresentation, \
    Document, CompletionRequest, Text


class AlephAlphaApi(ProviderInterface, TextInterface, ImageInterface):
    provider_name = "alephalpha"

    def __init__(self, api_keys: Dict = {}):
        self.api_settings = load_provider(
            ProviderDataEnum.KEY, self.provider_name, api_keys=api_keys
        )
        self.api_key = self.api_settings["api_key"]
        self.url_basic = "https://api.aleph-alpha.com"
        self.url_summarise = "https://api.aleph-alpha.com/summarize"

    def text__summarize(
            self,
            text: str,
            output_sentences: int,
            language: str,
            model: str,
    ) -> ResponseType[SummarizeDataClass]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": model,
            "document": {
                "text": text
            }
        }
        response = requests.post(url=self.url_summarise, headers=headers, json=payload)
        if response.status_code != 200:
            raise ProviderException(response.text, code=response.status_code)
        original_response = response.json()
        standardized_response = SummarizeDataClass(
            result=original_response.get("summary", {})
        )
        return ResponseType[SummarizeDataClass](
            original_response=original_response,
            standardized_response=standardized_response,
        )

    def image__embeddings(
            self, file: str, model: str, representation: str, file_url: str = "",
    ) -> ResponseType[EmbeddingsDataClass]:
        if representation == "symmetric":
            representation_client = SemanticRepresentation.Symmetric
        elif representation == "document":
            representation_client = SemanticRepresentation.Document
        else:
            representation_client = SemanticRepresentation.Query
        client = Client(self.api_key)
        prompt = Prompt.from_image(Image.from_file(file))
        request = SemanticEmbeddingRequest(prompt=prompt, representation=representation_client)
        try:
            response = client.semantic_embed(request=request, model=model)
        except:
            raise ProviderException(response.message)
        if response.message:
            raise ProviderException(response.message)
        original_response = response._asdict()
        items: Sequence[EmbeddingDataClass] = [EmbeddingDataClass(embedding=response.embedding)]
        standardized_response = EmbeddingsDataClass(items=items)
        return ResponseType[EmbeddingsDataClass](
            original_response=original_response,
            standardized_response=standardized_response
        )

    def image__question_answer(
            self,
            question: str,
            file: str,
            temperature: float,
            max_tokens: int,
            file_url: str = "",
            model: Optional[str] = None
    ) -> ResponseType[QuestionAnswerDataClass]:
        client = Client(self.api_key)
        prompts = Prompt([Text.from_text(question), Image.from_file(file)])
        request = CompletionRequest(prompt=prompts, maximum_tokens=max_tokens, temperature=temperature)
        try:
            response = client.complete(request=request, model=model)
        except Exception as error:
            raise ProviderException(error)
        original_response = response._asdict()
        answers = []
        for answer in response.completions:
            answers.append(answer.completion)
        standardized_response = QuestionAnswerDataClass(answers=answers)
        return ResponseType[QuestionAnswerDataClass](
            original_response=original_response,
            standardized_response=standardized_response
        )
    def image__completion(
        self,
        file: str,
        temperature: float,
        max_tokens: int,
        file_url: str = "",
        model: Optional[str] = None
    ) -> ResponseType[CompletionDataClass]:
        client = Client(self.api_key)
        prompt = Prompt.from_image(Image.from_file(file))
        requests = CompletionRequest(prompt=prompt, maximum_tokens=max_tokens, temperature=temperature)
        try:
            response = client.complete(request=requests, model=model)
        except Exception as error:
            raise ProviderException(error)
        original_response = response._asdict()
        completions = []
        for completion in response.completions:
            completions.append(completion.completion)
        standardized_response = CompletionDataClass(completion=completions)
        return ResponseType[CompletionDataClass](
            original_response=original_response,
            standardized_response=standardized_response
        )

