import os
import json
import re
from typing import Dict, List


class ParameterClassifier:
    """Rule-based classifier for knowledge_base parameters.

    Outputs classification: 'client_requirement', 'product_feature', or 'ambiguous'
    with matched keywords as rationale.
    """

    def __init__(self, keywords_path: str = None):
        # load default keyword file if provided
        self.keywords = {"client_requirement": [], "product_feature": []}
        if keywords_path and os.path.exists(keywords_path):
            with open(keywords_path, "r", encoding="utf-8") as f:
                obj = json.load(f)
                kws = obj.get("keywords", {})
                # normalize keywords to lowercase
                self.keywords["client_requirement"] = [k.lower() for k in kws.get("client_requirement", [])]
                self.keywords["product_feature"] = [k.lower() for k in kws.get("product_feature", [])]
        else:
            # fallback built-in small lists
            self.keywords["client_requirement"] = ["wiek", "minimum", "musi", "miesięcy", "lat", "umowa", "zaświadczenie", "ważność"]
            self.keywords["product_feature"] = ["oprocentowanie", "wibor", "marża", "rata", "ltv", "ubezpieczenie", "operat"]

    def _find_matches(self, text: str, keywords: List[str]) -> List[str]:
        text_l = text.lower()
        matches = []
        for kw in keywords:
            # use simple substring or word boundary matching for multi-word tokens
            if " " in kw:
                if kw in text_l:
                    matches.append(kw)
            else:
                # word boundary to avoid partial matches
                if re.search(r"\b" + re.escape(kw) + r"\b", text_l):
                    matches.append(kw)
        return matches

    def classify_param(self, key: str, value: str) -> Dict:
        combined = f"{key} {value or ''}".strip()
        combined = combined.replace("\n", " ")
        client_matches = self._find_matches(combined, self.keywords["client_requirement"])
        product_matches = self._find_matches(combined, self.keywords["product_feature"])

        # Scoring: number of matches (simple)
        client_score = len(client_matches)
        product_score = len(product_matches)

        if client_score > product_score:
            cls = "client_requirement"
        elif product_score > client_score:
            cls = "product_feature"
        else:
            # tie or zero => ambiguous; apply heuristics for numeric patterns
            # if contains month/year numbers or 'dni' treat as client requirement
            if re.search(r"\b(\d{1,3})\s*(miesi(ą|c)c|miesięcy|lat|dni)\b", combined.lower()):
                cls = "client_requirement"
            else:
                cls = "ambiguous"

        rationale = {
            "client_matches": client_matches,
            "product_matches": product_matches,
            "client_score": client_score,
            "product_score": product_score,
        }

        return {"key": key, "value": value, "classification": cls, "rationale": rationale}

    def classify_bank(self, bank_obj: Dict) -> Dict:
        out = {"bank_name": bank_obj.get("bank_name"), "categories": {}, "summary": {}}
        total = {"client_requirement": 0, "product_feature": 0, "ambiguous": 0}
        params = bank_obj.get("parameters", {})
        for cat, cat_body in params.items():
            out["categories"][cat] = {}
            for p_key, p_val in cat_body.items():
                entry = self.classify_param(str(p_key), str(p_val))
                out["categories"][cat][p_key] = entry
                total[entry["classification"]] += 1

        out["summary"] = total
        return out

    def classify_all(self, knowledge_path: str, output_dir: str) -> Dict:
        os.makedirs(output_dir, exist_ok=True)
        with open(knowledge_path, "r", encoding="utf-8") as f:
            kb = json.load(f)

        results_index = {}
        products = kb.get("products", []) if isinstance(kb, dict) else kb
        for prod in products:
            bank_name = prod.get("bank_name", "unknown_bank")
            safe_name = re.sub(r"[^0-9a-zA-Z_-]", "_", bank_name)
            classified = self.classify_bank(prod)
            out_path = os.path.join(output_dir, f"{safe_name}.classified.json")
            with open(out_path, "w", encoding="utf-8") as of:
                json.dump(classified, of, ensure_ascii=False, indent=2)
            results_index[bank_name] = out_path

        # write index
        index_path = os.path.join(output_dir, "index.json")
        with open(index_path, "w", encoding="utf-8") as idxf:
            json.dump(results_index, idxf, ensure_ascii=False, indent=2)

        return {"index_path": index_path, "files": results_index}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify knowledge_base parameters")
    parser.add_argument("--knowledge", default=os.path.join("data", "processed", "knowledge_base.json"), help="Path to knowledge_base.json")
    parser.add_argument("--keywords", default=os.path.join("data", "processed", "parameter_classification.json"), help="Path to parameter_classification.json")
    parser.add_argument("--out", default=os.path.join("results", "classifications"), help="Output directory for classifications")
    args = parser.parse_args()

    clf = ParameterClassifier(args.keywords)
    res = clf.classify_all(args.knowledge, args.out)
    print(f"Wrote classifications index: {res['index_path']}")
