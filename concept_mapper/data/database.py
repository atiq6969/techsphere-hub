"""
Database Module
SQLite database for storing concepts, relationships, and processing history
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import json


class Database:
    """SQLite database manager for Concept Mapper."""
    
    def __init__(self, db_path: str = "concept_mapper.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._create_tables()
    
    def connect(self):
        """Create database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                filepath TEXT,
                file_size INTEGER,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                page_count INTEGER,
                metadata TEXT
            )
        """)
        
        # Processing jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                status TEXT DEFAULT 'pending',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Concepts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                name TEXT NOT NULL,
                score REAL,
                pagerank REAL,
                importance REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES processing_jobs(id)
            )
        """)
        
        # Relationships table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                source_concept TEXT NOT NULL,
                target_concept TEXT NOT NULL,
                relationship_type TEXT,
                weight REAL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES processing_jobs(id)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_concepts_job_id 
            ON concepts(job_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relationships_job_id 
            ON relationships(job_id)
        """)
        
        conn.commit()
        self.close()
    
    def add_document(self, filename: str, filepath: str = None, 
                     file_size: int = None, page_count: int = None,
                     metadata: Dict = None) -> int:
        """
        Add a document record.
        
        Returns:
            Document ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT INTO documents (filename, filepath, file_size, page_count, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (filename, filepath, file_size, page_count, metadata_json))
        
        doc_id = cursor.lastrowid
        conn.commit()
        self.close()
        
        return doc_id
    
    def create_processing_job(self, document_id: int) -> int:
        """
        Create a new processing job.
        
        Returns:
            Job ID
        """
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO processing_jobs (document_id, status, started_at)
            VALUES (?, ?, ?)
        """, (document_id, 'processing', datetime.now()))
        
        job_id = cursor.lastrowid
        conn.commit()
        self.close()
        
        return job_id
    
    def update_job_status(self, job_id: int, status: str, 
                          error_message: str = None):
        """Update processing job status."""
        conn = self.connect()
        cursor = conn.cursor()
        
        completed_at = datetime.now() if status in ['completed', 'failed'] else None
        
        cursor.execute("""
            UPDATE processing_jobs 
            SET status = ?, completed_at = ?, error_message = ?
            WHERE id = ?
        """, (status, completed_at, error_message, job_id))
        
        conn.commit()
        self.close()
    
    def save_concepts(self, job_id: int, concepts: List[Dict]):
        """Save extracted concepts to database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        for concept in concepts:
            cursor.execute("""
                INSERT INTO concepts (job_id, name, score, pagerank, importance)
                VALUES (?, ?, ?, ?, ?)
            """, (
                job_id,
                concept.get('name', ''),
                concept.get('score', 0),
                concept.get('pagerank', 0),
                concept.get('importance', 0)
            ))
        
        conn.commit()
        self.close()
    
    def save_relationships(self, job_id: int, relationships: List[Dict]):
        """Save relationships to database."""
        conn = self.connect()
        cursor = conn.cursor()
        
        for rel in relationships:
            metadata_json = json.dumps({
                k: v for k, v in rel.items() 
                if k not in ['source', 'target', 'type', 'weight']
            }) if rel else None
            
            cursor.execute("""
                INSERT INTO relationships 
                (job_id, source_concept, target_concept, relationship_type, weight, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                rel.get('source', ''),
                rel.get('target', ''),
                rel.get('type', 'unknown'),
                rel.get('weight', 0),
                metadata_json
            ))
        
        conn.commit()
        self.close()
    
    def get_job_results(self, job_id: int) -> Dict:
        """Get all results for a processing job."""
        conn = self.connect()
        cursor = conn.cursor()
        
        # Get concepts
        cursor.execute("""
            SELECT name, score, pagerank, importance 
            FROM concepts 
            WHERE job_id = ?
            ORDER BY importance DESC
        """, (job_id,))
        concepts = [dict(row) for row in cursor.fetchall()]
        
        # Get relationships
        cursor.execute("""
            SELECT source_concept, target_concept, relationship_type, weight, metadata
            FROM relationships
            WHERE job_id = ?
        """, (job_id,))
        relationships = [dict(row) for row in cursor.fetchall()]
        
        self.close()
        
        return {
            'concepts': concepts,
            'relationships': relationships
        }
    
    def get_recent_jobs(self, limit: int = 10) -> List[Dict]:
        """Get recent processing jobs."""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT j.id, j.status, j.started_at, j.completed_at,
                   d.filename, d.page_count
            FROM processing_jobs j
            LEFT JOIN documents d ON j.document_id = d.id
            ORDER BY j.started_at DESC
            LIMIT ?
        """, (limit,))
        
        jobs = [dict(row) for row in cursor.fetchall()]
        self.close()
        
        return jobs
    
    def get_statistics(self, job_id: int = None) -> Dict:
        """Get database statistics."""
        conn = self.connect()
        cursor = conn.cursor()
        
        if job_id:
            # Statistics for specific job
            cursor.execute("SELECT COUNT(*) FROM concepts WHERE job_id = ?", (job_id,))
            num_concepts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships WHERE job_id = ?", (job_id,))
            num_relationships = cursor.fetchone()[0]
        else:
            # Overall statistics
            cursor.execute("SELECT COUNT(*) FROM documents")
            num_documents = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM processing_jobs")
            num_jobs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM concepts")
            num_concepts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM relationships")
            num_relationships = cursor.fetchone()[0]
            
            self.close()
            
            return {
                'total_documents': num_documents,
                'total_jobs': num_jobs,
                'total_concepts': num_concepts,
                'total_relationships': num_relationships
            }
        
        self.close()
        
        return {
            'num_concepts': num_concepts,
            'num_relationships': num_relationships
        }


# Singleton instance
_db_instance = None


def get_database(db_path: str = "concept_mapper.db") -> Database:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance


if __name__ == "__main__":
    # Test the database
    db = Database("test_concept_mapper.db")
    
    # Add a test document
    doc_id = db.add_document(
        filename="test_physics.pdf",
        file_size=1024 * 1024 * 5,
        page_count=100
    )
    print(f"Created document: {doc_id}")
    
    # Create a processing job
    job_id = db.create_processing_job(doc_id)
    print(f"Created job: {job_id}")
    
    # Save test concepts
    test_concepts = [
        {'name': 'Force', 'score': 0.9, 'pagerank': 0.15, 'importance': 0.15},
        {'name': 'Mass', 'score': 0.85, 'pagerank': 0.12, 'importance': 0.12},
        {'name': 'Acceleration', 'score': 0.8, 'pagerank': 0.10, 'importance': 0.10}
    ]
    db.save_concepts(job_id, test_concepts)
    
    # Save test relationships
    test_relationships = [
        {'source': 'Force', 'target': 'Mass', 'type': 'co_occurs', 'weight': 0.8},
        {'source': 'Force', 'target': 'Acceleration', 'type': 'defines', 'weight': 0.9}
    ]
    db.save_relationships(job_id, test_relationships)
    
    # Update job status
    db.update_job_status(job_id, 'completed')
    
    # Retrieve results
    results = db.get_job_results(job_id)
    print(f"\nRetrieved {len(results['concepts'])} concepts")
    print(f"Retrieved {len(results['relationships'])} relationships")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"\nDatabase statistics: {stats}")
    
    print("\n✅ Database tests passed!")
