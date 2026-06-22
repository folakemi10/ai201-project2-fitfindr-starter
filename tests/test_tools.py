"""
tests/test_tools.py

Comprehensive pytest tests for FitFindr tools with coverage of failure modes.
Tests cover:
  - search_listings: filtering, scoring, edge cases
  - suggest_outfit: empty wardrobe, LLM integration
  - create_fit_card: empty outfit, missing fields, LLM integration
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import search_listings, suggest_outfit, create_fit_card


# ── Fixtures and Mock Data ────────────────────────────────────────────────────

@pytest.fixture
def mock_listings():
    """Return a mock listings dataset for testing."""
    return [
        {
            "id": "1",
            "title": "Vintage Graphic Tee",
            "description": "Faded vintage band tee from the 90s",
            "category": "tops",
            "style_tags": ["vintage", "band", "graphic"],
            "size": "M",
            "condition": "good",
            "price": 15.99,
            "colors": ["white", "black"],
            "brand": "Hanes",
            "platform": "depop",
        },
        {
            "id": "2",
            "title": "Black Skinny Jeans",
            "description": "Classic black denim with stretch",
            "category": "bottoms",
            "style_tags": ["denim", "skinny", "classic"],
            "size": "S/M",
            "condition": "excellent",
            "price": 24.50,
            "colors": ["black"],
            "brand": "Levi's",
            "platform": "thredUp",
        },
        {
            "id": "3",
            "title": "Oversized Flannel Shirt",
            "description": "Red and white oversized flannel, perfect for layering",
            "category": "tops",
            "style_tags": ["flannel", "oversized", "vintage"],
            "size": "L",
            "condition": "fair",
            "price": 18.99,
            "colors": ["red", "white"],
            "brand": "Pendleton",
            "platform": "poshmark",
        },
        {
            "id": "4",
            "title": "White Leather Sneakers",
            "description": "Minimal white leather sneakers",
            "category": "shoes",
            "style_tags": ["sneakers", "minimal", "leather"],
            "size": "8",
            "condition": "good",
            "price": 35.00,
            "colors": ["white"],
            "brand": "Nike",
            "platform": "depop",
        },
    ]


@pytest.fixture
def mock_wardrobe():
    """Return a mock wardrobe with items."""
    return {
        "items": [
            {
                "id": "w_001",
                "title": "Baggy straight-leg jeans, dark wash",
                "category": "bottoms",
                "colors": ["dark blue", "indigo"],
                "style_tags": ["denim", "streetwear", "baggy"],
            },
            {
                "id": "w_002",
                "title": "White ribbed tank top",
                "category": "tops",
                "colors": ["white"],
                "style_tags": ["basics", "minimal", "fitted"],
            },
            {
                "id": "w_003",
                "title": "Black cropped zip hoodie",
                "category": "tops",
                "colors": ["black"],
                "style_tags": ["athletic", "streetwear", "cropped"],
            },
        ]
    }


@pytest.fixture
def empty_wardrobe():
    """Return an empty wardrobe."""
    return {"items": []}


@pytest.fixture
def sample_listing():
    """Return a single sample listing."""
    return {
        "id": "1",
        "title": "Vintage Band Tee",
        "description": "90s graphic tee",
        "category": "tops",
        "style_tags": ["vintage", "graphic"],
        "size": "M",
        "condition": "good",
        "price": 15.99,
        "colors": ["white", "black"],
        "brand": "Hanes",
        "platform": "depop",
    }


# ────────────────────────────────────────────────────────────────────────────
# TESTS: search_listings()
# ────────────────────────────────────────────────────────────────────────────


class TestSearchListings:
  
    @patch("tools.load_listings")
    def test_search_listings_exact_keyword_match(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage")
        
        assert len(results) >= 1
        assert any("vintage" in item["title"].lower() for item in results)

    @patch("tools.load_listings")
    def test_search_listings_no_results(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("nonexistent_item_xyz")
        
        assert results == []

    @patch("tools.load_listings")
    def test_search_listings_price_filter(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage", max_price=20.00)
        
        assert all(item["price"] <= 20.00 for item in results)

    @patch("tools.load_listings")
    def test_search_listings_price_filter_no_match(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage", max_price=5.00)
        
        assert results == []

    @patch("tools.load_listings")
    def test_search_listings_size_filter(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("jeans", size="S/M")
        
        # Check that results include S/M size
        assert len(results) > 0

    @patch("tools.load_listings")
    def test_search_listings_combined_filters(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("tee", size="M", max_price=20.00)
        
        assert all(item["price"] <= 20.00 for item in results)

    @patch("tools.load_listings")
    def test_search_listings_empty_description(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("")
        
        assert results == []

    @patch("tools.load_listings")
    def test_search_listings_scoring_order(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage graphic")
        
        # Vintage Graphic Tee should score highest
        if len(results) > 0:
            assert "graphic" in results[0].get("style_tags", []) or \
                   "graphic" in results[0]["title"].lower()

    @patch("tools.load_listings")
    def test_search_listings_empty_dataset(self, mock_load):
        mock_load.return_value = []
        results = search_listings("anything")
        
        assert results == []

    @patch("tools.load_listings")
    def test_search_listings_case_insensitive(self, mock_load, mock_listings):
        """Test: search is case-insensitive."""
        mock_load.return_value = mock_listings
        results_lower = search_listings("vintage")
        results_upper = search_listings("VINTAGE")
        
        assert len(results_lower) == len(results_upper)

    @patch("tools.load_listings")
    def test_search_listings_negative_price(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage", max_price=-10.00)
        
        assert results == []

    @patch("tools.load_listings")
    def test_search_listings_zero_price(self, mock_load, mock_listings):
        mock_load.return_value = mock_listings
        results = search_listings("vintage", max_price=0.00)
        
        assert results == []


# ────────────────────────────────────────────────────────────────────────────
# TESTS: suggest_outfit()
# ────────────────────────────────────────────────────────────────────────────


class TestSuggestOutfit:
    """Test suite for suggest_outfit() function."""

    @patch("tools.client")
    def test_suggest_outfit_empty_wardrobe(self, mock_client, sample_listing, empty_wardrobe):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "This vintage band tee would pair well with basic staples."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = suggest_outfit(sample_listing, empty_wardrobe)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Verify LLM was called with empty wardrobe handling
        mock_client.chat.completions.create.assert_called_once()

    @patch("tools.client")
    def test_suggest_outfit_with_wardrobe(self, mock_client, sample_listing, mock_wardrobe):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Pair this tee with your dark jeans and add the hoodie as a layer."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = suggest_outfit(sample_listing, mock_wardrobe)
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Verify LLM was called with wardrobe items
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args
        assert "Baggy" in str(call_args)  # Wardrobe item should be in prompt

    @patch("tools.client")
    def test_suggest_outfit_missing_new_item_fields(self, mock_client, empty_wardrobe):
        incomplete_item = {
            "id": "999",
        }
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Styling advice here."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = suggest_outfit(incomplete_item, empty_wardrobe)
        
        assert isinstance(result, str)
        
    @patch("tools.client")
    def test_suggest_outfit_llm_failure(self, mock_client, sample_listing, empty_wardrobe):
        """Test: suggest_outfit handles LLM API errors."""
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            suggest_outfit(sample_listing, empty_wardrobe)

    @patch("tools.client")
    def test_suggest_outfit_returns_non_empty_string(self, mock_client, sample_listing, mock_wardrobe):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Outfit suggestion"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = suggest_outfit(sample_listing, mock_wardrobe)
        
        assert isinstance(result, str)
        assert len(result.strip()) > 0

    @patch("tools.client")
    def test_suggest_outfit_with_none_wardrobe_items(self, mock_client, sample_listing):
        wardrobe = {}  # Missing 'items' key
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "General styling advice."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = suggest_outfit(sample_listing, wardrobe)
        
        assert isinstance(result, str)
        assert len(result) > 0


# ────────────────────────────────────────────────────────────────────────────
# TESTS: create_fit_card()
# ────────────────────────────────────────────────────────────────────────────


class TestCreateFitCard:
    
    def test_create_fit_card_empty_outfit(self, sample_listing):
        result = create_fit_card("", sample_listing)
        
        assert isinstance(result, str)
        assert "Unable to generate" in result or "no outfit" in result.lower()

    def test_create_fit_card_whitespace_outfit(self, sample_listing):
        result = create_fit_card("   \n\t  ", sample_listing)
        
        assert isinstance(result, str)
        assert "Unable to generate" in result or "no outfit" in result.lower()

    @patch("tools.client")
    def test_create_fit_card_valid_outfit(self, mock_client, sample_listing):
        outfit = "Pair with black jeans and white sneakers for a classic look."
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Found this vintage band tee on Depop for $15.99 — instantly made my vibe cooler. Paired it with black jeans and my white sneakers for that effortless 90s energy. This is the thrift find I didn't know I needed."
        mock_client.chat.completions.create.return_value = mock_response
        
        result = create_fit_card(outfit, sample_listing)
        
        assert isinstance(result, str)
        assert len(result) > 0
        mock_client.chat.completions.create.assert_called_once()

    @patch("tools.client")
    def test_create_fit_card_includes_price(self, mock_client, sample_listing):
        outfit = "Casual streetwear look"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Caption mentioning $15.99"
        mock_client.chat.completions.create.return_value = mock_response
        
        create_fit_card(outfit, sample_listing)
        
        call_args = mock_client.chat.completions.create.call_args
        assert "$15.99" in str(call_args)

    @patch("tools.client")
    def test_create_fit_card_includes_platform(self, mock_client, sample_listing):
        outfit = "Casual streetwear look"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Caption"
        mock_client.chat.completions.create.return_value = mock_response
        
        create_fit_card(outfit, sample_listing)
        
        call_args = mock_client.chat.completions.create.call_args
        assert "depop" in str(call_args).lower()

    @patch("tools.client")
    def test_create_fit_card_missing_item_fields(self, mock_client):
        outfit = "Casual look"
        incomplete_item = {
            # Missing: title, price, platform, condition
        }
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Generated caption"
        mock_client.chat.completions.create.return_value = mock_response
        
        result = create_fit_card(outfit, incomplete_item)
        
        assert isinstance(result, str)

    @patch("tools.client")
    def test_create_fit_card_llm_failure(self, mock_client, sample_listing):
        outfit = "Valid outfit description"
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception):
            create_fit_card(outfit, sample_listing)

    @patch("tools.client")
    def test_create_fit_card_uses_high_temperature(self, mock_client, sample_listing):
        outfit = "Casual streetwear"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Caption"
        mock_client.chat.completions.create.return_value = mock_response
        
        create_fit_card(outfit, sample_listing)
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        # Temperature should be set higher for creativity
        assert call_kwargs.get("temperature", 0) >= 0.8

    @patch("tools.client")
    def test_create_fit_card_max_tokens(self, mock_client, sample_listing):
        outfit = "Casual look"
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Short caption"
        mock_client.chat.completions.create.return_value = mock_response
        
        create_fit_card(outfit, sample_listing)
        
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "max_tokens" in call_kwargs
        assert call_kwargs["max_tokens"] <= 500


# ────────────────────────────────────────────────────────────────────────────
# Integration Tests
# ────────────────────────────────────────────────────────────────────────────


class TestToolsIntegration:
    """Integration tests using multiple tools together."""

    @patch("tools.load_listings")
    @patch("tools.client")
    def test_search_then_suggest_outfit(self, mock_client, mock_load, mock_listings, mock_wardrobe):
        mock_load.return_value = mock_listings
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Great outfit suggestion"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Search for a tee
        search_results = search_listings("vintage tee")
        assert len(search_results) > 0
        
        # Suggest outfit with first result
        outfit = suggest_outfit(search_results[0], mock_wardrobe)
        assert isinstance(outfit, str)
        assert len(outfit) > 0

    @patch("tools.load_listings")
    @patch("tools.client")
    def test_full_workflow(self, mock_client, mock_load, mock_listings, mock_wardrobe):
        """Test: complete workflow from search → outfit → fit card."""
        mock_load.return_value = mock_listings
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Great outfit suggestion"
        mock_client.chat.completions.create.return_value = mock_response
        
        # 1. Search
        search_results = search_listings("vintage")
        assert len(search_results) > 0
        
        # 2. Suggest outfit
        outfit = suggest_outfit(search_results[0], mock_wardrobe)
        assert len(outfit) > 0
        
        # 3. Create fit card
        mock_response.choices[0].message.content = "Amazing caption"
        fit_card = create_fit_card(outfit, search_results[0])
        assert len(fit_card) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
