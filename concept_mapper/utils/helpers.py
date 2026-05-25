"""
Helpers Module
Utility functions for text processing and analysis
"""

import re
from typing import List, Dict, Set


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and special characters.
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove page numbers and headers (simple pattern)
    text = re.sub(r'--- PAGE \d+ ---', '', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,;:!?()\-\'\"]+', '', text)
    
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into paragraphs.
    
    Args:
        text: Input text
        
    Returns:
        List of paragraphs
    """
    paragraphs = text.split('\n\n')
    return [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 50]


def extract_ngrams(text: str, n: int = 2) -> List[str]:
    """
    Extract n-grams from text.
    
    Args:
        text: Input text
        n: Number of words in each gram
        
    Returns:
        List of n-grams
    """
    words = text.lower().split()
    ngrams = []
    
    for i in range(len(words) - n + 1):
        ngram = ' '.join(words[i:i+n])
        ngrams.append(ngram)
    
    return ngrams


def count_word_frequencies(text: str) -> Dict[str, int]:
    """
    Count word frequencies in text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary of word frequencies
    """
    words = re.findall(r'\b\w+\b', text.lower())
    frequencies = {}
    
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    
    return frequencies


def remove_stopwords(words: List[str]) -> List[str]:
    """
    Remove common English stopwords from a list of words.
    
    Args:
        words: List of words
        
    Returns:
        List without stopwords
    """
    stopwords = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'whose',
        'where', 'when', 'why', 'how', 'all', 'each', 'every', 'both',
        'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
        'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'also'
    }
    
    return [w for w in words if w.lower() not in stopwords]


def is_likely_concept(phrase: str, min_length: int = 2) -> bool:
    """
    Check if a phrase is likely to be a technical concept.
    
    Args:
        phrase: Candidate phrase
        min_length: Minimum number of words
        
    Returns:
        True if likely a concept
    """
    words = phrase.split()
    
    # Must have minimum length
    if len(words) < min_length:
        return False
    
    # Should not be all stopwords
    content_words = remove_stopwords(words)
    if len(content_words) < 1:
        return False
    
    # Should contain at least one capitalized word or be technical-looking
    has_capital = any(w[0].isupper() for w in words if w)
    is_technical = any(len(w) > 8 for w in words)  # Long words often technical
    
    return has_capital or is_technical or len(content_words) >= 2


def find_cooccurrences(sentences: List[str], concepts: List[str]) -> Dict[tuple, int]:
    """
    Find co-occurrences of concepts in sentences.
    
    Args:
        sentences: List of sentences
        concepts: List of concepts to track
        
    Returns:
        Dictionary of (concept1, concept2) -> count
    """
    cooccurrences = {}
    concept_set = set(concepts)
    
    for sentence in sentences:
        # Find which concepts appear in this sentence
        found_concepts = [c for c in concepts if c.lower() in sentence.lower()]
        
        # Count pairs
        for i, c1 in enumerate(found_concepts):
            for c2 in found_concepts[i+1:]:
                pair = tuple(sorted([c1, c2]))
                cooccurrences[pair] = cooccurrences.get(pair, 0) + 1
    
    return cooccurrences


def normalize_concept_name(name: str) -> str:
    """
    Normalize a concept name for consistent matching.
    
    Args:
        name: Concept name
        
    Returns:
        Normalized name
    """
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Keep original capitalization for display
    return name


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """
    Split long text into overlapping chunks.
    
    Args:
        text: Input text
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            last_period = text.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


if __name__ == "__main__":
    # Test helper functions
    sample_text = """
    Newton's Second Law states that force equals mass times acceleration.
    To understand force, you must first understand mass.
    Momentum depends on mass and velocity.
    """
    
    print("Original text:")
    print(sample_text)
    
    print("\nCleaned text:")
    print(clean_text(sample_text))
    
    print("\nSentences:")
    for sent in split_into_sentences(sample_text):
        print(f"  - {sent}")
    
    print("\nWord frequencies:")
    freqs = count_word_frequencies(sample_text)
    for word, count in sorted(freqs.items(), key=lambda x: -x[1])[:10]:
        print(f"  {word}: {count}")
