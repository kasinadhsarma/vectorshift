# backend/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    cassandra_host: str = Field(..., validation_alias="CASSANDRA_HOST")
    cassandra_port: int = Field(..., validation_alias="CASSANDRA_PORT")
    cassandra_keyspace: str = Field(..., validation_alias="CASSANDRA_KEYSPACE")
    jwt_secret_key: str = Field(..., validation_alias="JWT_SECRET_KEY")
    google_client_id: str = Field(..., validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(..., validation_alias="GOOGLE_CLIENT_SECRET")
    hubspot_client_id: str = Field(..., validation_alias="HUBSPOT_CLIENT_ID")
    hubspot_client_secret: str = Field(..., validation_alias="HUBSPOT_CLIENT_SECRET")
    google_redirect_uri: Optional[str] = Field(None, validation_alias="GOOGLE_REDIRECT_URI")
    redis_host: Optional[str] = Field(None, validation_alias="REDIS_HOST")
    redis_port: Optional[str] = Field(None, validation_alias="REDIS_PORT")
    redis_db: Optional[str] = Field(None, validation_alias="REDIS_DB")
    notion_client_id: Optional[str] = Field(None, validation_alias="NOTION_CLIENT_ID")
    notion_client_secret: Optional[str] = Field(None, validation_alias="NOTION_CLIENT_SECRET")
    notion_redirect_uri: Optional[str] = Field(None, validation_alias="NOTION_REDIRECT_URI")
    airtable_client_id: Optional[str] = Field(None, validation_alias="AIRTABLE_CLIENT_ID")
    airtable_client_secret: Optional[str] = Field(None, validation_alias="AIRTABLE_CLIENT_SECRET")
    airtable_redirect_uri: Optional[str] = Field(None, validation_alias="AIRTABLE_REDIRECT_URI")
    hubspot_redirect_uri: Optional[str] = Field(None, validation_alias="HUBSPOT_REDIRECT_URI")
    slack_client_id: Optional[str] = Field(None, validation_alias="SLACK_CLIENT_ID")
    slack_client_secret: Optional[str] = Field(None, validation_alias="SLACK_CLIENT_SECRET")
    slack_redirect_uri: Optional[str] = Field(None, validation_alias="SLACK_REDIRECT_URI")
    backend_url: Optional[str] = Field(None, validation_alias="BACKEND_URL")
    frontend_url: Optional[str] = Field(None, validation_alias="FRONTEND_URL")
    session_secret: Optional[str] = Field(None, validation_alias="SESSION_SECRET")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
