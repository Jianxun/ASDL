from src.asdl.data_structures import ASDLFile, FileInfo, Module


def test_asdlfile_minimal():
    f = ASDLFile(file_info=FileInfo(), modules={"P": Module(spice_template="M ...")})
    assert "P" in f.modules


def test_asdlfile_with_imports_and_aliases_and_metadata():
    f = ASDLFile(
        file_info=FileInfo(top_module="TOP"),
        modules={"TOP": Module(instances={})},
        imports={"lib": "lib.asdl"},
        model_alias={"R": "lib.res"},
        metadata={"purpose": "demo"},
    )
    assert f.file_info.top_module == "TOP"
    assert f.imports["lib"] == "lib.asdl"
    assert f.model_alias["R"] == "lib.res"
    assert f.metadata["purpose"] == "demo"


