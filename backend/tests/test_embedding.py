from app.services.embedding_service import get_embedding_service


def test_embedding_service_singleton() -> None:
    svc1 = get_embedding_service()
    svc2 = get_embedding_service()
    assert svc1 is svc2


def test_embedding_dimension_and_batch() -> None:
    svc = get_embedding_service()
    texts = [
        "This is the kick-off meeting for our project.",
        "We are discussing the remote control design and components.",
        "The corporate color might be yellow.",
    ]
    embeddings = svc.generate_embeddings(texts)

    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb) == 384
        # Verify vector values are non-zero floats
        assert any(abs(v) > 1e-6 for v in emb)


def test_embedding_empty_text_returns_zero_vector() -> None:
    svc = get_embedding_service()
    texts = ["", "   ", "Valid utterance here"]
    embeddings = svc.generate_embeddings(texts)

    assert len(embeddings) == 3
    # Empty texts produce zero vectors of dimension 384
    assert len(embeddings[0]) == 384
    assert all(v == 0.0 for v in embeddings[0])
    assert len(embeddings[1]) == 384
    assert all(v == 0.0 for v in embeddings[1])

    # Non-empty text produces real dense embedding
    assert len(embeddings[2]) == 384
    assert any(abs(v) > 1e-6 for v in embeddings[2])
