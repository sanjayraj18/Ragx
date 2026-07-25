import ragx

def test_package_importable_with_version() -> None:
    assert ragx.__version__ == "0.1.0"