# Concept Mapper - README

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📚 Concept Mapper from Textbook PDF

**AI-powered tool that automatically reads any textbook PDF, extracts important concepts, discovers relationships between them, and displays them as an interactive visual graph.**

### ✨ Features

- **Automatic Concept Extraction**: Extracts 50-100 important concepts from any textbook
- **Relationship Mining**: Discovers connections using co-occurrence, semantic similarity, and prerequisite detection
- **Interactive Visualization**: Creates beautiful, interactive HTML knowledge graphs
- **Completely FREE**: No API costs, runs locally on your laptop
- **No GPU Required**: Works with 4-8 GB RAM on normal student laptops
- **Fast Processing**: 2-5 minutes for a 500-page textbook

### 🎯 Problem Solved

Students face 3 main problems with large textbooks:
1. **Don't know where to start** - No clear "start here" marker
2. **Can't see connections** - Related topics scattered across chapters
3. **No prerequisite guidance** - No one tells you "learn X before Y"

**Concept Mapper solves all three!**

### 🚀 Quick Start

#### Installation

```bash
# Clone the repository
git clone <repository-url>
cd concept_mapper

# Install dependencies
pip install -r requirements.txt

# Download spaCy scientific model
python -m spacy download en_core_web_sci
```

#### Usage

```bash
# Run the Streamlit app
streamlit run app/main.py
```

Then:
1. Upload your textbook PDF
2. Wait 2-5 minutes for processing
3. Explore the interactive concept map!

### 📁 Project Structure

```
concept_mapper/
├── app/                    # Main application
│   ├── main.py            # Streamlit UI
│   └── api.py             # FastAPI backend (optional)
├── models/                 # ML model wrappers
│   ├── concept_extractor.py
│   ├── relationship_miner.py
│   └── graph_builder.py
├── utils/                  # Utility functions
│   ├── pdf_processor.py
│   └── helpers.py
├── data/                   # Database and storage
│   └── database.py
├── static/                 # Static files
├── templates/              # HTML templates
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### 🔧 Technical Details

#### ML Models Used

| Model | Type | Size | Purpose |
|-------|------|------|---------|
| Sentence-BERT (all-MiniLM-L6-v2) | Transformer | 80 MB | Semantic similarity |
| KeyBERT | BERT-based | 80 MB | Concept extraction |
| spaCy (en_core_web_sci) | NER | 50 MB | Scientific term detection |
| PageRank | Graph Algorithm | - | Concept importance ranking |

#### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 4 GB | 8 GB |
| Storage | 500 MB | 1 GB |
| Processor | Intel i3 | Intel i5+ |
| GPU | Not required | Not required |
| OS | Windows/Mac/Linux | Any |

### 📊 Example Output

**Input**: Physics textbook PDF (500 pages)

**Output**: Interactive HTML graph showing:
- 75 concepts (Newton's Laws, Force, Mass, Energy, etc.)
- 200+ relationships with weights
- Prerequisite chains (what to learn first)
- Importance scores via PageRank

### 🎓 Use Cases

1. **Students**: Upload textbook before exam, see all important topics at once
2. **Professors**: Check syllabus order, find missing prerequisites
3. **Self-learners**: Get clear learning path without a teacher
4. **Curriculum designers**: Identify foundational concepts

### ⚙️ How It Works

```
PDF Upload
    ↓
[Step 1] PyMuPDF → Extract text
    ↓
[Step 2] KeyBERT + spaCy → Find 50-100 concepts
    ↓
[Step 3] Co-occurrence + Similarity → Discover relationships
    ↓
[Step 4] NetworkX + PageRank → Build knowledge graph
    ↓
Interactive HTML Output
```

### 📝 Sample Code

```python
from app.models.concept_extractor import ConceptExtractor
from app.models.relationship_miner import RelationshipMiner
from app.models.graph_builder import GraphBuilder

# Initialize
extractor = ConceptExtractor()
miner = RelationshipMiner()
builder = GraphBuilder()

# Process PDF
text = extractor.extract_text("physics.pdf")
concepts = extractor.extract_concepts(text)
relationships = miner.find_relationships(text, concepts)
graph = builder.build_graph(concepts, relationships)

# Generate visualization
graph.save_html("concept_map.html")
```

### 🛠️ Limitations

- Scanned PDFs (images) need OCR - not supported yet
- Very large textbooks (1000+ pages) may take 10+ minutes
- Some rare technical terms may be missed
- Works best with clear English text
- Equations and formulas are not extracted
- Requires internet for first-time model download (~200 MB)

### 🔮 Future Work

- [ ] Add OCR support for scanned textbooks
- [ ] Compare two textbooks (differences/similarities)
- [ ] Generate practice questions from relationships
- [ ] Personalized study path recommendations
- [ ] Multi-language support (Hindi, Spanish, etc.)
- [ ] Extract equations and formulas
- [ ] Export to Anki flashcards
- [ ] Browser extension for online textbooks

### 📄 License

MIT License - Feel free to use for your projects!

### 🙏 Acknowledgments

- BERT (Devlin et al., Google, 2018)
- SciBERT (Beltagy et al., 2019)
- Sentence-BERT (Reimers & Gurevych, 2019)
- PageRank (Larry Page, Google, 1999)

---

**"From 500 pages of confusion to one clear picture in 5 minutes."** 🚀
