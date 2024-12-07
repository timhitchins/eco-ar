from typing import List, Optional
from dataclasses import dataclass


@dataclass
class IssuuItem:
    issuu_name: str
    issuu_url: str
    issuu_img_src: str
    issuu_download_path: Optional[str] = None


@dataclass
class TTCContent:
    ttc_content_title: str
    ttc_items: List[IssuuItem]


@dataclass
class TTCTag:
    "The Talon Conpiracy - Items by Tag"
    ttc_accessible_name: str
    ttc_tag_name: str
    ttc_tag_url: str
    # content is added after tag scrape
    ttc_tag_content: Optional[List[TTCContent]] = None
