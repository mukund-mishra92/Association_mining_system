"""
HTML Database Schema Parser
Parses the database_schema.htm file to extract table and column information.
"""

from typing import Dict, List, Tuple
from pathlib import Path
from bs4 import BeautifulSoup
import re


class SchemaParser:
    """Parser for HTML database schema files."""
    
    def __init__(self, schema_file_path: str):
        """
        Initialize the schema parser.
        
        Args:
            schema_file_path: Path to the HTML schema file
        """
        self.schema_file_path = Path(schema_file_path)
        self.tables: Dict[str, List[Dict[str, str]]] = {}
        
    def parse(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Parse the HTML schema file and extract table structures.
        
        Returns:
            Dictionary mapping table names to list of column dictionaries
        """
        if not self.schema_file_path.exists():
            raise FileNotFoundError(f"Schema file not found: {self.schema_file_path}")
        
        with open(self.schema_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all table anchors
        table_anchors = soup.find_all('a', attrs={'name': True})
        
        for anchor in table_anchors:
            table_name = anchor.get('name')
            if not table_name or table_name.strip() == '':
                continue
            
            # Get the next table element that contains field information
            current = anchor.find_next('table')
            if not current:
                continue
            
            # Skip the header table, look for the field data table
            field_table = current.find_next('table', attrs={'border': '1'})
            if not field_table:
                continue
            
            # Extract column information
            columns = self._parse_columns(field_table)
            if columns:
                self.tables[table_name] = columns
        
        return self.tables
    
    def _parse_columns(self, table) -> List[Dict[str, str]]:
        """
        Parse column information from a table element.
        
        Args:
            table: BeautifulSoup table element
            
        Returns:
            List of column dictionaries with field details
        """
        columns = []
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue
            
            column = {
                'field': self._clean_text(cells[0].get_text()),
                'type': self._clean_text(cells[1].get_text()),
                'collation': self._clean_text(cells[2].get_text()),
                'null': self._clean_text(cells[3].get_text()),
                'key': self._clean_text(cells[4].get_text()),
                'default': self._clean_text(cells[5].get_text()),
                'extra': self._clean_text(cells[6].get_text()),
                'comment': self._clean_text(cells[8].get_text()) if len(cells) > 8 else ''
            }
            columns.append(column)
        
        return columns
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        return text.strip().replace('\xa0', '').replace('(NULL)', '')
    
    def get_table_schema(self, table_name: str) -> str:
        """
        Get formatted schema for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Formatted schema string
        """
        if table_name not in self.tables:
            return ""
        
        columns = self.tables[table_name]
        schema_lines = [f"Table: {table_name}"]
        schema_lines.append("Columns:")
        
        for col in columns:
            key_info = f" [{col['key']}]" if col['key'] else ""
            null_info = " NULL" if col['null'] == 'YES' else " NOT NULL"
            extra_info = f" {col['extra']}" if col['extra'] else ""
            
            schema_lines.append(
                f"  - {col['field']}: {col['type']}{key_info}{null_info}{extra_info}"
            )
        
        return "\n".join(schema_lines)
    
    def get_all_schemas(self) -> str:
        """
        Get formatted schema for all tables.
        
        Returns:
            Formatted schema string for all tables
        """
        all_schemas = []
        for table_name in sorted(self.tables.keys()):
            all_schemas.append(self.get_table_schema(table_name))
        
        return "\n\n".join(all_schemas)
    
    def get_compact_schema(self) -> str:
        """
        Get compact schema suitable for LLM system prompts.
        Only includes essential information.
        
        Returns:
            Compact schema string
        """
        compact_lines = ["Database Schema:"]
        
        for table_name in sorted(self.tables.keys()):
            columns = self.tables[table_name]
            
            # Get primary key and important columns
            pk_cols = [c['field'] for c in columns if c['key'] == 'PRI']
            col_list = [f"{c['field']} ({c['type']})" for c in columns]
            
            pk_info = f" [PK: {', '.join(pk_cols)}]" if pk_cols else ""
            compact_lines.append(f"\n{table_name}{pk_info}:")
            compact_lines.append(f"  {', '.join(col_list)}")
        
        return "\n".join(compact_lines)
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names."""
        return sorted(self.tables.keys())
    
    def search_tables(self, keyword: str) -> List[str]:
        """
        Search for tables containing a keyword in their name.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching table names
        """
        keyword_lower = keyword.lower()
        return [
            table for table in self.tables.keys()
            if keyword_lower in table.lower()
        ]


def get_schema_parser() -> SchemaParser:
    """
    Get initialized schema parser with default schema file.
    
    Returns:
        SchemaParser instance
    """
    schema_file = Path(__file__).parent.parent / "data" / "database" / "database_schema.htm"
    parser = SchemaParser(str(schema_file))
    parser.parse()
    return parser
