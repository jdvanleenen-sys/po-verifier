"""Test helper: seal a record again after a test changes it on purpose, the way Sam's yes to the
changed record would. Only for planting a mistake that is not about the seal itself."""
import seal


def resealed(name, text, check=True):
    """text as an approved record sealed under name. check=False seals even an answer that is not a
    plain yes, to test that the readers refuse it on its own."""
    plain = seal.unsealed(text)
    if check:
        return seal.seal_text(name, plain)
    plain = seal.STATUS.sub("status: approved", plain, count=1)
    line = f"sealed: {name} sha256 {seal.digest(name, plain)}"
    return seal.STATUS.sub(lambda m: m.group(0) + "\n" + line, plain, count=1)
