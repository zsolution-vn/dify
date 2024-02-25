from core.entities.provider_configuration import ProviderModelBundle
from core.entities.provider_entities import QuotaUnit
from models.provider import Provider, ProviderType
from extensions.ext_database import db

class DeductQuotaManager:
    @staticmethod
    def deduct_quota(
        provider_model_bundle: ProviderModelBundle,
        model: str,
        message_tokens: int,
        answer_tokens: int
    ):
        provider_configuration = provider_model_bundle.configuration
        if provider_configuration.using_provider_type != ProviderType.SYSTEM:
            return
        
        system_configuration = provider_configuration.system_configuration

        quota_unit = None
        for quota_configuration in system_configuration.quota_configurations:
            if quota_configuration.quota_type == system_configuration.current_quota_type:
                quota_unit = quota_configuration.quota_unit

                if quota_configuration.quota_limit == -1:
                    return

                break

        used_quota = None
        if quota_unit:
            if quota_unit == QuotaUnit.TOKENS:
                used_quota = message_tokens + answer_tokens
            elif quota_unit == QuotaUnit.CREDITS:
                used_quota = 1

                if 'gpt-4' in model:
                    used_quota = 20
            else:
                used_quota = 1

        if used_quota is not None:
            db.session.query(Provider).filter(
                Provider.tenant_id == provider_configuration.tenant_id,
                Provider.provider_name == provider_configuration.provider,
                Provider.provider_type == ProviderType.SYSTEM.value,
                Provider.quota_type == system_configuration.current_quota_type.value,
                Provider.quota_limit > Provider.quota_used
            ).update({'quota_used': Provider.quota_used + used_quota})
            db.session.commit()
