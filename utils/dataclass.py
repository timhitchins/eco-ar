from typing import List, Optional
from dataclasses import dataclass


@dataclass
class IssuuItem:
    issuu_name: str
    issuu_url: str
    issuu_img_src: str
    issuu_download_link: Optional[str] = None
    issuu_filepath: Optional[str] = None


@dataclass
class TTCContent:
    ttc_content_title: str
    ttc_items: List[IssuuItem]
