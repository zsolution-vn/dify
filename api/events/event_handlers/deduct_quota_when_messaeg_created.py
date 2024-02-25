from core.entities.application_entities import ApplicationGenerateEntity
from events.message_event import message_was_created
from libs.deduct_quota import DeductQuotaManager
from models.model import Message

@message_was_created.connect
def handle(sender: Message, **kwargs):
    message = sender
    application_generate_entity: ApplicationGenerateEntity = kwargs.get('application_generate_entity')

    model_config = application_generate_entity.app_orchestration_config_entity.model_config
    provider_model_bundle = model_config.provider_model_bundle
    
    DeductQuotaManager.deduct_quota(
        provider_model_bundle=provider_model_bundle,
        model=model_config.model,
        message_tokens=message.message_tokens,
        answer_tokens=message.answer_tokens
    )
    