"""
Reader Agent - Extracts and summarizes paper content.
"""

from typing import Dict, Any
import arxiv
import requests
import io  # <--- NEW: Needed to handle file streams
import pypdf  # <--- NEW: Needed to read the PDF
from .base_agent import BaseAgent


class ReaderAgent(BaseAgent):
    """Agent responsible for reading and extracting paper content."""
    
    def __init__(self, api_key: str = None):
        super().__init__(
            name="ReaderAgent",
            role="Extract paper content from arXiv and provide initial summary",
            api_key=api_key
        )
    
    def fetch_paper_metadata(self, arxiv_id: str) -> Dict[str, Any]:
        """
        Fetch paper metadata from arXiv API.
        """
        self.tool_calls_count += 1
        
        try:
            # Search for paper by ID
            search = arxiv.Search(id_list=[arxiv_id])
            # Use the Client API (Search.results() is deprecated/removed in arxiv>=2.0)
            client = arxiv.Client()
            paper = next(client.results(search))
            
            return {
                "title": paper.title,
                "authors": [author.name for author in paper.authors],
                "abstract": paper.summary,
                "categories": paper.categories,
                "published": str(paper.published),
                "pdf_url": paper.pdf_url,
                "entry_id": paper.entry_id
            }
        except Exception as e:
            return {
                "error": f"Failed to fetch paper: {str(e)}",
                "title": "Unknown",
                "abstract": "Could not retrieve abstract",
                "pdf_url": None
            }

    # --- NEW FUNCTION TO DOWNLOAD AND READ PDF ---
    def extract_text_from_pdf(self, pdf_url: str) -> str:
        """
        Download PDF and extract text content.
        """
        if not pdf_url:
            return ""
            
        print(f"📥 Downloading PDF from: {pdf_url}...")
        try:
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Convert downloaded bytes to a file-like object
            f = io.BytesIO(response.content)
            
            # Read the PDF
            reader = pypdf.PdfReader(f)
            full_text = ""
            
            # Extract text from all pages
            # extract_text() can return None for image-only/empty pages
            for page in reader.pages:
                full_text += (page.extract_text() or "") + "\n"
                
            print(f"✅ Extracted {len(full_text)} characters.")
            return full_text
            
        except Exception as e:
            print(f"❌ Error reading PDF: {e}")
            return ""
    
    def extract_key_points(self, abstract: str) -> Dict[str, Any]:
        """
        Extract key points from abstract using LLM.
        """
        self.tool_calls_count += 1
        
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            {"role": "user", "content": f"""Analyze this paper abstract and extract:
1. Main research question or problem
2. Key methodology or approach
3. Main findings or contributions
4. Significance for students

Abstract:
{abstract}

Provide a clear, student-friendly summary."""}
        ]
        
        response = self.call_llm(messages)
        
        return {
            "summary": response,
            "abstract_length": len(abstract.split())
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process paper and extract content.
        """
        self.tool_calls_count = 0  # Reset so counts don't accumulate across papers
        arxiv_id = input_data.get("arxiv_id", "")
        
        # 1. Fetch metadata
        metadata = self.fetch_paper_metadata(arxiv_id)
        
        if "error" in metadata:
            return self.format_output({
                "status": "error",
                "message": metadata["error"]
            })
        
        # 2. Extract Key Points (LLM Summary of Abstract)
        key_points = self.extract_key_points(metadata["abstract"])
        
        # 3. --- NEW: DOWNLOAD AND EXTRACT FULL TEXT ---
        full_text = self.extract_text_from_pdf(metadata["pdf_url"])
        
        # Combine results
        result = {
            "status": "success",
            "arxiv_id": arxiv_id,
            "metadata": metadata,
            "key_points": key_points,
            "full_text": full_text,  # <--- IMPORTANT: Passing this to the next agent
            "paper_title": metadata["title"],
            "authors": metadata["authors"],
            "categories": metadata["categories"]
        }
        
        return self.format_output(result)