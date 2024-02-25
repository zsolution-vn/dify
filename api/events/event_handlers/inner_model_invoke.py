from core.model_runtime.entities.model_entities import ModelType
from core.provider_manager import ProviderManager
from events.inner_event import model_was_invoked
from libs.deduct_quota import DeductQuotaManager

provider_manager = ProviderManager()

@model_was_invoked.connect
def handle(sender, **kwargs):
    """
    Invoke model event handler, handle the quota deduction

    :param sender: sender
    :param kwargs: kwargs
        :param tenant_id: tenant id
        :param model_config: model config
            :param provider: provider
            :param model_type: model type
            :param model: model
        :param message_tokens: message tokens
        :param answer_tokens: answer tokens
    :return: None
    """

    tenant_id = kwargs.get('tenant_id')
    if not tenant_id:
        return
    
    model_config = kwargs.get('model_config', {})
    if not model_config:
        return

    provider_model_bundle = provider_manager.get_provider_model_bundle(
        tenant_id,
        model_config.get('provider', ''),
        ModelType.value_of(model_config.get('model_type', ''))
    )

    if not provider_model_bundle:
        return

    DeductQuotaManager.deduct_quota(
        provider_model_bundle=provider_model_bundle,
        model=model_config.get('model', ''),
        message_tokens=kwargs.get('message_tokens', 0),
        answer_tokens=kwargs.get('answer_tokens', 0)
    )
    