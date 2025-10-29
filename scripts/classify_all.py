"""
Simple runner to classify all banks from data/processed/knowledge_base.json
and write per-bank classification files into results/classifications/
"""
import os
import sys
from src.models.parameter_classifier import ParameterClassifier


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    kb = os.path.join(root, "data", "processed", "knowledge_base.json")
    # allow override by env or arg
    if len(sys.argv) > 1:
        kb = sys.argv[1]

    keywords = os.path.join(root, "data", "processed", "parameter_classification.json")
    out = os.path.join(root, "results", "classifications")
    clf = ParameterClassifier(keywords)
    res = clf.classify_all(kb, out)
    print("Done. Index:", res["index_path"])


if __name__ == "__main__":
    main()
