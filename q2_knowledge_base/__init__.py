"""Question 2 - production-ready knowledge base used by Q1 and Q3 voice agents."""

from .retriever import Retriever, SearchResponse, get_retriever

__all__ = ["Retriever", "SearchResponse", "get_retriever"]
