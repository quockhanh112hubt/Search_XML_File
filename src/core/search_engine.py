"""
Search Engine Module
Implements various search algorithms for XML content
"""

import re
import io
import logging
from typing import List, Optional, Generator, Tuple, Dict, Any
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import iterparse

# Try to import ahocorasick, fallback to basic search if not available
try:
    import ahocorasick
    HAS_AHOCORASICK = True
except ImportError:
    HAS_AHOCORASICK = False

from config.settings import DEFAULT_CHUNK_SIZE, CHUNK_OVERLAP_SIZE

logger = logging.getLogger(__name__)

# Log ahocorasick availability after logger is defined
if not HAS_AHOCORASICK:
    logger.warning("ahocorasick not available, using basic string search")

logger = logging.getLogger(__name__)

class SearchResult:
    """Search result container"""
    
    def __init__(self, date_dir: str, filename: str, match_type: str, 
                 match_content: str = "", line_number: int = 0):
        self.date_dir = date_dir
        self.filename = filename
        self.match_type = match_type
        self.match_content = match_content
        self.line_number = line_number
        self.file_path = f"/{date_dir}/Send File/{filename}"

class TextSearchEngine:
    """Text-based search engine using various algorithms"""
    
    def __init__(self, keywords: List[str], case_sensitive: bool = False, 
                 use_regex: bool = False):
        self.keywords = [k.strip() for k in keywords if k.strip()]
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self.compiled_patterns = []
        self.aho_corasick = None
        
        if not self.keywords:
            raise ValueError("At least one keyword is required")
            
        self._prepare_search_patterns()
    
    def _prepare_search_patterns(self):
        """Prepare search patterns based on search type"""
        if self.use_regex:
            # Compile regex patterns
            flags = 0 if self.case_sensitive else re.IGNORECASE
            for keyword in self.keywords:
                try:
                    pattern = re.compile(keyword, flags)
                    self.compiled_patterns.append(pattern)
                except re.error as e:
                    logger.error(f"Invalid regex pattern '{keyword}': {e}")
                    # Fallback to literal search
                    escaped = re.escape(keyword)
                    pattern = re.compile(escaped, flags)
                    self.compiled_patterns.append(pattern)
        else:
            # Use Aho-Corasick for multiple string matching if available
            if HAS_AHOCORASICK:
                self.aho_corasick = ahocorasick.Automaton()
            else:
                self.aho_corasick = None
                # Prepare keywords for basic search
                if not self.case_sensitive:
                    self.keywords = [k.lower() for k in self.keywords]
            for idx, keyword in enumerate(self.keywords):
                search_word = keyword if self.case_sensitive else keyword.lower()
                if self.aho_corasick:  # Only if ahocorasick is available
                    self.aho_corasick.add_word(search_word, (idx, keyword))
            if self.aho_corasick:
                self.aho_corasick.make_automaton()
    
    def search_in_stream(self, stream_func, date_dir: str, filename: str,
                        chunk_size: int = DEFAULT_CHUNK_SIZE, 
                        early_termination: bool = True) -> Optional[SearchResult]:
        """Search in file stream using chunked reading"""
        buffer = b""
        line_number = 1
        found_result = None
        
        try:
            def chunk_callback(data):
                nonlocal buffer, line_number, found_result
                
                logger.debug(f"Received chunk: {len(data)} bytes")
                
                # Skip processing if we already found result and want early termination
                if found_result and early_termination:
                    logger.debug("Early termination - skipping chunk processing")
                    return
                    
                buffer += data
                logger.debug(f"Buffer size after adding chunk: {len(buffer)} bytes")
                
                # Process complete chunks (but only if we haven't found result or not using early termination)
                chunk_count = 0
                while len(buffer) >= chunk_size and (not found_result or not early_termination):
                    chunk_count += 1
                    logger.debug(f"Processing chunk #{chunk_count}, buffer size: {len(buffer)}")
                    
                    chunk = buffer[:chunk_size]
                    buffer = buffer[chunk_size - CHUNK_OVERLAP_SIZE:]
                    
                    # Search in chunk
                    result = self._search_in_chunk(chunk, date_dir, filename, line_number)
                    if result:
                        logger.debug(f"Found match in chunk #{chunk_count}")
                        if not found_result:  # Take first result found
                            found_result = result
                            if early_termination:
                                # Don't process more chunks, but can't stop stream here
                                logger.debug("Early termination triggered - breaking chunk loop")
                                break
                    
                    # Update line number
                    line_number += chunk.count(b'\n')
                
                logger.debug(f"Finished processing chunks. Processed {chunk_count} chunks, buffer remaining: {len(buffer)} bytes")
            
            logger.debug(f"Starting stream processing for {filename}")
            # Process stream
            stream_func(chunk_callback)
            logger.debug(f"Stream processing completed for {filename}")
            
            # If we found a result during streaming, return it
            if found_result:
                return found_result
            
            # Process remaining buffer if no result found yet
            if buffer:
                return self._search_in_chunk(buffer, date_dir, filename, line_number)
                
        except Exception as e:
            logger.error(f"Error searching in {filename}: {e}")
            
        return None
    
    def _search_in_chunk(self, chunk: bytes, date_dir: str, filename: str, 
                        line_number: int) -> Optional[SearchResult]:
        """Search within a single chunk"""
        try:
            # Decode chunk
            text = chunk.decode('utf-8', errors='ignore')
            search_text = text if self.case_sensitive else text.lower()
            
            if self.use_regex:
                # Regex search
                for pattern in self.compiled_patterns:
                    match = pattern.search(text)
                    if match:
                        match_line = line_number + text[:match.start()].count('\n')
                        return SearchResult(
                            date_dir, filename, "Regex Match",
                            match.group(), match_line
                        )
            else:
                # Aho-Corasick multi-string search or fallback to basic search
                if self.aho_corasick:
                    # Use Aho-Corasick
                    for end_index, (keyword_idx, original_keyword) in self.aho_corasick.iter(search_text):
                        start_index = end_index - len(original_keyword) + 1
                        match_line = line_number + search_text[:start_index].count('\n')
                        
                        # Get context around match
                        context_start = max(0, start_index - 50)
                        context_end = min(len(text), end_index + 50)
                        context = text[context_start:context_end].strip()
                        
                        return SearchResult(
                            date_dir, filename, "Text Match",
                            context, match_line
                        )
                else:
                    # Fallback to basic string search
                    for keyword in self.keywords:
                        search_keyword = keyword if self.case_sensitive else keyword.lower()
                        if search_keyword in search_text:
                            index = search_text.find(search_keyword)
                            match_line = line_number + search_text[:index].count('\n')
                            
                            # Get context around match
                            context_start = max(0, index - 50)
                            context_end = min(len(text), index + len(search_keyword) + 50)
                            context = text[context_start:context_end].strip()
                            
                            return SearchResult(
                                date_dir, filename, "Text Match",
                                context, match_line
                            )
                    
        except Exception as e:
            logger.error(f"Error processing chunk: {e}")
            
        return None

class XPathSearchEngine:
    """XPath-based search engine for XML structure"""
    
    def __init__(self, xpath_expressions: List[str]):
        self.xpath_expressions = [expr.strip() for expr in xpath_expressions if expr.strip()]
        if not self.xpath_expressions:
            raise ValueError("At least one XPath expression is required")
    
    def search_in_stream(self, stream_func, date_dir: str, filename: str) -> Optional[SearchResult]:
        """Search in XML stream using iterparse"""
        try:
            # Create a pipe for streaming XML data
            xml_buffer = io.BytesIO()
            
            def collect_data(data):
                xml_buffer.write(data)
            
            # Collect all data first (for XML parsing)
            stream_func(collect_data)
            xml_buffer.seek(0)
            
            # Parse XML with iterparse for memory efficiency
            try:
                for event, elem in iterparse(xml_buffer, events=('start', 'end')):
                    if event == 'end':
                        # Check XPath expressions
                        for xpath_expr in self.xpath_expressions:
                            try:
                                # Simple XPath evaluation
                                if self._evaluate_xpath(elem, xpath_expr):
                                    # Found match
                                    return SearchResult(
                                        date_dir, filename, "XPath Match",
                                        f"XPath: {xpath_expr}", 0
                                    )
                            except Exception as e:
                                logger.error(f"XPath evaluation error: {e}")
                        
                        # Clear element to save memory
                        elem.clear()
                        
            except ET.ParseError as e:
                logger.error(f"XML parse error in {filename}: {e}")
                
        except Exception as e:
            logger.error(f"Error in XPath search for {filename}: {e}")
            
        return None
    
    def _evaluate_xpath(self, element, xpath_expr: str) -> bool:
        """Simple XPath evaluation (basic implementation)"""
        try:
            # This is a simplified XPath evaluator
            # For full XPath support, consider using lxml
            
            if xpath_expr.startswith('//'):
                # Search in all descendants
                tag_name = xpath_expr[2:]
                return element.find(f".//{tag_name}") is not None
            elif xpath_expr.startswith('/'):
                # Absolute path
                parts = xpath_expr[1:].split('/')
                current = element
                for part in parts:
                    current = current.find(part)
                    if current is None:
                        return False
                return True
            else:
                # Relative search
                return element.find(xpath_expr) is not None
                
        except Exception:
            return False

class SearchEngineFactory:
    """Factory for creating search engines"""
    
    @staticmethod
    def create_text_search(keywords: List[str], case_sensitive: bool = False,
                          use_regex: bool = False) -> TextSearchEngine:
        """Create text search engine"""
        return TextSearchEngine(keywords, case_sensitive, use_regex)
    
    @staticmethod
    def create_xpath_search(xpath_expressions: List[str]) -> XPathSearchEngine:
        """Create XPath search engine"""
        return XPathSearchEngine(xpath_expressions)
