import unittest
import pandas as pd
from matcher.ai_matcher import AIMatcher

class TestAIMatcher(unittest.TestCase):

    def setUp(self):
        """Set up test data and AIMatcher instance."""
        self.matcher = AIMatcher()
        self.source_doc = pd.DataFrame({
            'clause': ['1.1', '1.2', '1.3'],
            'description': ['Test A', 'Test B', 'Test C']
        })
        self.target_doc = pd.DataFrame({
            'clause': ['1.1', '1.2', '1.4'],
            'description': ['Test A', 'Test B', 'Test D']
        })

    def test_match_documents(self):
        """Test matching documents using AIMatcher."""
        result = self.matcher.match_documents(
            self.source_doc, self.target_doc, source_col='clause', target_col='clause'
        )
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_invalid_input(self):
        """Test handling of invalid input."""
        with self.assertRaises(ValueError):
            self.matcher.match_documents(None, self.target_doc, source_col='clause', target_col='clause')

if __name__ == '__main__':
    unittest.main()