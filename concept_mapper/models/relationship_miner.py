"""
Relationship Miner Module
Discovers relationships between concepts using multiple methods
"""

from typing import List, Dict, Tuple, Set
import numpy as np
from sentence_transformers import SentenceTransformer, util


class RelationshipMiner:
    """Discover relationships between concepts."""
    
    def __init__(self):
        """Initialize the relationship miner."""
        print("Loading Sentence-BERT model for similarity...")
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def find_cooccurrence_relationships(
        self, 
        text: str, 
        concepts: List[Dict],
        min_count: int = 2
    ) -> List[Dict]:
        """
        Find relationships based on co-occurrence in sentences.
        
        Args:
            text: Full text
            concepts: List of concept dictionaries
            min_count: Minimum co-occurrence count
            
        Returns:
            List of relationship dictionaries
        """
        from utils.helpers import split_into_sentences
        
        sentences = split_into_sentences(text)
        concept_names = [c['name'] for c in concepts]
        
        # Count co-occurrences
        cooccurrences = {}
        
        for sentence in sentences:
            # Find concepts in this sentence
            found = []
            for concept in concept_names:
                if concept.lower() in sentence.lower():
                    found.append(concept)
            
            # Count pairs
            for i, c1 in enumerate(found):
                for c2 in found[i+1:]:
                    pair = tuple(sorted([c1, c2]))
                    cooccurrences[pair] = cooccurrences.get(pair, 0) + 1
        
        # Convert to relationships
        relationships = []
        for (c1, c2), count in cooccurrences.items():
            if count >= min_count:
                # Normalize weight by count (log scale)
                weight = min(1.0, 0.3 + 0.1 * np.log(count + 1))
                
                relationships.append({
                    'source': c1,
                    'target': c2,
                    'type': 'co_occurs',
                    'weight': round(weight, 3),
                    'count': count
                })
        
        return relationships
    
    def find_semantic_relationships(
        self,
        concepts: List[Dict],
        threshold: float = 0.65
    ) -> List[Dict]:
        """
        Find relationships based on semantic similarity.
        
        Args:
            concepts: List of concept dictionaries
            threshold: Minimum similarity threshold
            
        Returns:
            List of relationship dictionaries
        """
        concept_names = [c['name'] for c in concepts]
        
        # Get embeddings
        print("Computing semantic similarities...")
        embeddings = self.similarity_model.encode(
            concept_names,
            convert_to_tensor=True,
            show_progress_bar=True
        )
        
        # Calculate pairwise similarities
        relationships = []
        seen_pairs = set()
        
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                if i == j:
                    continue
                
                # Calculate similarity
                sim = util.cos_sim(
                    embeddings[i].unsqueeze(0),
                    embeddings[j].unsqueeze(0)
                )[0][0].item()
                
                if sim > threshold:
                    pair_key = tuple(sorted([concept_names[i], concept_names[j]]))
                    
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        
                        relationships.append({
                            'source': concept_names[i],
                            'target': concept_names[j],
                            'type': 'semantically_similar',
                            'weight': round(sim, 3),
                            'similarity': round(sim, 3)
                        })
        
        return relationships
    
    def find_prerequisite_relationships(
        self,
        text: str,
        concepts: List[Dict],
        page_structure: Dict = None
    ) -> List[Dict]:
        """
        Find prerequisite relationships (what to learn before what).
        
        Methods:
        1. Temporal: Earlier chapter concepts are prerequisites
        2. Pattern: "To understand X, you need Y" patterns
        3. Definition: "X is defined using Y" patterns
        
        Args:
            text: Full text
            concepts: List of concept dictionaries
            page_structure: Optional structure info from PDF
            
        Returns:
            List of prerequisite relationships
        """
        from utils.helpers import split_into_sentences
        
        prerequisites = []
        concept_names = [c['name'] for c in concepts]
        sentences = split_into_sentences(text)
        
        # Method 1: Look for prerequisite patterns
        prereq_patterns = [
            r'to understand ([\w\s]+),?\s+(?:you must |one should |it is necessary to )?(?:first )?(?:understand|know|learn|study) ([\w\s]+)',
            r'([\w\s]+) is (?:required|needed|necessary|essential) (?:for|to understand) ([\w\s]+)',
            r'before (?:learning|studying|understanding) ([\w\s]+),?\s+(?:one must|you should|it is important to) (?:first )?([\w\s]+)',
            r'([\w\s]+) (?:builds on|extends|relies on|depends on) ([\w\s]+)',
            r'assuming (?:knowledge of|familiarity with) ([\w\s]+)',
            r'as discussed in (?:the )?(?:previous|earlier) (?:section|chapter),?\s+([\w\s]+)'
        ]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            for pattern in prereq_patterns:
                import re
                matches = re.findall(pattern, sentence_lower, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        # Try to match to known concepts
                        candidate_before = match[1].strip()
                        candidate_after = match[0].strip()
                        
                        # Find closest matching concepts
                        before_concept = self._match_to_concept(candidate_before, concept_names)
                        after_concept = self._match_to_concept(candidate_after, concept_names)
                        
                        if before_concept and after_concept and before_concept != after_concept:
                            prerequisites.append({
                                'source': before_concept,
                                'target': after_concept,
                                'type': 'prerequisite',
                                'weight': 0.8,
                                'method': 'pattern'
                            })
        
        # Method 2: Use page/chapter structure (temporal ordering)
        if page_structure and 'pages' in page_structure:
            temporal_prereqs = self._find_temporal_prerequisites(
                page_structure, concepts
            )
            prerequisites.extend(temporal_prereqs)
        
        # Remove duplicates
        unique_prereqs = []
        seen = set()
        
        for prereq in prerequisites:
            key = (prereq['source'], prereq['target'])
            if key not in seen:
                seen.add(key)
                unique_prereqs.append(prereq)
        
        return unique_prereqs
    
    def _match_to_concept(self, candidate: str, concept_names: List[str]) -> str:
        """
        Match a candidate string to the closest known concept.
        
        Args:
            candidate: Candidate phrase
            concept_names: List of known concept names
            
        Returns:
            Best matching concept or None
        """
        if not candidate or len(candidate) < 3:
            return None
        
        # Direct match
        candidate_lower = candidate.lower().strip()
        for concept in concept_names:
            if candidate_lower in concept.lower() or concept.lower() in candidate_lower:
                return concept
        
        # Partial match (at least 2 words match)
        candidate_words = set(candidate_lower.split())
        for concept in concept_names:
            concept_words = set(concept.lower().split())
            overlap = len(candidate_words & concept_words)
            
            if overlap >= 2 or (overlap >= 1 and len(candidate_words) <= 2):
                return concept
        
        return None
    
    def _find_temporal_prerequisites(
        self,
        page_structure: Dict,
        concepts: List[Dict]
    ) -> List[Dict]:
        """
        Find prerequisites based on chapter/page order.
        Concepts appearing earlier are likely prerequisites for later ones.
        """
        prerequisites = []
        concept_pages = {}
        
        # Map concepts to their first appearance page
        pages = page_structure.get('pages', [])
        concept_names = [c['name'] for c in concepts]
        
        for page_info in pages:
            page_num = page_info.get('page_number', 0)
            text = page_info.get('text', '').lower()
            
            for concept in concept_names:
                if concept not in concept_pages and concept.lower() in text:
                    concept_pages[concept] = page_num
        
        # Create prerequisite relationships based on page order
        concept_list = list(concept_pages.items())
        concept_list.sort(key=lambda x: x[1])  # Sort by page number
        
        # For each concept, earlier concepts are potential prerequisites
        for i, (concept1, page1) in enumerate(concept_list):
            for j, (concept2, page2) in enumerate(concept_list):
                if i >= j:
                    continue
                
                # If concepts are far apart (different chapters), likely prerequisite
                if page2 - page1 >= 10:  # At least 10 pages apart
                    prerequisites.append({
                        'source': concept1,
                        'target': concept2,
                        'type': 'prerequisite',
                        'weight': min(0.9, 0.5 + 0.01 * (page2 - page1)),
                        'method': 'temporal',
                        'page_diff': page2 - page1
                    })
        
        return prerequisites[:50]  # Limit number of temporal relationships
    
    def mine_all_relationships(
        self,
        text: str,
        concepts: List[Dict],
        page_structure: Dict = None
    ) -> List[Dict]:
        """
        Mine all types of relationships.
        
        Args:
            text: Full text
            concepts: List of concept dictionaries
            page_structure: Optional structure info
            
        Returns:
            Combined list of all relationships
        """
        print("Mining relationships...")
        
        all_relationships = []
        
        # Method 1: Co-occurrence
        print("  Finding co-occurrence relationships...")
        cooccurrence_rels = self.find_cooccurrence_relationships(text, concepts)
        all_relationships.extend(cooccurrence_rels)
        print(f"    Found {len(cooccurrence_rels)} co-occurrence relationships")
        
        # Method 2: Semantic similarity
        print("  Finding semantic relationships...")
        semantic_rels = self.find_semantic_relationships(concepts)
        all_relationships.extend(semantic_rels)
        print(f"    Found {len(semantic_rels)} semantic relationships")
        
        # Method 3: Prerequisites
        print("  Finding prerequisite relationships...")
        prereq_rels = self.find_prerequisite_relationships(text, concepts, page_structure)
        all_relationships.extend(prereq_rels)
        print(f"    Found {len(prereq_rels)} prerequisite relationships")
        
        # Merge duplicate relationships (keep highest weight)
        merged = {}
        for rel in all_relationships:
            key = tuple(sorted([rel['source'], rel['target']]))
            
            if key not in merged:
                merged[key] = rel
            else:
                # Keep relationship with higher weight
                if rel['weight'] > merged[key]['weight']:
                    merged[key] = rel
        
        result = list(merged.values())
        
        # Sort by weight descending
        result.sort(key=lambda x: x['weight'], reverse=True)
        
        print(f"Total relationships after merging: {len(result)}")
        return result


if __name__ == "__main__":
    # Test the relationship miner
    sample_text = """
    Newton's Second Law states that force equals mass times acceleration.
    To understand force, you must first understand mass. Mass is a fundamental
    property of matter. Acceleration describes how velocity changes over time.
    
    Momentum depends on both mass and velocity. Before studying momentum,
    students should master the concepts of mass and velocity.
    
    Energy is related to force and motion. Kinetic energy builds on the
    concepts of mass and velocity.
    """
    
    test_concepts = [
        {'name': 'Force', 'score': 0.9},
        {'name': 'Mass', 'score': 0.85},
        {'name': 'Acceleration', 'score': 0.8},
        {'name': 'Velocity', 'score': 0.75},
        {'name': 'Momentum', 'score': 0.7},
        {'name': 'Energy', 'score': 0.65},
        {'name': 'Newton\'s Second Law', 'score': 0.95}
    ]
    
    miner = RelationshipMiner()
    relationships = miner.mine_all_relationships(sample_text, test_concepts)
    
    print("\nDiscovered Relationships:")
    for rel in relationships:
        print(f"  {rel['source']} → {rel['target']} ({rel['type']}, weight: {rel['weight']})")
