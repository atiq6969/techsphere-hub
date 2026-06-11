# Concept Mapper - Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies

```bash
cd concept_mapper

# Install Python packages
pip install -r requirements.txt

# Download spaCy scientific model
python -m spacy download en_core_web_sci
```

### Step 2: Run the Application

```bash
# Launch Streamlit app
streamlit run app/main.py
```

The app will open in your browser at `http://localhost:8501`

---

## Usage

### For Students

1. **Upload your textbook PDF** using the file uploader
2. **Click "Generate Concept Map"**
3. **Wait 2-5 minutes** for processing
4. **Explore the interactive graph**:
   - Click nodes to see details
   - Zoom in/out with mouse wheel
   - Drag nodes to rearrange
   - Search for specific concepts

### Understanding the Output

#### Interactive Map Tab
- **Red nodes**: Most important/foundational concepts
- **Yellow nodes**: Medium importance
- **Green nodes**: More specific concepts
- **Red dashed lines**: Prerequisites (learn first!)
- **Blue lines**: Semantic similarity
- **Gray lines**: Co-occurrence

#### Concept List Tab
- All extracted concepts ranked by importance
- Search functionality
- Export to CSV

#### Relationships Tab
- All discovered relationships
- Filter by type (prerequisite, semantic, co-occurrence)
- Export to JSON

#### Analysis Tab
- Graph statistics
- Top 10 most important concepts
- Personalized study recommendations

---

## Example Workflow

### Physics Textbook Example

**Input**: "University Physics" PDF (500 pages)

**Processing Time**: ~3 minutes

**Output**:
- 75 concepts extracted (Force, Energy, Momentum, etc.)
- 200+ relationships discovered
- PageRank identifies "Force" and "Energy" as most foundational
- Prerequisites show: learn Mass → Force → Newton's Laws

**Study Strategy**:
1. Start with top-ranked concepts (highest PageRank)
2. Follow red dashed arrows (prerequisites)
3. Group blue-connected concepts (related topics)

---

## Troubleshooting

### Common Issues

**Problem**: "ModuleNotFoundError: No module named 'spacy'"
**Solution**: 
```bash
pip install spacy
python -m spacy download en_core_web_sci
```

**Problem**: Processing takes too long
**Solution**: 
- Reduce number of concepts in sidebar (try 50 instead of 75)
- Use smaller PDF files first

**Problem**: Out of memory error
**Solution**:
- Close other applications
- Try with shorter PDF (< 200 pages)
- Increase system RAM if possible

**Problem**: No concepts extracted
**Solution**:
- Ensure PDF has text (not scanned images)
- Check that text is in English
- Try a different PDF

---

## Configuration Options

### Sidebar Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Number of concepts | 75 | How many concepts to extract (20-150) |
| Relationship threshold | 0.5 | Minimum strength for relationships |

### Advanced Configuration

Edit `app/main.py` to customize:
- Visualization colors and sizes
- ML model parameters
- Prerequisite detection patterns

---

## Performance Tips

1. **Best Results**: Clear text PDFs with proper formatting
2. **Fastest Processing**: < 200 pages, 50 concepts
3. **Most Accurate**: Technical/scientific textbooks
4. **Avoid**: Scanned image PDFs (need OCR first)

---

## Export Options

### HTML Map
- Interactive visualization
- Can be opened in any browser
- Share with classmates

### JSON Data
- Raw graph data
- Import into other tools
- Programmatic access

### CSV Concepts
- Spreadsheet format
- Easy to filter and sort
- Import into Anki for flashcards

---

## Next Steps

After generating your concept map:

1. **Identify starting points**: Top 3-5 concepts by PageRank
2. **Follow prerequisites**: Red dashed arrows show learning order
3. **Group related topics**: Blue edges show semantic connections
4. **Create study plan**: Use the Analysis tab recommendations
5. **Export to flashcards**: Download CSV and import to Anki

---

## Support

For issues or questions:
- Check the README.md for detailed documentation
- Review troubleshooting section above
- Examine console output for error messages

---

**Happy Learning! 📚✨**

"From 500 pages of confusion to one clear picture in 5 minutes."
