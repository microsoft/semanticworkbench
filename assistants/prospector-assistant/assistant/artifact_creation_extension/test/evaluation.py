def sentence_cosine_similarity(sentence1: str, sentence2: str) -> float:
    """Calculate the cosine similarity between two sentences."""

    raise RuntimeError(
        "This function is disabled because upgrading torch doesn't work on Mac X86, and the torch that does work is no longer secure."
    )

    # from sentence_transformers import SentenceTransformer, SimilarityFunction

    # model = SentenceTransformer("all-mpnet-base-v2", similarity_fn_name=SimilarityFunction.COSINE)

    # sentence1_embeddings = model.encode([sentence1])
    # sentence2_embeddings = model.encode([sentence2])

    # similarities = model.similarity(sentence1_embeddings[0], sentence2_embeddings[0])
    # similarity = similarities[0][0]

    # return similarity.item()
