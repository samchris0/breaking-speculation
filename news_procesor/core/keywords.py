import logging
import re
from typing import List, Set
from collections import Counter


import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk import pos_tag

MIN_KEYWORD_LENGTH=3

logger = logging.getLogger(__name__)


class KeywordExtractor:
    """Extracts keywords from news headlines."""
    
    def __init__(self):
        self._ensure_nltk_data()
        
        # Common words to exclude
        self.custom_stopwords = {
            'says', 'new', 'first', 'makes', 'gets', 'takes',
            'may', 'could', 'will', 'would', 'should',
            'news', 'report', 'reports', 'update', 'updates',
            'live', 'breaking', 'latest', 'today', 'now'
        }
        
        # Load stopwords
        try:
            self.stopwords = set(stopwords.words('english'))
            self.stopwords.update(self.custom_stopwords)
        except:
            # Fallback if NLTK data isn't available
            self.stopwords = self.custom_stopwords
            logger.warning("Using minimal stopwords set")
    
    def _ensure_nltk_data(self):

        if nltk is None:
            logger.warning("NLTK not installed, using basic keyword extraction")
            return
            
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download('punkt', quiet=True)
        
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading NLTK stopwords...")
            nltk.download('stopwords', quiet=True)
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            logger.info("Downloading NLTK POS tagger...")
            nltk.download('averaged_perceptron_tagger', quiet=True)
    
    def extract_keywords(self, text: str, max_keywords: int = 4) -> List[str]:
        """
        Extract keywords from text using multiple strategies.
        """

        if not text:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        # Find likely proper nouns
        capitalized_keywords = self._extract_capitalized_terms(text)
        
        # Important noun phrases using POS tagging
        if nltk is not None:
            pos_keywords = self._extract_pos_keywords(text)
        else:
            pos_keywords = []
        
        # words by frequency and length
        freq_keywords = self._extract_by_frequency(text)
        
        all_keywords = capitalized_keywords + pos_keywords + freq_keywords
        
        keyword_counts = Counter(all_keywords)
        
        # Sort by frequency, then by length
        ranked_keywords = sorted(
            keyword_counts.items(),
            key=lambda x: (x[1], len(x[0])),
            reverse=True
        )
        
        # Get unique keywords
        unique_keywords = []
        seen_lower = set()
        
        for keyword, _ in ranked_keywords:
            keyword_lower = keyword.lower()
            
            # Skip if too short or already seen (case-insensitive)
            if len(keyword) < 3 or keyword_lower in seen_lower:
                continue
            
            unique_keywords.append(keyword)
            seen_lower.add(keyword_lower)
            
            if len(unique_keywords) >= max_keywords:
                break
        
        logger.debug(f"Extracted keywords from '{text[:50]}...': {unique_keywords}")
        return unique_keywords
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^\w\s\-]', ' ', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text
    
    def _extract_capitalized_terms(self, text: str) -> List[str]:
        """Extract capitalized words and phrases (likely proper nouns/entities)."""
        keywords = []
        
        # Split into words
        words = text.split()
        
        # Find consecutive capitalized words (multi-word entities)
        i = 0
        while i < len(words):
            if words[i] and words[i][0].isupper():
                # Start of potential entity
                entity_words = [words[i]]
                j = i + 1
                
                # Collect consecutive capitalized words
                while j < len(words) and words[j] and words[j][0].isupper():
                    entity_words.append(words[j])
                    j += 1
                
                entity = ' '.join(entity_words)
                
                # Only add if not a stopword
                if entity.lower() not in self.stopwords and len(entity) >= MIN_KEYWORD_LENGTH:
                    keywords.append(entity)
                
                i = j
            else:
                i += 1
        
        return keywords
    
    def _extract_pos_keywords(self, text: str) -> List[str]:
        """Extract keywords using POS tagging (nouns and proper nouns)."""
        try:
            # Tokenize
            tokens = word_tokenize(text)
            
            # POS tagging
            pos_tags = pos_tag(tokens)
            
            keywords = []
            i = 0
            
            while i < len(pos_tags):
                word, tag = pos_tags[i]
                
                # Look for nouns (NN, NNS) and proper nouns (NNP, NNPS)
                if tag in ['NN', 'NNS', 'NNP', 'NNPS']:
                    # Check for consecutive nouns (noun phrases)
                    phrase_words = [word]
                    j = i + 1
                    
                    while j < len(pos_tags) and pos_tags[j][1] in ['NN', 'NNS', 'NNP', 'NNPS']:
                        phrase_words.append(pos_tags[j][0])
                        j += 1
                    
                    phrase = ' '.join(phrase_words)
                    
                    # Filter stopwords and short words
                    if phrase.lower() not in self.stopwords and len(phrase) >= MIN_KEYWORD_LENGTH:
                        keywords.append(phrase)
                    
                    i = j
                else:
                    i += 1
            
            return keywords
            
        except Exception as e:
            logger.warning(f"Error in POS tagging: {e}")
            return []
    
    def _extract_by_frequency(self, text: str) -> List[str]:
        """Extract keywords by word frequency and significance."""
        # Simple tokenization
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # Filter stopwords and short words
        keywords = [
            word for word in words
            if word not in self.stopwords and len(word) >= MIN_KEYWORD_LENGTH
        ]
        
        return keywords
    
    def extract_from_headlines(self, headlines: List[dict]) -> List[dict]:
        """
        Take list of headline dictionaries with 'title' field and extract keywords
        """

        for headline in headlines:
            title = headline.get('title', '')
            headline['keywords'] = self.extract_keywords(title)
        
        return headlines
