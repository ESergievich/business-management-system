from pydantic import BaseModel, Field, PostgresDsn, field_validator
from pydantic_core.core_schema import ValidationInfo
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
        auth (str): The authentication endpoint.
    """

    prefix: str = "/v1"
    auth: str = "/auth"


class ApiPrefix(BaseModel):
    """
    Configuration settings for the API prefix.

    Attributes:
        prefix (str): The API prefix.
        v1 (ApiV1Prefix): Configuration settings for the API v1 prefix.

    Properties:
        bearer_token_url (str):
            Returns the full relative URL path for the authentication endpoint
            used to obtain a Bearer token (e.g., "api/v1/auth/login").
            The leading slash is automatically removed for compatibility
            with FastAPI's OAuth2 configuration.
    """

    prefix: str = "/api"
    v1: ApiV1Prefix = ApiV1Prefix()

    @property
    def bearer_token_url(self) -> str:
        """
        Build and return the full relative URL for the Bearer token endpoint.

        Returns:
            str: The authentication URL path without a leading slash.
                 Example: "api/v1/auth/login".
        """
        parts = (self.prefix, self.v1.prefix, self.v1.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")


class DatabaseConfig(BaseModel):
    """
    Configuration settings for connecting to a PostgreSQL database.

    Attributes:
        host (str | None): Database host address.
        port (int | None): Database port.
        user (str | None): Username for authentication.
        password (str | None): Password for authentication.
        name (str | None): Name of the database.
        url (PostgresDsn | None): Full database URL. If provided, individual connection fields are optional.
        echo (bool): Enable SQL query logging.
        echo_pool (bool): Enable SQLAlchemy connection pool logging.
        pool_size (int): Maximum number of database connections in the pool.
        max_overflow (int): Maximum number of connections to allow in overflow beyond the pool_size.
        naming_convention (dict[str, str]): Default naming conventions for database constraints.
    """

    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    name: str | None = None
    url: PostgresDsn | None = None
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10

    naming_convention: dict[str, str] = Field(
        default_factory=lambda: {
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
    )

    @field_validator("url", mode="before")
    @classmethod
    def validate_url(
        cls,
        value: PostgresDsn | None,
        values: ValidationInfo,
    ) -> PostgresDsn | None:
        """
        Validate or build the database URL.

        If 'url' is provided, it will be used directly.
        If 'url' is not provided, all individual connection fields
        (host, port, user, password, name) must be specified. A PostgresDsn URL
        will then be automatically constructed.

        Args:
            value (PostgresDsn | None): The database URL.
            values (ValidationInfo): The validation info containing other field values.

        Returns:
            PostgresDsn | None: Validated or constructed Postgres DSN.

        Raises:
            ValueError: If 'url' is not provided and any required field is missing.
        """
        if value:
            return value

        required_fields = ["host", "port", "user", "password", "name"]
        if not all(values.data.get(required_field) for required_field in required_fields):
            msg = "If 'url' is not set, you need to specify 'host', 'port', 'user', 'password' and 'name'."
            raise ValueError(
                msg,
            )

        return PostgresDsn.build(
            scheme="postgresql",
            username=values.data["user"],
            password=values.data["password"],
            host=values.data["host"],
            port=values.data["port"],
            path=f"/{values.data['name']}",
        )


class AccessToken(BaseModel):
    """
    Configuration settings for access tokens.

    Attributes:
        lifetime_seconds (int): Lifetime of the access token in seconds.
            Default is 3600 seconds (1 hour).
    """

    lifetime_seconds: int = 3600


class Settings(BaseSettings):
    """
    Application settings container.

    Attributes:
        run (RunConfig): Configuration settings for the application's runtime.
        api (ApiPrefix): Configuration settings for the API prefix.
        db (DatabaseConfig): Database configuration settings.

        model_config (SettingsConfigDict): Pydantic model configuration.
    """

    run: RunConfig = RunConfig()
    api: ApiPrefix = ApiPrefix()
    db: DatabaseConfig = DatabaseConfig()
    access_token: AccessToken = AccessToken()

    model_config = SettingsConfigDict(
        env_file=("../.env.template", "../.env"),
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
    )


settings = Settings()
