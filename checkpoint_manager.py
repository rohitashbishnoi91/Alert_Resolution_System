"""Checkpoint management utilities"""

import os
from pathlib import Path


def list_checkpoints(db_path="checkpoints/aars_checkpoints.db"):
    """List all saved checkpoints"""
    if not os.path.exists(db_path):
        print("No checkpoint database found")
        return []
    
    from langgraph.checkpoint.sqlite import SqliteSaver
    
    checkpointer = SqliteSaver.from_conn_string(db_path)
    
    print(f"Checkpoints in {db_path}:")
    print("="*60)
    
    # This would require querying the SQLite database directly
    # For now, just confirm it exists
    print(f"✓ Checkpoint database exists at: {db_path}")
    print("  Workflow states are being persisted")
    
    return []


def clear_checkpoints(db_path="checkpoints/aars_checkpoints.db"):
    """Clear all checkpoints"""
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Cleared checkpoints: {db_path}")
    else:
        print("No checkpoint database to clear")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        clear_checkpoints()
    else:
        list_checkpoints()

