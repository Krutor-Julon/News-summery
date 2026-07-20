from sentence_transformers import SentenceTransformer

print("Loading model...")

model = SentenceTransformer("BAAI/bge-small-en-v1.5")

print("Loaded!")

chunks = [
    "Apple released a new MacBook.",
    "Microsoft announced a Windows update.",
    "Google unveiled a new Gemini model."
]

embeddings = model.encode(chunks)

print(len(embeddings))
print(embeddings[0].shape)

"""
OpenAI released a new language model that improves coding.


embedding = model.encode(text)

print(embedding.shape)
print(embedding[:10])
"""