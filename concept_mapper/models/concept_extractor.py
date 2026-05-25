"""
Concept Extractor Module
Extracts important concepts from text using KeyBERT and spaCy
"""

from typing import List, Dict, Tuple
from keybert import KeyBERT
import spacy


class ConceptExtractor:
    """Extract important concepts from textbook text."""
    
    def __init__(self, top_n: int = 75):
        """
        Initialize the concept extractor.
        
        Args:
            top_n: Number of top concepts to extract (default: 75)
        """
        self.top_n = top_n
        
        # Load KeyBERT model for keyword extraction
        print("Loading KeyBERT model...")
        self.kw_model = KeyBERT(model='all-MiniLM-L6-v2')
        
        # Load spaCy model for NER (scientific terms)
        print("Loading spaCy model...")
        try:
            self.nlp = spacy.load('en_core_web_sci')
        except OSError:
            print("Warning: en_core_web_sci not found. Install with: python -m spacy download en_core_web_sci")
            self.nlp = None
    
    def extract_keywords(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract keywords using KeyBERT.
        
        Args:
            text: Input text
            
        Returns:
            List of (keyword, score) tuples
        """
        # Limit text length for KeyBERT (it can be slow on very long texts)
        max_chars = 50000
        if len(text) > max_chars:
            # Take representative chunks
            text_sample = text[:max_chars]
        else:
            text_sample = text
        
        # Extract keywords
        keywords = self.kw_model.extract_keywords(
            text_sample,
            keyphrase_ngram_range=(1, 3),
            stop_words='english',
            top_n=self.top_n * 2,  # Get more initially, will filter later
            use_mmr=True,
            diversity=0.7
        )
        
        return keywords
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities using spaCy.
        
        Args:
            text: Input text
            
        Returns:
            List of entity strings
        """
        if not self.nlp:
            return []
        
        # Process text in chunks to avoid memory issues
        chunk_size = 10000
        entities = set()
        
        for i in range(0, min(len(text), 50000), chunk_size):
            chunk = text[i:i+chunk_size]
            doc = self.nlp(chunk)
            
            for ent in doc.ents:
                # Filter for scientific/technical entities
                if ent.label_ in ['CONCEPT', 'METHOD', 'MATERIAL', 'METRIC'] or \
                   len(ent.text) > 3:
                    entities.add(ent.text.strip())
        
        return list(entities)
    
    def extract_phrases(self, text: str) -> List[str]:
        """
        Extract repeated multi-word phrases from text.
        
        Args:
            text: Input text
            
        Returns:
            List of frequent phrases
        """
        import re
        from collections import Counter
        
        # Find capitalized phrases (likely concepts)
        pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z]?[a-z]+)*)\b'
        matches = re.findall(pattern, text)
        
        # Count frequencies
        phrase_counts = Counter(matches)
        
        # Return phrases that appear at least twice
        frequent_phrases = [
            phrase for phrase, count in phrase_counts.items()
            if count >= 2 and len(phrase) > 3
        ]
        
        return frequent_phrases[:self.top_n]
    
    def extract_concepts(self, text: str) -> List[Dict]:
        """
        Main method to extract concepts combining multiple approaches.
        
        Args:
            text: Full text from textbook
            
        Returns:
            List of concept dictionaries with name and score
        """
        print("Extracting concepts from text...")
        
        # Method 1: KeyBERT keywords
        keywords = self.extract_keywords(text)
        keyword_concepts = {kw: score for kw, score in keywords}
        
        # Method 2: spaCy NER
        entities = self.extract_entities(text)
        
        # Method 3: Frequent phrases
        phrases = self.extract_phrases(text)
        
        # Combine all sources
        all_concepts = {}
        
        # Add KeyBERT results (they have scores)
        for concept, score in keyword_concepts.items():
            # Clean concept name
            concept = concept.strip()
            if len(concept) > 2:
                all_concepts[concept] = score
        
        # Add entities (give them moderate scores)
        for entity in entities:
            entity = entity.strip()
            if len(entity) > 2 and entity not in all_concepts:
                all_concepts[entity] = 0.5  # Default score for entities
        
        # Add frequent phrases
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) > 2 and phrase not in all_concepts:
                all_concepts[phrase] = 0.4  # Lower score for phrases
        
        # Filter and sort
        filtered_concepts = [
            {'name': name, 'score': score}
            for name, score in all_concepts.items()
            if len(name) > 2 and len(name) < 100  # Reasonable length
        ]
        
        # Sort by score descending
        filtered_concepts.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        result = filtered_concepts[:self.top_n]
        
        print(f"Extracted {len(result)} concepts")
        return result
    
    def deduplicate_concepts(self, concepts: List[Dict], threshold: float = 0.85) -> List[Dict]:
        """
        Remove duplicate or highly similar concepts.
        
        Args:
            concepts: List of concept dictionaries
            threshold: Similarity threshold for considering duplicates
            
        Returns:
            Deduplicated list
        """
        from sentence_transformers import SentenceTransformer, util
        
        if not concepts:
            return []
        
        # Load model for similarity comparison
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Get embeddings for all concepts
        concept_names = [c['name'] for c in concepts]
        embeddings = model.encode(concept_names, convert_to_tensor=True)
        
        # Find duplicates
        keep_indices = set(range(len(concepts)))
        
        for i in range(len(concepts)):
            if i not in keep_indices:
                continue
            
            for j in range(i + 1, len(concepts)):
                if j not in keep_indices:
                    continue
                
                # Calculate similarity
                sim = util.cos_sim(embeddings[i].unsqueeze(0), 
                                  embeddings[j].unsqueeze(0))[0][0]
                
                # If too similar, keep the one with higher score
                if sim > threshold:
                    if concepts[i]['score'] >= concepts[j]['score']:
                        keep_indices.discard(j)
                    else:
                        keep_indices.discard(i)
        
        # Return kept concepts
        return [concepts[i] for i in sorted(keep_indices)]


if __name__ == "__main__":
    # Test the concept extractor
    sample_text = """
    Newton's Second Law states that force equals mass times acceleration.
    This fundamental principle of classical mechanics relates the net force
    acting on an object to its mass and acceleration. The law is often written
    as F = ma, where F is force, m is mass, and a is acceleration.
    
    Momentum is another important concept in physics. It depends on both
    mass and velocity. The conservation of momentum is a key principle
    in understanding collisions and interactions between objects.
    
    Energy comes in many forms: kinetic energy, potential energy, thermal
    energy. The law of conservation of energy states that energy cannot
    be created or destroyed, only transformed from one form to another.
    """
    
    extractor = ConceptExtractor(top_n=10)
    concepts = extractor.extract_concepts(sample_text)
    
    print("\nExtracted Concepts:")
    for i, concept in enumerate(concepts, 1):
        print(f"{i}. {concept['name']} (score: {concept['score']:.3f})")
