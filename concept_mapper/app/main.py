"""
Concept Mapper - Main Application
Streamlit UI for processing textbooks and viewing concept maps
"""

import streamlit as st
import os
import tempfile
from pathlib import Path

# Import our modules
from utils.pdf_processor import PDFProcessor, process_pdf
from models.concept_extractor import ConceptExtractor
from models.relationship_miner import RelationshipMiner
from models.graph_builder import GraphBuilder


def initialize_session_state():
    """Initialize session state variables."""
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    if 'concepts' not in st.session_state:
        st.session_state.concepts = []
    if 'relationships' not in st.session_state:
        st.session_state.relationships = []
    if 'html_path' not in st.session_state:
        st.session_state.html_path = None
    if 'json_path' not in st.session_state:
        st.session_state.json_path = None
    if 'stats' not in st.session_state:
        st.session_state.stats = {}


def main():
    """Main Streamlit application."""
    
    # Page configuration
    st.set_page_config(
        page_title="Concept Mapper",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-header">📚 Concept Mapper</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Transform any textbook into an interactive knowledge graph</div>', unsafe_allow_html=True)
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        num_concepts = st.slider(
            "Number of concepts to extract",
            min_value=20,
            max_value=150,
            value=75,
            step=10
        )
        
        relationship_threshold = st.slider(
            "Relationship threshold",
            min_value=0.3,
            max_value=0.9,
            value=0.5,
            step=0.05
        )
        
        st.markdown("---")
        st.markdown("**About**")
        st.markdown("""
        Concept Mapper uses AI to:
        - Extract key concepts from textbooks
        - Discover relationships between concepts
        - Identify prerequisites
        - Create interactive visualizations
        
        **ML Models:**
        - KeyBERT (concept extraction)
        - Sentence-BERT (similarity)
        - spaCy (NER)
        - PageRank (importance)
        """)
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # File uploader
        uploaded_file = st.file_uploader(
            "Upload your textbook PDF",
            type=["pdf"],
            help="Upload a textbook PDF to generate a concept map"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Uploaded: {uploaded_file.name}")
            
            # Show file info
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.info(f"File size: {file_size_mb:.2f} MB")
            
            # Process button
            if st.button("🚀 Generate Concept Map", type="primary", use_container_width=True):
                process_pdf_file(uploaded_file, num_concepts, relationship_threshold)
    
    with col2:
        # Quick stats
        st.subheader("📊 Quick Stats")
        
        if st.session_state.processing_complete and st.session_state.stats:
            stats = st.session_state.stats
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("Concepts", stats.get('num_concepts', 0))
            with col_b:
                st.metric("Relationships", stats.get('num_relationships', 0))
            
            col_c, col_d = st.columns(2)
            with col_c:
                st.metric("Graph Density", f"{stats.get('density', 0):.3f}")
            with col_d:
                st.metric("Components", stats.get('num_components', 1))
            
            # Top concepts
            if stats.get('top_concepts'):
                st.markdown("**Top 5 Concepts:**")
                for i, concept in enumerate(stats['top_concepts'][:5], 1):
                    st.text(f"{i}. {concept['name']}")
        else:
            st.info("Upload a PDF and click 'Generate' to see statistics")
    
    # Results section
    if st.session_state.processing_complete:
        st.markdown("---")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs([
            "🎯 Interactive Map",
            "📋 Concept List",
            "🔗 Relationships",
            "📈 Analysis"
        ])
        
        with tab1:
            show_interactive_map()
        
        with tab2:
            show_concept_list()
        
        with tab3:
            show_relationships()
        
        with tab4:
            show_analysis()


def process_pdf_file(uploaded_file, num_concepts: int, relationship_threshold: float):
    """Process the uploaded PDF file."""
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Step 1: Extract text from PDF
        st.markdown("### Processing Pipeline")
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Step 1/4: Extracting text from PDF...")
        pdf_processor = PDFProcessor()
        
        if not pdf_processor.open_pdf(tmp_path):
            st.error("Failed to open PDF file")
            return
        
        result = pdf_processor.extract_text_with_structure()
        full_text = result['full_text']
        page_structure = result
        
        progress_bar.progress(25)
        
        # Show text preview
        with st.expander("📄 Preview extracted text"):
            st.text(full_text[:2000] + "...")
            st.text(f"Total characters: {len(full_text)}")
            st.text(f"Total pages: {result.get('total_pages', 'Unknown')}")
        
        # Step 2: Extract concepts
        status_text.text(f"Step 2/4: Extracting {num_concepts} concepts...")
        extractor = ConceptExtractor(top_n=num_concepts)
        concepts = extractor.extract_concepts(full_text)
        
        progress_bar.progress(50)
        
        with st.expander("🏷️ View extracted concepts"):
            for i, concept in enumerate(concepts[:20], 1):
                st.text(f"{i}. {concept['name']} (score: {concept['score']:.3f})")
            if len(concepts) > 20:
                st.text(f"... and {len(concepts) - 20} more")
        
        # Step 3: Mine relationships
        status_text.text("Step 3/4: Mining relationships...")
        miner = RelationshipMiner()
        relationships = miner.mine_all_relationships(
            full_text,
            concepts,
            page_structure
        )
        
        progress_bar.progress(75)
        
        # Step 4: Build graph
        status_text.text("Step 4/4: Building knowledge graph...")
        builder = GraphBuilder()
        graph = builder.build_graph(concepts, relationships)
        
        # Create outputs
        output_dir = Path(tempfile.gettempdir()) / "concept_mapper"
        output_dir.mkdir(exist_ok=True)
        
        html_path = str(output_dir / "concept_map.html")
        json_path = str(output_dir / "concept_graph.json")
        
        builder.create_visualization(html_path)
        builder.export_to_json(json_path)
        
        # Get statistics
        stats = builder.get_graph_statistics()
        top_concepts = builder.get_top_concepts(n=10)
        
        progress_bar.progress(100)
        status_text.text("✅ Processing complete!")
        
        # Store in session state
        st.session_state.processing_complete = True
        st.session_state.concepts = concepts
        st.session_state.relationships = relationships
        st.session_state.html_path = html_path
        st.session_state.json_path = json_path
        st.session_state.stats = {
            'num_concepts': len(concepts),
            'num_relationships': len(relationships),
            'density': stats.get('density', 0),
            'num_components': stats.get('num_components', 1),
            'top_concepts': top_concepts
        }
        
        st.success("✨ Concept map generated successfully!")
        st.balloons()
        
        # Auto-scroll to results
        st.rerun()
        
    except Exception as e:
        st.error(f"Error during processing: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def show_interactive_map():
    """Display the interactive concept map."""
    
    if st.session_state.html_path and os.path.exists(st.session_state.html_path):
        # Read HTML file
        with open(st.session_state.html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Display using components
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        # Download button
        with open(st.session_state.html_path, 'rb') as f:
            st.download_button(
                label="📥 Download HTML Map",
                data=f.read(),
                file_name="concept_map.html",
                mime="text/html"
            )
    else:
        st.warning("No concept map available. Please process a PDF first.")


def show_concept_list():
    """Display the list of extracted concepts."""
    
    if st.session_state.concepts:
        concepts = st.session_state.concepts
        
        # Search box
        search_term = st.text_input("🔍 Search concepts...", "")
        
        # Filter concepts
        filtered = concepts
        if search_term:
            filtered = [
                c for c in concepts
                if search_term.lower() in c['name'].lower()
            ]
        
        st.write(f"Showing {len(filtered)} of {len(concepts)} concepts")
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(filtered)
        df.columns = ['Concept', 'Score']
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download button
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="concepts.csv",
            mime="text/csv"
        )
    else:
        st.warning("No concepts available. Please process a PDF first.")


def show_relationships():
    """Display the relationships between concepts."""
    
    if st.session_state.relationships:
        relationships = st.session_state.relationships
        
        # Filter by type
        rel_types = set(r['type'] for r in relationships)
        selected_type = st.selectbox(
            "Filter by relationship type",
            options=["All"] + list(rel_types)
        )
        
        # Filter relationships
        filtered = relationships
        if selected_type != "All":
            filtered = [r for r in relationships if r['type'] == selected_type]
        
        st.write(f"Showing {len(filtered)} of {len(relationships)} relationships")
        
        # Display as table
        import pandas as pd
        df = pd.DataFrame(filtered)
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Download button
        json_data = open(st.session_state.json_path, 'rb').read()
        st.download_button(
            label="📥 Download JSON",
            data=json_data,
            file_name="concept_graph.json",
            mime="application/json"
        )
    else:
        st.warning("No relationships available. Please process a PDF first.")


def show_analysis():
    """Show detailed analysis of the concept map."""
    
    if not st.session_state.processing_complete:
        st.warning("Please process a PDF first.")
        return
    
    stats = st.session_state.stats
    
    # Overview
    st.subheader("📊 Graph Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Concepts", stats.get('num_concepts', 0))
    with col2:
        st.metric("Total Relationships", stats.get('num_relationships', 0))
    with col3:
        st.metric("Avg Connections", f"{stats.get('density', 0) * 100:.1f}%")
    with col4:
        st.metric("Graph Components", stats.get('num_components', 1))
    
    # Top concepts
    st.subheader("🏆 Most Important Concepts")
    st.markdown("Ranked by PageRank algorithm (foundational concepts)")
    
    if stats.get('top_concepts'):
        for i, concept in enumerate(stats['top_concepts'][:10], 1):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{i}. {concept['name']}**")
            with col_b:
                st.write(f"Importance: {concept['importance']:.4f}")
    
    # Recommendations
    st.subheader("💡 Study Recommendations")
    
    if stats.get('top_concepts'):
        top_3 = stats['top_concepts'][:3]
        
        st.markdown("""
        Based on the analysis, here's a suggested learning order:
        
        1. **Start with foundational concepts** (highest PageRank scores)
        2. **Follow prerequisite chains** (red dashed arrows in the map)
        3. **Group related concepts** (blue edges show semantic similarity)
        """)
        
        st.info(f"""
        **Recommended starting points:**
        - {top_3[0]['name']}
        - {top_3[1]['name']}
        - {top_3[2]['name']}
        
        These concepts appear most frequently and connect to many other topics.
        Master these first for better understanding!
        """)


if __name__ == "__main__":
    main()
