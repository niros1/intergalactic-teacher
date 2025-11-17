"""Text beautification utilities for child-friendly story formatting."""

import re
import logging
from typing import List

logger = logging.getLogger(__name__)


def beautify_story_text(text: str, language: str = "english") -> str:
    """
    Beautify story text by adding line breaks after each sentence.
    
    This makes stories more visually appealing and easier to read for children
    by creating clear separation between sentences.
    
    Args:
        text: The story text to beautify
        language: The language of the text ("english" or "hebrew")
        
    Returns:
        Beautified text with line breaks after each sentence
    """
    if not text or not text.strip():
        return text
    
    logger.info(f"Beautifying story text ({language}) - Length: {len(text)} chars")
    
    # Split into paragraphs first (preserve existing paragraph structure)
    paragraphs = text.split('\n\n')
    beautified_paragraphs = []
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # Beautify each paragraph
        beautified = _beautify_paragraph(paragraph.strip(), language)
        beautified_paragraphs.append(beautified)
    
    # Join paragraphs with double line breaks
    result = '\n\n'.join(beautified_paragraphs)
    
    logger.info(f"Beautification complete - New length: {len(result)} chars")
    return result


def _beautify_paragraph(paragraph: str, language: str) -> str:
    """
    Beautify a single paragraph by adding line breaks after sentences.
    
    Args:
        paragraph: A single paragraph of text
        language: The language of the text
        
    Returns:
        Beautified paragraph with line breaks after sentences
    """
    # Detect sentences using sentence ending punctuation
    sentences = _split_into_sentences(paragraph, language)
    
    if not sentences:
        return paragraph
    
    # Join sentences with single line breaks
    beautified = '\n'.join(sentence.strip() for sentence in sentences if sentence.strip())
    
    return beautified


def _split_into_sentences(text: str, language: str) -> List[str]:
    """
    Split text into sentences intelligently.
    
    Handles:
    - Common sentence endings (. ! ? ...)
    - Quotation marks
    - Abbreviations (Mr. Mrs. Dr. etc.)
    - Decimals and numbers
    - Ellipsis
    
    Args:
        text: The text to split
        language: The language of the text
        
    Returns:
        List of sentences
    """
    # Common abbreviations that shouldn't trigger sentence breaks
    abbreviations = [
        r'Mr\.', r'Mrs\.', r'Ms\.', r'Dr\.', r'Prof\.', r'Sr\.', r'Jr\.',
        r'etc\.', r'vs\.', r'i\.e\.', r'e\.g\.', r'approx\.',
    ]
    
    # Replace abbreviations temporarily to protect them
    protected_text = text
    placeholders = []
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        matches = re.findall(abbr, protected_text, re.IGNORECASE)
        if matches:
            protected_text = re.sub(abbr, placeholder, protected_text, flags=re.IGNORECASE)
            placeholders.append((placeholder, matches[0]))
    
    # Split on sentence-ending punctuation followed by space or end of string
    # Handles: . ! ? ... ." !' ?" etc.
    sentence_pattern = r'([.!?…]+[\"\']?\s+|[.!?…]+[\"\']?$)'
    
    # Split the text
    parts = re.split(sentence_pattern, protected_text)
    
    # Reconstruct sentences by pairing content with their endings
    sentences = []
    current_sentence = ""
    
    for i, part in enumerate(parts):
        if not part.strip():
            continue
            
        # Check if this is a sentence ending
        if re.match(sentence_pattern, part):
            current_sentence += part.strip()
            sentences.append(current_sentence)
            current_sentence = ""
        else:
            current_sentence += part.strip() + " "
    
    # Add any remaining text as a sentence
    if current_sentence.strip():
        sentences.append(current_sentence.strip())
    
    # Restore abbreviations
    restored_sentences = []
    for sentence in sentences:
        restored = sentence
        for placeholder, original in placeholders:
            restored = restored.replace(placeholder, original)
        restored_sentences.append(restored)
    
    return restored_sentences


def add_line_break_after_sentences(text: str, language: str = "english") -> str:
    """
    Add a line break after each sentence in the text.
    
    This is an alias for beautify_story_text for backward compatibility.
    
    Args:
        text: The text to process
        language: The language of the text
        
    Returns:
        Text with line breaks after each sentence
    """
    return beautify_story_text(text, language)


def count_sentences(text: str, language: str = "english") -> int:
    """
    Count the number of sentences in the text.
    
    Args:
        text: The text to analyze
        language: The language of the text
        
    Returns:
        Number of sentences
    """
    sentences = _split_into_sentences(text, language)
    return len([s for s in sentences if s.strip()])


def analyze_text_structure(text: str, language: str = "english") -> dict:
    """
    Analyze the structure of the text.
    
    Args:
        text: The text to analyze
        language: The language of the text
        
    Returns:
        Dictionary with text structure information
    """
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    total_sentences = 0
    paragraph_details = []
    
    for i, paragraph in enumerate(paragraphs, 1):
        sentences = _split_into_sentences(paragraph, language)
        sentence_count = len([s for s in sentences if s.strip()])
        word_count = len(paragraph.split())
        
        total_sentences += sentence_count
        
        paragraph_details.append({
            'paragraph_number': i,
            'sentences': sentence_count,
            'words': word_count,
            'avg_words_per_sentence': word_count / max(sentence_count, 1)
        })
    
    return {
        'total_paragraphs': len(paragraphs),
        'total_sentences': total_sentences,
        'total_words': sum(p['words'] for p in paragraph_details),
        'avg_sentences_per_paragraph': total_sentences / max(len(paragraphs), 1),
        'avg_words_per_sentence': sum(p['words'] for p in paragraph_details) / max(total_sentences, 1),
        'paragraphs': paragraph_details
    }


# Example usage
if __name__ == "__main__":
    # Test with English text
    english_text = """Luna looked up at the stars. They twinkled brightly. She smiled and waved.

The moon was full tonight. It cast a silver glow over the garden. Luna felt happy and peaceful."""

    print("ORIGINAL TEXT:")
    print(english_text)
    print("\n" + "="*80 + "\n")
    
    beautified = beautify_story_text(english_text, "english")
    print("BEAUTIFIED TEXT:")
    print(beautified)
    print("\n" + "="*80 + "\n")
    
    # Analyze structure
    analysis = analyze_text_structure(beautified, "english")
    print("TEXT ANALYSIS:")
    print(f"Total Paragraphs: {analysis['total_paragraphs']}")
    print(f"Total Sentences: {analysis['total_sentences']}")
    print(f"Total Words: {analysis['total_words']}")
    print(f"Avg Words/Sentence: {analysis['avg_words_per_sentence']:.1f}")

