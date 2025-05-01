from typing import List, Dict

def get_results_data() -> List[Dict[str, str]]:
    return [
        {"id": 1, "filename": "image1.jpg", "status": "duplicate"},
        {"id": 2, "filename": "image2.jpg", "status": "unique"}
    ]

def get_trash_data() -> List[Dict[str, str]]:
    return [
        {"id": 1, "filename": "deleted_image1.jpg"},
        {"id": 2, "filename": "deleted_image2.jpg"}
    ]
