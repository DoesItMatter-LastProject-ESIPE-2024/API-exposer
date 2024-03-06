import json
from typing import Any, Dict
from pdf_parser.feature import Features


if __name__ == '__main__':
    with open('pdf_parser/out/tmp.json', 'r', encoding='utf-8') as f:
        clusters: Dict[str, Any] = json.load(f)

    features = {
        int(id, 0): Features.__from_json__(json_feature)
        for id, json_feature in clusters.items()
    }

    print(features[6].get_features_by_map(0))
    print(features[6].get_features_by_map(1))
