#!/usr/bin/env python3
"""
Test improved fact filtering to ensure bad facts are not extracted
"""
import logging

from fact_extractor import FactExtractor
from lmstudio_client import LMStudioClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_fact_filtering():
    """Test that the improved fact extraction rejects inappropriate facts"""

    # Test messages with various types of content
    test_messages = [
        # GOOD facts (should be extracted)
        ("My name is Mark", ["My name is Mark", "name is Mark"]),  # Identity
        ("I like pizza", ["likes pizza"]),  # Preference
        ("I work as a teacher", ["works as a teacher"]),  # Job
        ("I have a dog named Max", ["has a dog named Max"]),  # Pet/relationship
        ("I live in California", ["lives in California"]),  # Location
        ("I play guitar", ["plays guitar"]),  # Hobby
        # BAD facts (should be rejected)
        ("I am feeling happy", []),  # Temporary emotion
        ("I am calm", []),  # Temporary state
        ("The user is feeling calm and happy", []),  # Emotional state
        ("I am going to listen to happy songs", []),  # Immediate intention
        ("I am asking for my name", []),  # Conversational context
        ("I am currently tired", []),  # Temporary condition
        ("I am responding to your question", []),  # Conversational response
        ("I will go to the store later", []),  # Future plan
        ("Right now I am excited", []),  # Temporal emotion
        ("Today I am feeling good", []),  # Daily emotion
    ]

    try:
        # Initialize LLM client and fact extractor
        llm_client = LMStudioClient()

        if not llm_client.check_connection():
            return False

        fact_extractor = FactExtractor(llm_client)

        all_passed = True

        for message, expected_keywords in test_messages:

            try:
                # Extract facts using the improved system
                extracted_facts = fact_extractor.extract_facts_from_message(message)

                for fact in extracted_facts:
                    pass

                # Check if extraction matches expectations
                if not expected_keywords:
                    # Should extract no facts
                    if extracted_facts:
                        all_passed = False
                    else:
                        pass
                else:
                    # Should extract facts containing the expected keywords
                    if not extracted_facts:
                        all_passed = False
                    else:
                        found_match = False
                        for fact in extracted_facts:
                            for keyword in expected_keywords:
                                if keyword.lower() in fact["fact"].lower():
                                    found_match = True
                                    break
                            if found_match:
                                break

                        if found_match:
                            pass
                        else:
                            all_passed = False

            except Exception:
                all_passed = False

        if all_passed:
            pass
        else:
            pass

        return all_passed

    except Exception:
        return False


def main():
    """Run the fact filtering tests"""
    success = test_fact_filtering()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
