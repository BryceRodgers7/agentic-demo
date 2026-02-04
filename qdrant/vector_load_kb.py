import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from qdrant_client.http.models import PointStruct
from fastembed import TextEmbedding  # installed via qdrant-client[fastembed]
import json
from collections import defaultdict

QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
COLLECTION_NAME = "knowledge_base"

print("Connecting to Qdrant...")
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
embedder = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")  # fast + good demo choice

# 0) Load chunks from JSON file
chunks_path = os.path.join(os.path.dirname(__file__), "newchunks.json")
# chunks_path = os.path.join(os.path.dirname(__file__), "chunks.json")
print("Loading chunks from file: ", chunks_path)
with open(chunks_path, "r", encoding="utf-8") as f:
    data = json.load(f)
    chunks = data["chunks"]  # Extract the chunks array from the JSON

print(f"Loaded {len(chunks)} chunks")

# 1) Get vector size from one embedding (using title + content)
sample_text = chunks[0]["title"] + " " + chunks[0]["content"]
sample_vec = next(embedder.embed([sample_text]))
VECTOR_SIZE = len(sample_vec)
print(f"Vector size: {VECTOR_SIZE}")

# 2) Create collection
print("Creating/recreating collection...")
client.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
)

# 3) Prepare texts for embedding (title + content)
print("Generating embeddings...")
texts = [c["title"] + " " + c["content"] for c in chunks]
vectors_iter = embedder.embed(texts)

# 4) Build points with full chunk as payload
points = []
errors = []
for idx, (c, v) in enumerate(zip(chunks, vectors_iter)):
    try:
        # Convert numpy array to list of floats
        vector_list = [float(x) for x in v]
        
        # Rename 'id' to 'chunk_id' in payload to avoid confusion
        payload = {**c}
        payload['chunk_id'] = payload.pop('id')
        
        # Use numeric index as Qdrant point ID (required by Qdrant)
        points.append(
            PointStruct(
                id=idx,  # Use numeric index as point ID
                vector=vector_list,
                payload=payload,  # Store the entire chunk with chunk_id
            ),
        )
    except Exception as e:
        errors.append(f"Error processing chunk {c.get('id', idx)}: {e}")

# 5) Upsert points to Qdrant
print(f"Inserting {len(points)} points into Qdrant...")
client.upsert(collection_name=COLLECTION_NAME, points=points)

# 6) Aggregate metadata
print("Aggregating metadata...")
chunk_list = []
audience_counts = defaultdict(int)
doc_type_counts = defaultdict(int)
category_counts = defaultdict(int)
product_id_counts = defaultdict(int)
tag_counts = defaultdict(int)

for chunk in chunks:
    # Create sorted list entry: chunk_id + title
    chunk_list.append(f"{chunk['id']}: {chunk['title']}")
    
    # Count by audience
    audience_counts[chunk['audience']] += 1
    
    # Count by doc_type
    doc_type_counts[chunk['doc_type']] += 1
    
    # Count by category (handle null)
    category = chunk.get('category')
    if category is not None:
        category_counts[category] += 1
    else:
        category_counts['null'] += 1
    
    # Count by product_id (handle null)
    product_id = chunk.get('product_id')
    if product_id is not None:
        product_id_counts[product_id] += 1
    else:
        product_id_counts['null'] += 1
    
    # Count by tags
    for tag in chunk.get('tags', []):
        tag_counts[tag] += 1

# Sort the chunk list
chunk_list.sort()

# 7) Write metadata to file
print("Writing metadata to chunk_metadata.txt...")
metadata_path = os.path.join(os.path.dirname(__file__), "newchunk_metadata.txt")
# metadata_path = os.path.join(os.path.dirname(__file__), "chunk_metadata.txt")
with open(metadata_path, "w", encoding="utf-8") as f:
    f.write("=" * 80 + "\n")
    f.write("CHUNK METADATA REPORT\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("SORTED CHUNK LIST (ID + Title):\n")
    f.write("-" * 80 + "\n")
    for item in chunk_list:
        f.write(f"{item}\n")
    
    f.write("\n" + "=" * 80 + "\n")
    f.write("METADATA STATISTICS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write(f"AUDIENCE COUNTS:\n")
    for audience, count in sorted(audience_counts.items()):
        f.write(f"  {audience}: {count}\n")
    
    f.write(f"\nDOC_TYPE COUNTS:\n")
    for doc_type, count in sorted(doc_type_counts.items()):
        f.write(f"  {doc_type}: {count}\n")
    
    f.write(f"\nCATEGORY COUNTS:\n")
    for category, count in sorted(category_counts.items()):
        f.write(f"  {category}: {count}\n")
    
    f.write(f"\nPRODUCT_ID COUNTS:\n")
    for product_id, count in sorted(product_id_counts.items(), key=lambda x: (x[0] == 'null', x[0])):
        f.write(f"  {product_id}: {count}\n")
    
    f.write(f"\nTAG COUNTS:\n")
    for tag, count in sorted(tag_counts.items()):
        f.write(f"  {tag}: {count}\n")

# 8) Print summary to console
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✓ Successfully inserted {len(points)} chunks into Qdrant collection '{COLLECTION_NAME}'")

if errors:
    print(f"\n⚠ Encountered {len(errors)} error(s):")
    for error in errors:
        print(f"  - {error}")
else:
    print("✓ No errors encountered")

print(f"\n✓ Metadata report written to chunk_metadata.txt")
print("=" * 80)