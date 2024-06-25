import re
from typing import List, Optional, Tuple
import pandas as pd
import pytz
from datetime import datetime, timedelta

from src.modules.document.typing import Document


def document_formatting(doc: Document) -> Tuple[bool, Document]:
    try:
        regex = r"<(\d{4}[-\/年]\d{1,2}[-\/月]\d{1,2}日? \d{1,2}:\d{2});(.*?)(?:;(\d{4}[-\/年]\d{1,2}[-\/月]\d{1,2}日? \d{1,2}:\d{2}))?;>"
        matches = re.findall(regex, doc.page_content)
        if not matches:
            return False, doc

        last_match = matches[-1]
        end_time_str, tags, start_time_str = last_match[0], last_match[1], last_match[2]

        # Convert times to datetime objects
        def parse_time(time_str: Optional[str]) -> datetime:
            if not time_str:
                return pytz.timezone('Asia/Shanghai').localize(datetime.now())
            time_str = time_str.replace(
                '年', '/').replace('月', '/').replace('日', '').strip()
            time_str = time_str.replace(
                '-', '/').strip()
            return datetime.strptime(time_str, "%Y/%m/%d %H:%M")

        # Handle times
        end_time = parse_time(end_time_str)
        start_time = parse_time(start_time_str)

        doc.metadata.start_time = start_time.timestamp()
        doc.metadata.valid_time = end_time.timestamp() - doc.metadata.start_time

        # Handle tags
        doc.metadata.tags.add_tags([tag.strip() for tag in tags.split(',')])

        # Remove the matched format string
        doc.page_content = re.sub(regex, '', doc.page_content).strip()

        return True, doc
    except Exception:
        return False, None


def reverse_document_formatting(doc: Document) -> str:
    try:
        start_time = datetime.fromtimestamp(
            doc.metadata.start_time, pytz.timezone("Asia/Shanghai"))
        valid_time = timedelta(seconds=doc.metadata.valid_time)
        end_time = start_time + valid_time
        tags = doc.metadata.tags.get_tags()

        end_time_str = end_time.strftime("%Y/%m/%d %H:%M")
        start_time_str = start_time.strftime("%Y/%m/%d %H:%M")
        tags_str = ','.join(tags)

        formatted_str = f"<{end_time_str};{tags_str};{start_time_str}>"
        return formatted_str
    except Exception as e:
        return f"Error: {str(e)}"


def process_excel_file(filepath) -> List[Document]:
    df = pd.read_excel(filepath)
    documents = []

    for content in df.iloc[:, 0].dropna().tolist():
        doc = Document(page_content=content)
        formatted, updated_doc = document_formatting(doc)
        if formatted:
            documents.append(updated_doc)

    return documents
