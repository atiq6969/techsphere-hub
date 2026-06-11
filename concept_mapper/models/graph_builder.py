"""
Graph Builder Module
Builds knowledge graph and generates interactive visualization
"""

from typing import List, Dict, Any
import networkx as nx
from pyvis.network import Network


class GraphBuilder:
    """Build and visualize knowledge graphs."""
    
    def __init__(self):
        """Initialize the graph builder."""
        self.graph = None
    
    def build_graph(
        self,
        concepts: List[Dict],
        relationships: List[Dict]
    ) -> nx.Graph:
        """
        Build a NetworkX graph from concepts and relationships.
        
        Args:
            concepts: List of concept dictionaries
            relationships: List of relationship dictionaries
            
        Returns:
            NetworkX graph object
        """
        print("Building knowledge graph...")
        
        # Create graph
        G = nx.Graph()
        
        # Add nodes (concepts)
        for concept in concepts:
            G.add_node(
                concept['name'],
                score=concept.get('score', 0.5),
                label=concept['name']
            )
        
        # Add edges (relationships)
        for rel in relationships:
            G.add_edge(
                rel['source'],
                rel['target'],
                weight=rel.get('weight', 0.5),
                type=rel.get('type', 'unknown'),
                label=rel.get('type', '')
            )
        
        # Calculate PageRank for importance
        print("  Calculating PageRank scores...")
        try:
            pagerank = nx.pagerank(G, weight='weight')
            
            # Add PageRank as node attribute
            for node, score in pagerank.items():
                G.nodes[node]['pagerank'] = score
                G.nodes[node]['importance'] = round(score, 4)
        except Exception as e:
            print(f"  Warning: Could not calculate PageRank: {e}")
            
            # Set default importance
            for node in G.nodes():
                G.nodes[node]['pagerank'] = 1.0 / len(G.nodes())
                G.nodes[node]['importance'] = 0.5
        
        self.graph = G
        
        num_nodes = G.number_of_nodes()
        num_edges = G.number_of_edges()
        print(f"  Graph built: {num_nodes} concepts, {num_edges} relationships")
        
        return G
    
    def get_top_concepts(self, n: int = 10) -> List[Dict]:
        """
        Get top N most important concepts by PageRank.
        
        Args:
            n: Number of top concepts to return
            
        Returns:
            List of top concept dictionaries
        """
        if not self.graph:
            return []
        
        # Sort by PageRank
        sorted_nodes = sorted(
            self.graph.nodes(data=True),
            key=lambda x: x[1].get('pagerank', 0),
            reverse=True
        )
        
        top_concepts = []
        for node, data in sorted_nodes[:n]:
            top_concepts.append({
                'name': node,
                'importance': data.get('importance', 0),
                'pagerank': data.get('pagerank', 0)
            })
        
        return top_concepts
    
    def create_visualization(
        self,
        output_path: str = "concept_map.html",
        title: str = "Concept Map",
        height: str = "750px",
        width: str = "100%"
    ) -> str:
        """
        Create interactive HTML visualization using Pyvis.
        
        Args:
            output_path: Path to save HTML file
            title: Title of the visualization
            height: Height of the visualization
            width: Width of the visualization
            
        Returns:
            Path to saved HTML file
        """
        if not self.graph:
            raise ValueError("No graph built yet. Call build_graph() first.")
        
        print(f"Creating interactive visualization: {output_path}")
        
        # Create Pyvis network
        net = Network(
            height=height,
            width=width,
            bgcolor="#222222",
            font_color="white",
            notebook=False
        )
        
        # Configure physics for better layout
        net.set_options("""
        var options = {
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.005,
              "springLength": 100,
              "springConstant": 0.18
            },
            "maxVelocity": 146,
            "solver": "forceAtlas2Based",
            "timestep": 0.35,
            "stabilization": {
              "iterations": 150
            }
          },
          "interaction": {
            "hover": true,
            "tooltipDelay": 200,
            "zoomView": true,
            "dragView": true,
            "dragNodes": true
          }
        }
        """)
        
        # Get PageRank scores for sizing
        pagerank_scores = nx.pagerank(self.graph, weight='weight')
        max_score = max(pagerank_scores.values()) if pagerank_scores else 1
        
        # Add nodes with size based on importance
        for node, data in self.graph.nodes(data=True):
            score = data.get('pagerank', 0.5)
            size = 15 + 40 * (score / max_score)  # Size between 15-55
            
            # Color based on importance
            if score > 0.7 * max_score:
                color = "#ff9999"  # Red for high importance
            elif score > 0.4 * max_score:
                color = "#ffff99"  # Yellow for medium
            else:
                color = "#99ff99"  # Green for lower
            
            # Create tooltip with details
            tooltip = f"<b>{node}</b><br>"
            tooltip += f"Importance: {data.get('importance', 0):.4f}<br>"
            
            # Add connected concepts
            neighbors = list(self.graph.neighbors(node))
            if neighbors:
                tooltip += f"Connected to: {len(neighbors)} concepts"
            
            net.add_node(
                node,
                label=node,
                title=tooltip,
                size=size,
                color=color,
                font={'size': 14, 'color': '#000000'}
            )
        
        # Add edges
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            weight = data.get('weight', 0.5)
            rel_type = data.get('type', 'relationship')
            
            # Edge color based on type
            if rel_type == 'prerequisite':
                edge_color = "#ff6666"  # Red for prerequisites
                dashes = True
            elif rel_type == 'semantically_similar':
                edge_color = "#66ccff"  # Blue for semantic
                dashes = False
            else:
                edge_color = "#cccccc"  # Gray for co-occurrence
                dashes = False
            
            # Width based on weight
            edge_width = 1 + 4 * weight
            
            net.add_edge(
                source,
                target,
                value=edge_width,
                color=edge_color,
                title=f"{rel_type} (weight: {weight:.3f})",
                dashes=dashes
            )
        
        # Add legend note
        net.add_node("legend_prereq", label="Prerequisite", size=10, color="#ff6666", x=-100, y=-100)
        net.add_node("legend_semantic", label="Semantic", size=10, color="#66ccff", x=-100, y=-150)
        net.add_node("legend_cooccur", label="Co-occurrence", size=10, color="#cccccc", x=-100, y=-200)
        
        # Save to HTML
        net.save_graph(output_path)
        
        print(f"  Visualization saved to: {output_path}")
        return output_path
    
    def export_to_json(self, output_path: str = "concept_graph.json") -> str:
        """
        Export graph data to JSON format.
        
        Args:
            output_path: Path to save JSON file
            
        Returns:
            Path to saved JSON file
        """
        import json
        
        if not self.graph:
            raise ValueError("No graph built yet.")
        
        print(f"Exporting graph to JSON: {output_path}")
        
        # Prepare data structure
        data = {
            'concepts': [],
            'relationships': [],
            'statistics': {
                'total_concepts': self.graph.number_of_nodes(),
                'total_relationships': self.graph.number_of_edges()
            }
        }
        
        # Add concepts
        for node, attrs in self.graph.nodes(data=True):
            data['concepts'].append({
                'name': node,
                'importance': attrs.get('importance', 0),
                'pagerank': attrs.get('pagerank', 0)
            })
        
        # Add relationships
        for edge in self.graph.edges(data=True):
            source, target, attrs = edge
            data['relationships'].append({
                'source': source,
                'target': target,
                'type': attrs.get('type', 'unknown'),
                'weight': attrs.get('weight', 0.5)
            })
        
        # Sort by importance
        data['concepts'].sort(key=lambda x: x['importance'], reverse=True)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  JSON exported to: {output_path}")
        return output_path
    
    def get_graph_statistics(self) -> Dict:
        """
        Get statistics about the graph.
        
        Returns:
            Dictionary of graph statistics
        """
        if not self.graph:
            return {}
        
        stats = {
            'num_nodes': self.graph.number_of_nodes(),
            'num_edges': self.graph.number_of_edges(),
            'density': nx.density(self.graph),
            'avg_degree': sum(dict(self.graph.degree()).values()) / self.graph.number_of_nodes() if self.graph.number_of_nodes() > 0 else 0,
            'is_connected': nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False,
            'num_components': nx.number_connected_components(self.graph)
        }
        
        # Find central nodes
        try:
            centrality = nx.degree_centrality(self.graph)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]
            stats['most_central'] = [{'name': n, 'centrality': c} for n, c in top_central]
        except:
            stats['most_central'] = []
        
        return stats


def process_and_build(
    text: str,
    concepts: List[Dict],
    relationships: List[Dict],
    output_html: str = "concept_map.html",
    output_json: str = "concept_graph.json"
) -> Dict[str, Any]:
    """
    Convenience function to build graph and create all outputs.
    
    Args:
        text: Source text
        concepts: Extracted concepts
        relationships: Mined relationships
        output_html: Path for HTML output
        output_json: Path for JSON output
        
    Returns:
        Dictionary with paths and statistics
    """
    builder = GraphBuilder()
    
    # Build graph
    graph = builder.build_graph(concepts, relationships)
    
    # Create visualization
    html_path = builder.create_visualization(output_html)
    
    # Export to JSON
    json_path = builder.export_to_json(output_json)
    
    # Get statistics
    stats = builder.get_graph_statistics()
    
    # Get top concepts
    top_concepts = builder.get_top_concepts(n=10)
    
    return {
        'html_path': html_path,
        'json_path': json_path,
        'statistics': stats,
        'top_concepts': top_concepts,
        'graph': graph
    }


if __name__ == "__main__":
    # Test the graph builder
    test_concepts = [
        {'name': 'Force', 'score': 0.9},
        {'name': 'Mass', 'score': 0.85},
        {'name': 'Acceleration', 'score': 0.8},
        {'name': 'Velocity', 'score': 0.75},
        {'name': 'Momentum', 'score': 0.7},
        {'name': 'Energy', 'score': 0.65}
    ]
    
    test_relationships = [
        {'source': 'Force', 'target': 'Mass', 'type': 'co_occurs', 'weight': 0.8},
        {'source': 'Force', 'target': 'Acceleration', 'type': 'defines', 'weight': 0.9},
        {'source': 'Mass', 'target': 'Velocity', 'type': 'prerequisite', 'weight': 0.7},
        {'source': 'Momentum', 'target': 'Mass', 'type': 'depends_on', 'weight': 0.75},
        {'source': 'Momentum', 'target': 'Velocity', 'type': 'depends_on', 'weight': 0.8},
        {'source': 'Energy', 'target': 'Force', 'type': 'semantically_similar', 'weight': 0.65}
    ]
    
    result = process_and_build(
        text="",
        concepts=test_concepts,
        relationships=test_relationships,
        output_html="test_concept_map.html",
        output_json="test_concept_graph.json"
    )
    
    print("\nGraph Statistics:")
    for key, value in result['statistics'].items():
        print(f"  {key}: {value}")
    
    print("\nTop Concepts:")
    for i, concept in enumerate(result['top_concepts'], 1):
        print(f"  {i}. {concept['name']} (importance: {concept['importance']:.4f})")
    
    print(f"\nOutputs created:")
    print(f"  HTML: {result['html_path']}")
    print(f"  JSON: {result['json_path']}")
