from config.settings import Settings


def test_settings_are_loaded_from_environment(monkeypatch):
    monkeypatch.setenv("RABBITMQ_HOST", "broker.internal")
    monkeypatch.setenv("RABBITMQ_PORT", "5673")
    monkeypatch.setenv("WEBHOOK_MAX_RETRIES", "7")
    monkeypatch.setenv("WEBHOOK_TIMEOUT_SECONDS", "12.5")

    settings = Settings(_env_file=None)

    assert settings.rabbitmq_host == "broker.internal"
    assert settings.rabbitmq_port == 5673
    assert settings.webhook_max_retries == 7
    assert settings.webhook_timeout_seconds == 12.5
