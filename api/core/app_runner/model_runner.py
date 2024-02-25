from core.provider_manager import ProviderManager, ProviderModelBundle
from core.model_runtime.entities.llm_entities import LLMResult, LLMResultChunk, LLMUsage
from core.model_runtime.entities.message_entities import PromptMessage, PromptMessageTool
from core.model_runtime.model_providers.__base.large_language_model import LargeLanguageModel
from core.model_runtime.entities.model_entities import ModelType

from core.model_runtime.utils.encoders import jsonable_encoder

from events.inner_event import model_was_invoked
from typing import Generator, Union, cast, Optional

class ModelRunner:
    """
    Model runner
    """
    @staticmethod
    def run(
        provider_model_bundle: ProviderModelBundle,
        model: str, 
        prompt_messages: list[PromptMessage], 
        model_parameters: Optional[dict] = None,
        tools: Optional[list[PromptMessageTool]] = None, 
        stop: Optional[list[str]] = None,
        stream: bool = True, 
        user: Optional[str] = None,
    ) -> Union[Generator, dict]:
        """
        Run model
        """
        llm_model = cast(LargeLanguageModel, provider_model_bundle.model_type_instance)

        credentials = provider_model_bundle.configuration.get_current_credentials(
            model_type=ModelType.LLM,
            model=model,
        )

        if not credentials:
            raise ValueError('No credentials found for model')

        response = llm_model.invoke(
            model=model,
            credentials=credentials,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stop=stop,
            stream=stream,
            user=user,
        )

        if stream:
            return ModelRunner.handle_streaming_response(
                tenant_id=provider_model_bundle.configuration.tenant_id,
                provider=provider_model_bundle.configuration.provider,
                model=model,
                model_type=ModelType.LLM.value,
                response=response,
            )
        
        return ModelRunner.handle_blocking_response(
            tenant_id=provider_model_bundle.configuration.tenant_id,
            provider=provider_model_bundle.configuration.provider,
            model=model,
            model_type=ModelType.LLM.value,
            response=response,
        )

    def handle_streaming_response(
        tenant_id: str,
        provider: str,
        model: str,
        model_type: str, 
        response: Generator[LLMResultChunk, None, None],
    ) -> Generator[dict]:
        """
        Handle streaming response
        """
        usage = LLMUsage.empty_usage()
        for chunk in response:
            if chunk.delta.usage:
                usage.completion_price += chunk.delta.usage.completion_price
                usage.prompt_price += chunk.delta.usage.prompt_price

                usage.prompt_price_unit = chunk.delta.usage.prompt_price_unit
                usage.prompt_unit_price = chunk.delta.usage.prompt_unit_price
                usage.completion_price_unit = chunk.delta.usage.completion_price_unit
                usage.completion_unit_price = chunk.delta.usage.completion_unit_price

                usage.prompt_tokens += chunk.delta.usage.prompt_tokens
                usage.completion_tokens += chunk.delta.usage.completion_tokens

                usage.currency = chunk.delta.usage.currency

            yield jsonable_encoder(chunk)

        model_was_invoked(
            None, 
            tenant_id=tenant_id,
            model_config={
                'provider': provider,
                'model_type': model_type,
                'model': model,
            },
            message_tokens=usage.prompt_tokens,
            answer_tokens=usage.completion_tokens,
        )
        
    def handle_blocking_response(
        tenant_id: str,
        provider: str,
        model: str,
        model_type: str, 
        response: LLMResult, 
    ) -> dict:
        """
        Handle blocking response
        """
        usage = response.usage or LLMUsage.empty_usage()
        
        model_was_invoked(
            None, 
            tenant_id=tenant_id,
            model_config={
                'provider': provider,
                'model_type': model_type,
                'model': model,
            },
            message_tokens=usage.prompt_tokens,
            answer_tokens=usage.completion_tokens,
        )

        return jsonable_encoder(response)