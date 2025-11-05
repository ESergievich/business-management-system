from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class RunConfig(BaseModel):
    """
    Configuration settings for the application's runtime.

    Attributes:
        host (str): Host address to bind the application to.
        port (int): Port to bind the application to.
        debug (bool): Enable debug mode.
    """

    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True


class ApiV1Prefix(BaseModel):
    """
    Configuration settings for the API v1 prefix.

    Attributes:
        prefix (str): The API v1 prefix.
    """

    prefix: str = "/v1"


class ApiPrefix(BaseModel):
    """
    Configuration settings for the API prefix.

    Attributes:
        prefix (str): The API prefix.
        v1 (ApiV1Prefix): Configuration settings for the API v1 prefix.
    """

    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()


class Settings(BaseSettings):
    """
    Application settings container.

    Attributes:
        run (RunConfig): Configuration settings for the application's runtime.
        api (ApiPrefix): Configuration settings for the API prefix.

        model_config (SettingsConfigDict): Pydantic model configuration.
    """

    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()

    model_config = SettingsConfigDict(
        env_file=("../.env.template", "../.env"),
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
    )


settings = Settings()
