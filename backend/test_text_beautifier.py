"""Test script for text beautification utility."""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.text_beautifier import (
    beautify_story_text,
    count_sentences,
    analyze_text_structure,
)


def test_basic_beautification():
    """Test basic text beautification."""
    print("\n" + "="*80)
    print("TEST 1: BASIC BEAUTIFICATION")
    print("="*80 + "\n")
    
    original_text = """Luna looked up at the stars. They twinkled brightly. She smiled and waved. The night was magical!

The moon was full tonight. It cast a silver glow over the garden. Luna felt happy and peaceful. She loved these quiet moments."""
    
    print("ORIGINAL TEXT:")
    print(original_text)
    print("\n" + "-"*80 + "\n")
    
    beautified = beautify_story_text(original_text, "english")
    
    print("BEAUTIFIED TEXT (with line breaks after each sentence):")
    print(beautified)
    print("\n" + "-"*80 + "\n")
    
    # Count sentences
    sentence_count = count_sentences(beautified, "english")
    print(f"Total Sentences: {sentence_count}")
    
    return beautified


def test_with_quotes_and_punctuation():
    """Test with quotes and various punctuation."""
    print("\n" + "="*80)
    print("TEST 2: QUOTES AND PUNCTUATION")
    print("="*80 + "\n")
    
    original_text = '''"Hello, Luna!" said her friend Max. "What are you doing?" Luna replied, "I'm watching the stars. Aren't they beautiful?"

Max nodded. "They are amazing!" he exclaimed. They sat together in silence.'''
    
    print("ORIGINAL TEXT:")
    print(original_text)
    print("\n" + "-"*80 + "\n")
    
    beautified = beautify_story_text(original_text, "english")
    
    print("BEAUTIFIED TEXT:")
    print(beautified)
    print("\n" + "-"*80 + "\n")
    
    sentence_count = count_sentences(beautified, "english")
    print(f"Total Sentences: {sentence_count}")


def test_with_abbreviations():
    """Test with abbreviations like Mr., Mrs., Dr., etc."""
    print("\n" + "="*80)
    print("TEST 3: ABBREVIATIONS")
    print("="*80 + "\n")
    
    original_text = """Dr. Luna was a brilliant scientist. She worked with Prof. Smith and Mr. Johnson. They discovered something amazing!

Mrs. Martinez joined the team later. She brought new ideas and energy. Together they changed the world."""
    
    print("ORIGINAL TEXT:")
    print(original_text)
    print("\n" + "-"*80 + "\n")
    
    beautified = beautify_story_text(original_text, "english")
    
    print("BEAUTIFIED TEXT:")
    print(beautified)
    print("\n" + "-"*80 + "\n")
    
    sentence_count = count_sentences(beautified, "english")
    print(f"Total Sentences: {sentence_count}")


def test_with_ellipsis():
    """Test with ellipsis and multiple punctuation."""
    print("\n" + "="*80)
    print("TEST 4: ELLIPSIS AND SPECIAL CASES")
    print("="*80 + "\n")
    
    original_text = """Luna waited... and waited... Finally, something happened! The stars began to move. What was happening?!

She couldn't believe her eyes. This was incredible! She had to tell someone."""
    
    print("ORIGINAL TEXT:")
    print(original_text)
    print("\n" + "-"*80 + "\n")
    
    beautified = beautify_story_text(original_text, "english")
    
    print("BEAUTIFIED TEXT:")
    print(beautified)
    print("\n" + "-"*80 + "\n")
    
    sentence_count = count_sentences(beautified, "english")
    print(f"Total Sentences: {sentence_count}")


def test_hebrew_text():
    """Test with Hebrew text (RTL)."""
    print("\n" + "="*80)
    print("TEST 5: HEBREW TEXT")
    print("="*80 + "\n")
    
    original_text = """לונה הביטה למעלה אל הכוכבים. הם נצצו בבהירות. היא חייכה ונופפה. הלילה היה קסום!

הירח היה מלא הלילה. הוא הטיל זוהר כסוף על הגן. לונה הרגישה מאושרת ושלווה."""
    
    print("ORIGINAL TEXT (Hebrew):")
    print(original_text)
    print("\n" + "-"*80 + "\n")
    
    beautified = beautify_story_text(original_text, "hebrew")
    
    print("BEAUTIFIED TEXT (Hebrew):")
    print(beautified)
    print("\n" + "-"*80 + "\n")
    
    sentence_count = count_sentences(beautified, "hebrew")
    print(f"Total Sentences: {sentence_count}")


def test_text_analysis():
    """Test text structure analysis."""
    print("\n" + "="*80)
    print("TEST 6: TEXT STRUCTURE ANALYSIS")
    print("="*80 + "\n")
    
    original_text = """Luna loved adventures. Every day she explored new places. She never got tired of discovering!

One day she found a secret garden. It was hidden behind a tall hedge. Inside were the most beautiful flowers she had ever seen.

Luna decided to visit every day. She brought her sketchbook to draw the flowers. This became her favorite place in the whole world."""
    
    print("ANALYZING TEXT STRUCTURE:")
    print("\n" + original_text)
    print("\n" + "-"*80 + "\n")
    
    analysis = analyze_text_structure(original_text, "english")
    
    print("ANALYSIS RESULTS:")
    print(f"  Total Paragraphs: {analysis['total_paragraphs']}")
    print(f"  Total Sentences: {analysis['total_sentences']}")
    print(f"  Total Words: {analysis['total_words']}")
    print(f"  Avg Sentences/Paragraph: {analysis['avg_sentences_per_paragraph']:.1f}")
    print(f"  Avg Words/Sentence: {analysis['avg_words_per_sentence']:.1f}")
    
    print("\n  PARAGRAPH DETAILS:")
    for para in analysis['paragraphs']:
        print(f"    Paragraph {para['paragraph_number']}: {para['sentences']} sentences, "
              f"{para['words']} words, {para['avg_words_per_sentence']:.1f} words/sentence")


def test_before_and_after_comparison():
    """Show before and after comparison of story text."""
    print("\n" + "="*80)
    print("TEST 7: BEFORE & AFTER COMPARISON")
    print("="*80 + "\n")
    
    story_text = """Once upon a time, there was a curious girl named Luna who loved to explore. She lived in a small village surrounded by tall mountains and deep forests. Every night, Luna would look up at the stars and wonder what adventures awaited her.

One magical evening, Luna discovered a glowing path in the forest. She followed it carefully, her heart beating with excitement. The path led her to a beautiful clearing where fireflies danced in the moonlight. It was the most amazing thing she had ever seen!"""
    
    print("📖 BEFORE BEAUTIFICATION:")
    print("-" * 80)
    print(story_text)
    
    beautified = beautify_story_text(story_text, "english")
    
    print("\n\n✨ AFTER BEAUTIFICATION (Line break after each sentence):")
    print("-" * 80)
    print(beautified)
    
    # Show analysis
    print("\n\n📊 IMPROVEMENT SUMMARY:")
    print("-" * 80)
    original_analysis = analyze_text_structure(story_text, "english")
    beautified_analysis = analyze_text_structure(beautified, "english")
    
    print(f"Original: {original_analysis['total_sentences']} sentences in {original_analysis['total_paragraphs']} paragraphs")
    print(f"Beautified: {beautified_analysis['total_sentences']} sentences with line breaks for clarity")
    print("\n✅ Each sentence is now on its own line for easier reading!")
    print("✅ Perfect for children aged 7-12!")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("🧪 TEXT BEAUTIFIER TEST SUITE")
    print("="*80)
    
    test_basic_beautification()
    test_with_quotes_and_punctuation()
    test_with_abbreviations()
    test_with_ellipsis()
    test_hebrew_text()
    test_text_analysis()
    test_before_and_after_comparison()
    
    print("\n" + "="*80)
    print("✅ ALL TESTS COMPLETED!")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()

