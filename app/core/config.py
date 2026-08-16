from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart Data Analyst Agent"
    VERSION: str = "1.0.0"
    
    # API & Agent Authentication
    API_KEY: str
    GROQ_API_KEY: str
    
    # Webhook Verification & Tools
    WEBHOOK_SECRET: str
    TELEGRAM_BOT_TOKEN: str = "dummy"
    
    # Databases
    POS_DB_URI: str
    CHECKPOINTER_DB_URI: str
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
