class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///api_keys.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SCHEDULER_API_ENABLED = True
    
    # Job monitoring configuration
    JOB_MONITOR_INTERVAL = 10  # seconds
    
    # Pricing configuration
    CPU_RATE = 0.10  # $0.10 per CPU hour
    MEMORY_RATE = 0.05  # $0.05 per GB hour
    
    # Default resource limits
    DEFAULT_CPU_LIMIT = '100m'
    DEFAULT_MEMORY_LIMIT = '128Mi'