from app.services.tts.base import LocalTTS


def test_tts_interface_monkeypatched(monkeypatch, tmp_path):
    # Monkeypatch LocalTTS.synthesize to simulate audio file generation
    def fake_synthesize(self, texts, out_dir):
        paths = []
        for i, t in enumerate(texts):
            p = str(tmp_path / f"tts_{i}.mp3")
            # create empty file to simulate output
            open(p, "wb").close()
            paths.append(p)
        return paths

    monkeypatch.setattr(LocalTTS, "synthesize", fake_synthesize, raising=False)

    tts = LocalTTS()
    out = tts.synthesize(["Xin chào"], str(tmp_path))
    assert len(out) == 1
    assert out[0].endswith(".mp3")
    # file should exist
    import os

    assert os.path.exists(out[0])
