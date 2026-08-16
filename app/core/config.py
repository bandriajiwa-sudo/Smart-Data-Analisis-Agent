from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Data Analyst Agent"
    VERSION: str = "1.0.0"
    
    # API & Agent Authentication
    API_KEY: str
    OPENAI_API_KEY: str
    
    # Webhook Verification
    WEBHOOK_SECRET: str
    
    # Databases
    POS_DB_URI: str
    CHECKPOINTER_DB_URI: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
