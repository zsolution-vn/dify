from collections.abc import Generator
from typing import Union

from core.app_runner.model_runner import ModelRunner
from core.entities.model_entities import ModelStatus
from core.errors.error import ModelCurrentlyNotSupportError, ProviderTokenNotInitError, QuotaExceededError
from core.model_runtime.entities.message_entities import (
    AssistantPromptMessage,
    PromptMessage,
    PromptMessageRole,
    PromptMessageTool,
    SystemPromptMessage,
    ToolPromptMessage,
    UserPromptMessage,
)
from core.model_runtime.entities.model_entities import ModelType
from core.provider_manager import ProviderManager


class CompletionService:
    @staticmethod
    def invoke_model(
        tenant_id: str, provider: str, model: str,
        completion_params: dict,
        prompt_messages: list[dict],
        tools: list[dict],
        stop: list[str],
        stream: bool,
        user: str
    ) -> Union[Generator, dict]:
        """
            invoke model

            :param tenant_id: the tenant id
            :param provider: the provider
            :param model: the model
            :param mode: the mode
            :param completion_params: the completion params
            :param prompt_messages: the prompt messages
            :param stream: the stream
            :return: the model result
        """

        converted_prompt_messages: list[PromptMessage] = []
        for message in prompt_messages:
            role = message.get('role')
            if not role:
                raise ValueError('role is required')
            if role == PromptMessageRole.USER.value:
                converted_prompt_messages.append(UserPromptMessage(content=message['content']))
            elif role == PromptMessageRole.ASSISTANT.value:
                converted_prompt_messages.append(AssistantPromptMessage(
                    content=message['content'],
                    tool_calls=message.get('tool_calls', [])
                ))
            elif role == PromptMessageRole.SYSTEM.value:
                converted_prompt_messages.append(SystemPromptMessage(content=message['content']))
            elif role == PromptMessageRole.TOOL.value:
                converted_prompt_messages.append(ToolPromptMessage(
                    content=message['content'],
                    tool_call_id=message['tool_call_id']
                ))
            else:
                raise ValueError(f'Unknown role: {role}')
        
        # check if the model is available
        bundle = ProviderManager().get_provider_model_bundle(
            tenant_id=tenant_id, 
            provider=provider, 
            model_type=ModelType.LLM,
        )

        provider_model = bundle.configuration.get_provider_model(
            model_type=ModelType.LLM, 
            model=model,
        )

        if not provider_model:
            raise ModelCurrentlyNotSupportError(f"Could not find model {model} in provider {provider}.")

        if provider_model.status == ModelStatus.NO_CONFIGURE:
            raise ProviderTokenNotInitError(f"Model {model} credentials is not initialized.")
        elif provider_model.status == ModelStatus.NO_PERMISSION:
            raise ModelCurrentlyNotSupportError(f"Dify Hosted OpenAI {model} currently not support.")
        if provider_model.status == ModelStatus.QUOTA_EXCEEDED:
            raise QuotaExceededError(f"Model provider {provider} quota exceeded.")
        
        converted_tools = []
        for tool in tools or []:
            converted_tools.append(PromptMessageTool(
                name=tool['name'],
                description=tool['description'],
                parameters=tool['parameters']
            ))

        # invoke model
        return ModelRunner.run(
            provider_model_bundle=bundle,
            model=model,
            prompt_messages=converted_prompt_messages,
            model_parameters=completion_params,
            tools=converted_tools,
            stop=stop,
            stream=stream,
            user=user
        )