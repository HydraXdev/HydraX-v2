"""
Mock database connection for testing
"""

def get_db_session():
    """Mock database session"""
    return None

class DatabaseSession:
    """Mock database session"""
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def commit(self):
        pass
    
    def rollback(self):
        pass